import copy
import json
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.functions import KernelArguments

from .agents.matcher_agent import MatcherAgent
from .agents.parser_agent import ParserAgent
from .agents.ranker_agent import RankerAgent
from .agents.reviewer_agent import ReviewerAgent
from .agents.scheduler_agent import SchedulerAgent
from .availability_tool import AvailabilityTool
from .memory import PipelineMemory


def _result_text(result: Any) -> str:
    value = getattr(result, "value", result)
    return value if isinstance(value, str) else str(value)


class PipelineCoordinator:
    """Run the Semantic Kernel agents in the required sequential architecture."""

    def __init__(self, availability_slots: list[dict[str, str]] | None = None) -> None:
        self.kernel = Kernel()
        self.availability = AvailabilityTool(availability_slots or [])
        self.kernel.add_plugin(ParserAgent(), plugin_name="parser")
        self.kernel.add_plugin(MatcherAgent(), plugin_name="matcher")
        self.kernel.add_plugin(RankerAgent(), plugin_name="ranker")
        self.kernel.add_plugin(ReviewerAgent(), plugin_name="reviewer")
        self.kernel.add_plugin(SchedulerAgent(), plugin_name="scheduler")
        self.kernel.add_plugin(self.availability, plugin_name="availability")

    async def _invoke_agent(self, memory: PipelineMemory, plugin_name: str) -> None:
        function = self.kernel.get_function(plugin_name=plugin_name, function_name="run")
        result = await self.kernel.invoke(
            function=function,
            arguments=KernelArguments(payload=memory.payload()),
        )
        memory.replace(json.loads(_result_text(result)))
        memory.record(
            {
                "step": len(memory.trace) + 1,
                "agent": plugin_name,
                "action": "processed shared candidate pool",
                "candidate_count": len(memory.state.get("candidate_pool", [])),
            }
        )

    async def _invoke_availability(self, function_name: str, **arguments: str) -> str:
        function = self.kernel.get_function(
            plugin_name="availability", function_name=function_name
        )
        result = await self.kernel.invoke(
            function=function,
            arguments=KernelArguments(**arguments),
        )
        return _result_text(result)

    async def run(
        self,
        job: dict[str, Any],
        resumes: list[dict[str, str]],
        top_n: int = 3,
    ) -> dict[str, Any]:
        memory = PipelineMemory(
            {
                "job": copy.deepcopy(job),
                "resumes": copy.deepcopy(resumes),
                "candidate_pool": [],
                "top_n": max(0, top_n),
            }
        )

        for agent_name in ("parser", "matcher", "ranker", "reviewer"):
            await self._invoke_agent(memory, agent_name)

        available_slots = json.loads(
            await self._invoke_availability("list_available_slots")
        )
        memory.record(
            {
                "step": len(memory.trace) + 1,
                "tool": "availability.list_available_slots",
                "available_slot_count": len(available_slots),
            }
        )
        memory.state["available_slots"] = available_slots
        await self._invoke_agent(memory, "scheduler")

        for profile in memory.state.get("candidate_pool", []):
            slot = profile.get("interview_slot")
            if not slot:
                continue
            reservation = json.loads(
                await self._invoke_availability("reserve_slot", slot_id=slot["slot_id"])
            )
            memory.record(
                {
                    "step": len(memory.trace) + 1,
                    "tool": "availability.reserve_slot",
                    "candidate_id": profile["candidate_id"],
                    "slot_id": slot["slot_id"],
                    "reserved": reservation["reserved"],
                }
            )
            if not reservation["reserved"]:
                profile["interview_slot"] = None

        memory.state.pop("available_slots", None)
        return {**memory.state, "trace": memory.trace}

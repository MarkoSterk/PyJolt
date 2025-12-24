"""Controller for state machine extension"""
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Any, Optional, cast

from pydantic import BaseModel, Field

from pyjolt.http_statuses import HttpStatus

from ..controller import Controller, post
from ..request import Request
from ..response import Response

if TYPE_CHECKING:
    from .state_machine import StateMachine

class TransitionRequestData(BaseModel):
    """Request model for state transition"""
    step: int|str = Field(description="Step to perform")
    data: Optional[dict[str, Any]] = Field(None,
                        description="Additional data for the transition")

class StateMachineController(Controller):
    """Controller for state machine operations"""

    state_machine: "StateMachine"

    @post("/transition")
    async def transition_state(self, req: Request) -> Response:
        """
        Transition to the next state based on the current state.
        """
        data = await req.json()
        if data is None:
            return req.res.json({
                "message": "Transition data is missing",
                "status": "error"
            }).status(HttpStatus.BAD_REQUEST)
        transition_request = self.state_machine.transition_request_data(**data).model_dump()
        transition_context = await self.state_machine.context_loader(req, transition_request)
        print("Transition: ", transition_request, transition_context)
        return req.res.json({"message": "State transitioned successfully"})

    def check_mapping(self, current_state: Enum|StrEnum, step: Enum|StrEnum) -> None|Enum|StrEnum:
        """
        Check if the transition from current_state to next_state is allowed.
        """
        state_map = self.state_machine.states_steps_map
        steps_for_current_state = cast(dict, state_map.get(current_state, None))
        if steps_for_current_state is None:
            return None
        next_state = steps_for_current_state.get(step, None)
        if next_state is None:
            return None
        return next_state

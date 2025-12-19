"""Controller for state machine extension"""
from enum import Enum, StrEnum
from pydantic import BaseModel, Field
from typing import Any, Optional, TYPE_CHECKING, cast
from ..controller import Controller, post, consumes, produces
from ..media_types import MediaType
from ..request import Request
from ..response import Response

if TYPE_CHECKING:
    from .state_machine import StateMachine

class TransitionRequest(BaseModel):
    """Request model for state transition"""
    step: Enum|StrEnum = Field(description="Step to perform")
    data: Optional[dict[str, Any]] = Field(None, description="Additional data for the transition")

class StateMachineController(Controller):
    """Controller for state machine operations"""

    state_machine: "StateMachine"

    @post("/transition")
    @consumes(MediaType.APPLICATION_JSON)
    @produces(MediaType.APPLICATION_JSON)
    async def transition_state(self, req: Request, transition_request: TransitionRequest) -> Response:
        """
        Transition to the next state based on the current state.
        """

        return req.res.json({"message": "State transitioned successfully"})
    
    def check_mapping(self, current_state: Enum|StrEnum, step: Enum|StrEnum) -> bool|Enum|StrEnum:
        """
        Check if the transition from current_state to next_state is allowed.
        """
        state_map = self.state_machine.state_step_map
        steps_for_current_state = cast(dict, state_map.get(current_state, None))
        if steps_for_current_state is None:
            return False
        next_state = steps_for_current_state.get(step, None)
        if next_state is None:
            return False
        return next_state
            


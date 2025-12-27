"""State machine extension implementation"""
from enum import StrEnum
from typing import Any

from pyjolt.http_statuses import HttpStatus
from pyjolt.request import Request
from pyjolt.response import Response
from pyjolt.state_machine import StateMachine as SM, step_method

class States(StrEnum):

    PENDING = "pend"
    UNDER_REVIEW = "urev"
    REJECTED = "rej"
    EVALUATED = "eval"

class Steps(StrEnum):

    ACCEPT_REVIEW = "accr"
    REJECT_REVIEW = "rejr"
    ACCEPT = "acc"
    REJECT = "rej"

STATE_STEP_MAP: dict[States, dict[Steps, States]] = {
    States.PENDING: {
        Steps.ACCEPT_REVIEW: States.UNDER_REVIEW,
        Steps.REJECT_REVIEW: States.REJECTED
    },
    States.UNDER_REVIEW: {
        Steps.REJECT: States.REJECTED,
        Steps.ACCEPT: States.EVALUATED
    }
}

class StateMachine(SM):
    """SM implementation"""

    @step_method(Steps.ACCEPT_REVIEW)
    async def on_accept_review(self, req: Request,
                               transition_request: Any, context: Any) -> Response:
        print("Performing step:", req, transition_request, context)
        return req.res.json({
            "message": f"Bla bla bla: {transition_request.get('step')}",
            "status": "success"
        }).status(HttpStatus.OK)


    async def has_permission(self, req: Request) -> bool:
        return True

    async def context_loader(self, req: Request, transition_request: Any) -> Any:
        return {}

state_machine: StateMachine = StateMachine(Steps, States, STATE_STEP_MAP)

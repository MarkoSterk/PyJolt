"""
Transition request data schema for state machine extension
"""
from enum import IntEnum, StrEnum, Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class StateMachineTransitionRequestData(BaseModel):
    """Schema"""
    step: Enum|IntEnum|StrEnum = Field(description="Step to take")
    record_id: int = Field(description="Id of the record to transition")
    data: Optional[Any] = Field(None, description="Any additional data required for the transition")

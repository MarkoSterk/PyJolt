"""
State machine extension
"""
from pydantic import ConfigDict, Field, BaseModel
from typing import TypedDict, NotRequired, Optional, TYPE_CHECKING, cast, Callable, Awaitable, Any
from abc import abstractmethod
from enum import Enum, StrEnum
from ..base_extension import BaseExtension
from ..request import Request
from ..response import Response

if TYPE_CHECKING:
    from pyjolt.pyjolt import PyJolt

# Any bound method (sync or async) -> async method returning Response
AsyncMethod = Callable[..., Awaitable["Response"]]

class _StateMachineConfigs(BaseModel):
    """Configuration options for StateMachine extension"""
    model_config = ConfigDict(extra="allow")

    API_URL: Optional[str] = Field("/api/v1/state-machine", description="API URL for state machine operations")
    STATE_STEP_MAP: dict[Enum|StrEnum, Enum|StrEnum] = Field(description="Map of allowed state transitions")
    INCLUDE_OPEN_API: Optional[bool] = Field(True, description="Whether to include state machine endpoints in OpenAPI schema")

class StateMachineConfig(TypedDict):
    """StateMachine extension configurations"""
    API_URL: NotRequired[str]
    STATE_STEP_MAP: dict[Enum|StrEnum, Enum|StrEnum]
    INCLUDE_OPEN_API: NotRequired[bool]

def step_method(*steps: Enum|StrEnum):
    """Adds method as a step method for the given step in the state machine"""

    def decorator(func: AsyncMethod) -> AsyncMethod:
        # pylint: disable=protected-access
        func.__state_machine_step__ = list(steps)  # type: ignore[attr-defined]
        return func
    return decorator

class StateMachine(BaseExtension):
    """
    State machine extension class
    """

    def __init__(self, configs_name: str = "STATE_MACHINE"):
        self._app: "PyJolt" = cast("PyJolt", None)
        self._state_step_map: dict[Enum|StrEnum, Enum|StrEnum] = {}
        self._configs_name: str = configs_name
        self._configs: dict[str, Any] = cast(dict[str, Any], None)
        self._step_methods_map: dict[str, Callable] = {}
    
    def init_app(self, app: "PyJolt") -> None:
        """
        Initialize the extension with the PyJolt app
        """
        self._app = app
        self._configs = cast(dict[str, Any], app.configs.get(self._configs_name, None))
        if self._configs is None:
            raise ValueError(f"Configurations for {self._configs_name} not found in app configurations.")
        self._configs = self.validate_configs(self._configs, _StateMachineConfigs)
        self._state_step_map = self._configs["STATE_STEP_MAP"]
        self._get_step_methods()
    
    def _get_step_methods(self) -> None:
        """Returns a dictionery with step methods mapping"""
        for name in dir(self):
            method = getattr(self, name)
            if not callable(method):
                continue
            steps = getattr(method, "__state_machine_step__", None)
            if steps:
                for step in steps:
                    if self._step_methods_map.get(step, None) is not None:
                        raise ValueError(f"Multiple methods found for step {step} in state machine.")
                    if step is not None:
                        self._step_methods_map[step] = method
    
    @property
    def state_step_map(self) -> dict[Enum|StrEnum, Enum|StrEnum]:
        """
        Get the state step map
        """
        return self._state_step_map
    
    @abstractmethod
    async def has_permission(self, req: Request) -> bool:
        """Checks if user has permission for action"""
"""
State machine extension
"""
from abc import abstractmethod
from enum import Enum, StrEnum
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    NotRequired,
    Optional,
    Type,
    TypedDict,
    cast,
)

from pydantic import BaseModel, ConfigDict, Field
from .state_machine_controller import StateMachineController, TransitionRequestData
from ..controller import path
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

    API_URL: Optional[str] = Field("/api/v1/state-machine",
                            description="API URL for state machine operations")
    INCLUDE_OPEN_API: Optional[bool] = Field(True,
                        description="Whether to include state machine endpoints in OpenAPI schema")
    TRANSITION_DATA: Optional[Type[BaseModel]] = Field(TransitionRequestData,
                        description="Transition request pydantic model for validation")

class StateMachineConfig(TypedDict):
    """StateMachine extension configurations"""
    API_URL: NotRequired[str]
    INCLUDE_OPEN_API: NotRequired[bool]
    TRANSITION_DATA: NotRequired[BaseModel]

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

    def __init__(self, steps: Type[Enum|StrEnum], states: Type[Enum|StrEnum],
                 states_steps_map: dict[Any, dict[Any, Any]], configs_name: str = "STATE_MACHINE", ):
        self._app: "PyJolt" = cast("PyJolt", None)
        self._steps = steps
        self._states = states
        self._states_steps_map: dict[Any, dict[Any, Any]] = states_steps_map
        self._configs_name: str = configs_name
        self._configs: dict[str, Any] = cast(dict[str, Any], None)
        self._step_methods_map: dict[str, Callable] = {}

    def init_app(self, app: "PyJolt") -> None:
        """
        Initialize the extension with the PyJolt app
        """
        self._app = app
        self._configs = cast(dict[str, Any], app.configs.get(self._configs_name, {}))
        if self._configs is None:
            raise ValueError(f"Configurations for {self._configs_name} not found in app configurations.")
        self._configs = self.validate_configs(self._configs, _StateMachineConfigs)
        self._get_step_methods()
        ctrl = path(self.configs["API_URL"])(StateMachineController)
        setattr(ctrl, "state_machine", self)
        self.app.register_controller(ctrl)

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
    def states_steps_map(self) -> dict[Any, dict[Any, Any]]:
        """
        Get the state step map
        """
        return self._states_steps_map

    @property
    def transition_request_data(self) -> Type[BaseModel]:
        return self._configs["TRANSITION_DATA"]

    @abstractmethod
    async def has_permission(self, req: Request) -> bool:
        """Checks if user has permission for action"""

    @abstractmethod
    async def context_loader(self, req: Request, transition_request: Any) -> Any:
        """
        Loads the needed context for transitions. This can be anything
        which is required to perform the transition
        """

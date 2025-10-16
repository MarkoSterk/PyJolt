"""
Base extension class
"""
from typing import TYPE_CHECKING, Any
from abc import abstractmethod, ABC
from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from .pyjolt import PyJolt

class BaseExtension(ABC):

    _configs_name: str

    @abstractmethod
    def init_app(self, app: "PyJolt") -> None:
        ...
    
    def validate_configs(self, configs: dict[str, Any], model: type[BaseModel]) -> dict[str, Any]:
        try:
            return model.model_validate(configs).model_dump()
        except ValidationError as e:
            raise ValueError(f"Invalid configuration for {self._configs_name or self.__class__.__name__}: {e}") from e
    
    @property
    def configs_name(self) -> str:
        """
        Return the config name used in app configurations
        for this extension.
        """
        return self._configs_name

"""
Base extension class
"""
from typing import TYPE_CHECKING
from abc import abstractmethod

if TYPE_CHECKING:
    from .pyjolt import PyJolt

class BaseExtension:
    
    @abstractmethod
    def init_app(self, app: "PyJolt") -> None:
        ...

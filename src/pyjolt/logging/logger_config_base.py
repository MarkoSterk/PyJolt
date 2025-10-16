"""
Base logger configuration class
"""
import re
from abc import ABC, abstractmethod
from datetime import timedelta
from pathlib import Path
from typing import Dict, Any, Union, Optional, List, IO, Callable, Protocol, runtime_checkable

from loguru import logger

SinkType = Union[str, Path, IO[str], IO[bytes], Callable[[str], Any]]
@runtime_checkable
#pylint: disable=R0903
class Writable(Protocol):
    def write(self, s: str) -> Any: ...
SinkInput = Union[str, Path, IO[str], IO[bytes], Callable[[str], Any], Writable]
SinkAccepted = Union[str, Writable, Callable[[str], None]]
RotationType = Union[str, int, timedelta, Callable[[str, Any], Any]]
RetentionType = Union[str, int, timedelta, Callable[[str, Any], Any]]
CompressionType = Optional[str]
FilterType = Union[None, str, Dict[str, str], Callable[[Dict[str, Any]], bool]]

class LoggerConfigBase(ABC):
    """
    Base template for configuring a Loguru sink.
    Subclasses implement get_sink() and optionally override getters below.
    """

    def __init__(self, app):
        self.app = app
        #loads configs for the logger from application configurations
        #by the config class name as upper-case 
        #example: CustomLoggerConfig -> CUSTOM_LOGGER_CONFIG
        self.conf: Dict[str, Any] = app.get_conf(self.logger_name_upper, None) or {}

    @property
    def logger_name_upper(self) -> str:
        """Returns class name as upper snake case"""
        name = self.__class__.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()

    @abstractmethod
    def get_sink(self) -> SinkInput:
        ...

    def get_conf_value(self, key: str, default: Any = None) -> Any:
        return self.conf.get(key, default)

    def get_level(self) -> Union[str, int]:
        return self.get_conf_value("level", "INFO")

    def get_format(self) -> str:
        # includes the class name as a constant-like tag
        return self.get_conf_value(
            "format",
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | {extra[logger_name]} | "
            "{name}:{function}:{line} - <cyan>{message}</cyan>",
        )

    def get_rotation(self) -> Optional[RotationType]:
        return self.get_conf_value("rotation", None)

    def get_retention(self) -> Optional[RetentionType]:
        return self.get_conf_value("retention", None)

    def get_compression(self) -> CompressionType:
        return self.get_conf_value("compression", None)

    def get_filter(self) -> FilterType:
        return self.get_conf_value("filter", None)

    def get_enqueue(self) -> bool:
        return self.get_conf_value("enqueue", True)

    def get_backtrace(self) -> bool:
        return self.get_conf_value("backtrace", False)

    def get_diagnose(self) -> bool:
        return self.get_conf_value("diagnose", False)

    def get_colorize(self) -> Optional[bool]:
        return self.get_conf_value("colorize", None)

    def get_serialize(self) -> bool:
        return self.get_conf_value("serialize", False)

    def get_encoding(self) -> Optional[str]:
        return self.get_conf_value("encoding", "utf-8")

    def get_mode(self) -> Optional[str]:
        return self.get_conf_value("mode", "a")

    def get_delay(self) -> bool:
        return self.get_conf_value("delay", True)

    def remove_existing_handlers(self) -> bool:
        return self.get_conf_value("remove_existing_handlers", False)

    def _build_handler_kwargs(self) -> Dict[str, Any]:
        return {
            "level": self.get_level(),
            "format": self.get_format(),
            "rotation": self.get_rotation(),
            "retention": self.get_retention(),
            "compression": self.get_compression(),
            "filter": self.get_filter(),
            "enqueue": self.get_enqueue(),
            "backtrace": self.get_backtrace(),
            "diagnose": self.get_diagnose(),
            "colorize": self.get_colorize(),
            "serialize": self.get_serialize(),
            "encoding": self.get_encoding(),
            "mode": self.get_mode(),
            "delay": self.get_delay(),
        }

    def _normalize_sink(self, sink: SinkInput) -> SinkAccepted:
        # Loguru accepts string paths; stubs don’t list Path, so convert.
        if isinstance(sink, Path):
            return sink.as_posix()
        # Text/byte IO objects implement .write -> satisfy Writable Protocol
        return sink  # type: ignore[return-value]

    def configure(self):
        """
        Attach this class's sink(s) to the global logger.
        """

        # Bind a constant so {extra[logger_name]} is available in the format
        bound = logger.bind(logger_name=self.logger_name_upper)

        # Primary sink
        raw_sink = self.get_sink()
        sink = self._normalize_sink(raw_sink)
        kwargs = {k: v for k, v in self._build_handler_kwargs().items() if v is not None}
        bound.add(sink, **kwargs) # type: ignore[arg-type]

        # Extra sinks (if any)
        for spec in self.add_extra_sinks():
            spec = dict(spec)
            if "sink" not in spec:
                raise ValueError("Each extra sink dict must include a 'sink' key.")
            spec["sink"] = self._normalize_sink(spec["sink"])
            bound.add(**spec)  # type: ignore[arg-type]  # (spec kwargs are dynamic)
        return logger

    def add_extra_sinks(self) -> List[Dict[str, Any]]:
        return []

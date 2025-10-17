"""
Base logger configuration class
"""
import re
from abc import ABC, abstractmethod
from datetime import timedelta
from pathlib import Path
from typing import Dict, Any, Union, Optional, List, IO, Callable, Protocol, runtime_checkable
from enum import StrEnum

from loguru import logger

@runtime_checkable
#pylint: disable=R0903
class Writable(Protocol):
    def write(self, s: str) -> Any: ...

SinkType = Union[str, Path, IO[str], IO[bytes], Callable[[str], Any]]
SinkInput = Union[str, Path, IO[str], IO[bytes], Callable[[str], Any], Writable]
SinkAccepted = Union[str, Writable, Callable[[str], None]]
RotationType = Union[str, int, timedelta, Callable[[str, Any], Any]]
RetentionType = Union[str, int, timedelta, Callable[[str, Any], Any]]
CompressionType = Optional[str]
FilterType = Union[None, str, Dict[str, str], Callable[[Dict[str, Any]], bool]]

class LogLevel(StrEnum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

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
        self.conf: Dict[str, Any] = app.get_conf(self.logger_name, None) or {} # type: ignore

    @property
    def logger_name(self) -> str:
        """Returns class name as upper snake case"""
        name = self.__class__.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()

    @abstractmethod
    def get_sink(self) -> SinkInput:
        ...

    def get_conf_value(self, key: str, default: Any = None) -> Any:
        return self.conf.get(key, default)

    def get_level(self) -> Union[str, int]:
        return self.get_conf_value("LEVEL", LogLevel.INFO)

    def get_format(self) -> str:
        # includes the class name as a constant-like tag
        return self.get_conf_value(
            "FORMAT",
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | {extra[logger_name]} | "
            "{name}:{function}:{line} - <cyan>{message}</cyan>",
        )

    def get_rotation(self) -> Optional[RotationType]:
        return self.get_conf_value("ROTATION", None)

    def get_retention(self) -> Optional[RetentionType]:
        return self.get_conf_value("RETENTION", None)

    def get_compression(self) -> CompressionType:
        return self.get_conf_value("COMPRESSION", None)

    def get_filter(self) -> FilterType:
        return self.get_conf_value("FILTER", None)
    
    def _wrap_filter_with_logger_name(self, original_filter: FilterType) -> Callable[[Dict[str, Any]], bool]:
        def _wrapped(record: Dict[str, Any]) -> bool:
            # Ensure the key is always present
            record["extra"].setdefault("logger_name", self.logger_name)

            # Apply original filter semantics
            if original_filter is None:
                return True
            if callable(original_filter):
                return bool(original_filter(record))
            if isinstance(original_filter, str):
                # same semantics as Loguru: match logger name
                return record.get("name") == original_filter
            if isinstance(original_filter, dict):
                # same semantics: match extra values
                return all(record["extra"].get(k) == v for k, v in original_filter.items())
            return True
        return _wrapped

    def get_enqueue(self) -> bool:
        return self.get_conf_value("ENQUEUE", True)

    def get_backtrace(self) -> bool:
        return self.get_conf_value("BACKTRACE", False)

    def get_diagnose(self) -> bool:
        return self.get_conf_value("DIAGNOSE", False)

    def get_colorize(self) -> Optional[bool]:
        return self.get_conf_value("COLORIZE", None)

    def get_serialize(self) -> bool:
        return self.get_conf_value("SERIALIZE", False)

    def get_encoding(self) -> Optional[str]:
        return self.get_conf_value("ENCODING", "utf-8")

    def get_mode(self) -> Optional[str]:
        return self.get_conf_value("MODE", "a")

    def get_delay(self) -> bool:
        return self.get_conf_value("DELAY", True)

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
    
    def _is_path_sink(self, sink: SinkAccepted) -> bool:
        return isinstance(sink, str)

    def _is_stream_sink(self, sink: SinkAccepted) -> bool:
        return (not isinstance(sink, str)) and hasattr(sink, "write")

    def _is_callable_sink(self, sink: SinkAccepted) -> bool:
        return callable(sink) and not hasattr(sink, "write")

    def _normalize_sink(self, sink: SinkInput) -> SinkAccepted:
        # Loguru accepts string paths; stubs don’t list Path, so convert.
        if isinstance(sink, Path):
            return sink.as_posix()
        # Text/byte IO objects implement .write -> satisfy Writable Protocol
        return sink  # type: ignore[return-value]
    
    def _filter_kwargs_for_sink(self, sink: SinkAccepted, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        # Common kwargs accepted by all sinks
        common = {
            "level", "format", "filter",
            "colorize", "serialize", "backtrace", "diagnose",
            "enqueue", "catch"
        }
        # File-path only kwargs (Loguru opens the file for you)
        file_only = {"rotation", "retention", "compression", "mode", "delay", "encoding", "buffering"}
        # Streams (TextIO / Writable): no rotation/retention/compression/encoding/mode/delay
        stream_only: set = set()  # (no extra)
        # Callables: also no file-only kwargs
        callable_only: set = set()

        if self._is_path_sink(sink):
            allowed = common | file_only
        elif self._is_stream_sink(sink):
            allowed = common | stream_only
        else:  # callable sink
            allowed = common | callable_only

        return {k: v for k, v in kwargs.items() if k in allowed and v is not None}

    def configure(self):

        raw_sink = self.get_sink()
        sink = self._normalize_sink(raw_sink)

        base_kwargs = self._build_handler_kwargs()
        # Wrap filter to inject extra["logger_name"] for every record to this sink
        base_kwargs["filter"] = self._wrap_filter_with_logger_name(base_kwargs.get("filter"))

        kwargs = self._filter_kwargs_for_sink(sink, base_kwargs)
        logger.add(sink, **kwargs)

        for spec in self.add_extra_sinks():
            spec = dict(spec)
            if "sink" not in spec:
                raise ValueError("Each extra sink dict must include a 'sink' key.")
            s = self._normalize_sink(spec.pop("sink"))

            # Wrap each extra sink's filter as well
            spec["filter"] = self._wrap_filter_with_logger_name(spec.get("filter"))
            filtered = self._filter_kwargs_for_sink(s, spec)
            logger.add(s, **filtered)

        return logger

    def add_extra_sinks(self) -> List[Dict[str, Any]]:
        return []

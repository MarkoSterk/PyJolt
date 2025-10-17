"""
PyJolt default logger
"""
import sys
from .logging.logger_config_base import LoggerConfigBase, SinkType, LogLevel

class DefaultLogger(LoggerConfigBase):
    """Default logger implementation"""

    def get_sink(self) -> SinkType:
        return sys.stderr


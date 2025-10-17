"""
PyJolt default logger
"""
import sys
from .logging.logger_config_base import LoggerConfigBase, SinkType, LogLevel

class DefaultLogger(LoggerConfigBase):
    """Default logger implementation"""

    def get_sink(self) -> SinkType:
        return sys.stderr

    def get_level(self):
        return LogLevel.TRACE

    def get_filter(self):
        return None

    def get_colorize(self):
        return True

    def get_backtrace(self):
        return True

    def get_diagnose(self):
        return True
    
    def get_format(self):
        # Simple, readable, colorized; includes the class tag via {extra[logger_name]}
        return (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "{extra[logger_name]} | "
            "<level>{message}</level>"
        )

"""
Performance file logger
"""
from typing import Any
from pyjolt.logging import LoggerBase

class PerformanceFileLogger(LoggerBase):
    """File logger for performance data"""
    def get_format(self) -> str:
        """Should return a valid format string for the logger output"""
        return ("<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | {extra[logger_name]} | "
                "{name}:{function}:{line} - <cyan>{message}</cyan>")

    def get_filter(self):
        def _filter(record: dict[str, Any]) -> bool:
            return "PERFORMANCE" in record["message"]

        return _filter

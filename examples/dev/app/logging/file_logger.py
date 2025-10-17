"""
File logger for app
"""
from pyjolt.logging import LoggerBase

class FileLogger(LoggerBase):
    """Simple file logger"""

    def get_format(self) -> str:
        """
        Clunky way to construct a valid Loguru format string. 
        TO DO: figure out a better way
        """
        fmt = (
            '{{'
            '"TIME": "{time:YYYY-MM-DD HH:mm:ss}", '
            '"LEVEL": "{level}", '
            '"LOGGER": "{extra[logger_name]}", '
            '"LOCATION": "{name}:{function}:{line}", '
            '"MESSAGE": "{message}"'
            '}}'
        )
        return fmt

import os
import sys
import logging
from pathlib import Path

import ecs_logging


class LoggingHelper:
    """Centralized class for handling logging. This creates human-readable logs.
    Structured logging implemented for shits and giggles"""

    @staticmethod
    def generate_logger(log_level: int, log_file_loc: Path, logger_name: str) -> logging.Logger:
        """
        Generates a logger with our standardized format based on arguments
        @param log_level:
        @param log_file_loc:
        @param logger_name:
        @return:
        """
        wanted_logger = logging.getLogger(logger_name)

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(ecs_logging.StdlibFormatter())

        LoggingHelper.create_directory(log_file_loc)
        file_handler = logging.FileHandler(filename=log_file_loc)
        file_handler.setFormatter(ecs_logging.StdlibFormatter())

        wanted_logger.addHandler(stdout_handler)
        wanted_logger.addHandler(file_handler)

        wanted_logger.setLevel(log_level)
        return wanted_logger

    @staticmethod
    def create_directory(file_loc: Path):
        if not os.path.exists(file_loc.parent):
            os.makedirs(file_loc.parent)

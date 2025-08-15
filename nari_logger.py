""" Primary modular for setting up logging. """

from datetime import datetime
from pathlib import Path
import sys
import os
import warnings
import logging
import inspect


from dotenv import load_dotenv

__all__ = [
    'get_script_name',
    'flush_newline',
    'LogManager',
    'print_message'
]

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Pointing to the specific targeted .env file due to directory shenanigans
#load_dotenv(os.path.join(MAINDIR, ".env"))

LOG_FORMAT = '%(asctime)s : [PID: %(process)d, TID: %(thread)d] : [%(levelname)s] : %(name)s >> %(message)s'
DATEFORMAT = '%Y-%m-%d %H:%M:%S'
CONSOLE_FORMAT = '[%(levelname)s] >> %(message)s'

class LogManager:
    def __init__(self, app_name):
        self.app_name = app_name
        self.base_logging_path = Path(os.environ.get("LOG_DIR"))
        self.ensure_logging_directory()

    def ensure_logging_directory(self) -> None:
        self.base_logging_path.mkdir(
            parents=True,
            exist_ok=True
        )

    def get_log_file_path(self) -> Path:
        timestamp = datetime.now().strftime('%Y-%m-%d')
        return self.base_logging_path / f"{self.app_name}_{timestamp}.log"

    def setup_file_logging(self) -> None:
        log_file_path = self.get_log_file_path()
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATEFORMAT)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)

        # Clear existing handlers to avoid duplicate logging
        root_logger.handlers.clear()

        root_logger.addHandler(file_handler)

    def get_console_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.app_name)
        logger.setLevel(logging.INFO)

        # Console output format
        console_formatter = logging.Formatter(CONSOLE_FORMAT)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        return logger

    def shutdown(self):
        self.clean_logs()
        logging.shutdown()

    def clean_logs(self):
        # Do not want to clean up logs in Dev Folder yet!
        if 'Python Scripts' in str(self.base_logging_path):
            return

        # General Pattern matching used for file in systems
        glob_base_logging_path = self.base_logging_path.glob('**/*')
        files = [f for f in glob_base_logging_path if f.is_file()]
        today = datetime.today().date()

        for file in files:
            file_path = Path(file)

            # Pathlib way of getting date made returns an epoch int
            file_epoch_time = file_path.stat().st_mtime

            # Converts the epoch int to usable timestamp
            file_date = datetime.fromtimestamp(file_epoch_time).date()
            delta_days = abs(file_date - today)

            if delta_days.days > 21:
                # unlink is Pathlib way of deleting
                file_path.unlink()


def get_script_name(filename: str) -> str:
    return os.path.basename(os.path.abspath(filename)).split('.')[0]


def flush_newline():
    print("\n", end="")
    sys.stdout.flush()


def print_message(message: str, *args, to_log: bool = False, log_level: int = logging.INFO):
    """
    Outputs a message to either the stdout or logger, with support for lazy message formatting.

    Parameters:
        message (str): The message, potentially with format specifiers (e.g., %s).
        args (tuple): Arguments for formatting the message string.
        to_log (bool): If True will direct message to the logger vs the stdout
            Currently set to False
        log_level (int): Logging level if logger is used. Defaults to logging.INFO.
    """

    # Accommodates for when user enters variable names as a list
    if args and isinstance(args[0], list):
        args = tuple(args[0])

    if to_log:
        # To set the %(name)s in the logger we first need to retrieve where it was called from
        # Using the 'inspect' modular we can retrieve the modular.function name
        # The 2nd entry seems to always be previous action which occurs print_message call
        caller_frame_info = inspect.stack()[1]
        caller_name = inspect.getmodule(caller_frame_info[0]).__name__
        logger = logging.getLogger(caller_name)

        # Use the current logger and pass in the log level and message
        logger.log(log_level, message, *args)

    else:
        # message % args is used to insert submitted variables in the message as part of the
        #   lazy %s method.
        if log_level == 30:
            # Warning message and it's not logging.
            if args:
                message = message % args
            warnings.warn(message)

        elif log_level == 40:
            # Error message and it's not logging
            if args:
                message = message % args
            print(
                message,
                file=sys.stderr
            )

        # Regular stdout message.
        if args:
            message = message % args
        print(message)

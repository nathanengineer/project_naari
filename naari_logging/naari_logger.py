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
    'LogManager',
]

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(MAINDIR, ".env"))

FILENAME_BASE = "naari_logs"

# Note: %(message)s broken up to be 'caller function' >> message
LOG_FORMAT = '%(asctime)s : [PID: %(process)d, TID: %(thread)d] : [%(levelname)s] : %(name)s::%(message)s'
DATEFORMAT = '%Y-%m-%d %H:%M:%S'
CONSOLE_FORMAT = '[%(levelname)s] >> %(message)s'
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE"))     # Size in MB


class LogManager:
    """
        Singleton-style logging manager for the NAARI application.

        This class centralizes logging across the Dash app, ensuring that all
        modules and callbacks can use a consistent logger without configuring
        logging separately. It manages log files, automatically rotates them when
        size limits are exceeded, and provides a single entry point for writing
        messages to either stdout or the active log file.

        Key features:
            • Creates and manages log files in the app's `Logs` directory.
            • Automatically selects the most recent log file or creates a new one.
            • Rotates logs when file size exceeds the configured limit.
            • Filters noisy library loggers (httpx, urllib3) to reduce clutter.
            • Supports optional cleanup of old log files.
            • Provides a unified `print_message` method that:
                - Supports lazy `%s`-style formatting.
                - Adds caller function name context to messages.
                - Can direct output to stdout, stderr, warnings, or the log file.
    """
    _instance = None
    _current_file_path: Path = None

    def __dir__(self):
        return ["print_message", "setup_file_logging"]

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Aids in re-running on re-running on multiple imports
        if not hasattr(self, "initialized"):
            app_path = Path(__file__).parent
            self.base_logging_path = app_path / 'Logs'
            self._ensure_logging_directory()
            self.current_file_path = self._get_active_file()
            self.initialized = True     # flag to lock __init__ once


    def _ensure_logging_directory(self) -> None:
        self.base_logging_path.mkdir(
            parents=True,
            exist_ok=True
        )

    def _get_active_file(self):
        """ Finds currently active log file and if not nothing exist it creates it. """
        log_files = list(self.base_logging_path.glob(f"{FILENAME_BASE}_*"))
        if log_files:
            latest_file = max(log_files, key=lambda  f: f.stat().st_mtime)
            return latest_file
        return self._make_log_file()

    def _make_log_file(self) -> Path:
        """ Makes Log File. """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        return self.base_logging_path / f"{FILENAME_BASE}_{timestamp}.log"

    def setup_file_logging(self) -> None:
        """ Sets up the app log schema. """
        # We get the file path after first checking for existance and size.
        log_file_path = self.current_file_path

        # Prevents 'Info' from requests being logged, prevents flooding the logger.
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATEFORMAT)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)

        # Clear existing handlers to avoid duplicate logging
        root_logger.handlers.clear()

        root_logger.addHandler(file_handler)

    def shutdown(self):
        """ Allows for a safe closing and shutdown of the active logger. """
        logging.shutdown()

    # TODO: Is this even needed? DO I want to clean up logs
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

    def _file_size_exceeded(self):
        """ Checks if file exceeded system limit. Creates new file if exceeded. """
        current_file = self.current_file_path
        if current_file and current_file.exists():
            current_size = current_file.stat().st_size / (1024*1024)    # bit conversion to Mb -> 1/Kb * 1/Mb
            if current_size > MAX_FILE_SIZE:
                self.current_file_path =  self._make_log_file()
                self.setup_file_logging()

    @classmethod
    def print_message(cls, message: str, *args, to_log: bool = False, log_level: int = logging.INFO):
        """
        Outputs a message to either the stdout or logger, with support for lazy message formatting.

        Parameters:
            message (str): The message, potentially with format specifiers (e.g., %s).
            args (tuple): Variables tied with Lazy method messages to be inserted.
            to_log (bool): If True will direct message to the logger vs the stdout
                Currently set to False
            log_level (int): Logging level if logger is used. Defaults to logging.INFO.
        """

        # ensure singleton exists
        self = cls._instance or cls()

        # Check size rollover
        self._file_size_exceeded()

        # Accommodates for lazy %s formatting
        if args and isinstance(args[0], list):
            args = tuple(args[0])

        if to_log:
            # To set the %(name)s in the logger we first need to retrieve where it was called from
            # Using the 'inspect' modular we can retrieve the modular.function name
            # The 2nd entry seems to always be previous action which occurs print_message call
            caller_frame_info = inspect.stack()[1]
            caller_name = inspect.getmodule(caller_frame_info[0]).__name__
            function_caller = caller_frame_info.function
            logger = logging.getLogger(caller_name)

            message = "%s >> " + message
            args = (function_caller, *args) if args else (function_caller,)
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


import logging
import os

from dotenv import load_dotenv

from naari_logging.naari_logger import LogManager
from naari_app.dash_app import dash_app

load_dotenv(".env")
TO_LOG = int(os.getenv("LOGGING", "0")) == 1

logger = LogManager()
logger.setup_file_logging()

try:
    server = dash_app().server
except Exception as err:  # pylint: disable=broad-exception-caught
    logger.print_message(
        "Major problem during run >> %s",
        err,
        to_log=TO_LOG,
        log_level=logging.CRITICAL
    )

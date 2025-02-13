# utils/error_handling.py
import functools
import logging
import os
import time

from dash import no_update

from config import BASE_DIR


def setup_logger():
    logger = logging.getLogger("saxs_analysis")
    logger.setLevel(logging.DEBUG)

    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(BASE_DIR, "output_data", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Create file handler and set level to debug
    log_file = os.path.join(log_dir, "saxs_analysis.log")
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add formatter to handlers
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


logger = setup_logger()


def handle_callback_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logger.exception(error_msg)
            return (
                {"message": error_msg, "is_error": True, "timestamp": time.time()},
                no_update,
                no_update,
                no_update,
            )

    return wrapper

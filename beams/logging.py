"""
Logging configuration for BEAMS and multiprocessing-compatible logging
Mostly adapted from the python logging cookbook and hutch_python.logging
"""

import logging
import logging.config
import multiprocessing as mp
import os
import threading
import time
from logging.handlers import QueueHandler
from pathlib import Path
from typing import Optional, Union

import yaml

LOGGER_QUEUE = mp.Queue(-1)
LOGGER_THREAD: Optional[threading.Thread] = None
LOGGER_CFG_YAML = Path(__file__).parent / "logging.yml"
LOG_DIR = None
logger = logging.getLogger(__name__)


def worker_logging_configurer(queue: mp.Queue):
    """
    Pass this into the worker process, and run the function with the shared
    LOGGER_QUEUE.  This will allow logging messages to be passed out of the process
    and processed by the main process

    Parameters
    ----------
    queue : multiprocessing.Queue
        Queue that passes logging records between processes
    """
    h = QueueHandler(queue)  # Just the one handler needed
    root = logging.getLogger("beams")  # root logger for beams
    root.addHandler(h)


def logger_thread(q: mp.Queue):
    """
    Logger process to be started in the main thread for receiving and processing
    logging events from other processes.

    Parameters
    ----------
    q : multiprocessing.Queue
        Queue that passes logging records between processes
    """
    while True:
        record = q.get()
        if record is None:
            logger.debug("Logger thread ending")
            break
        record_logger = logging.getLogger(record.name)
        record_logger.handle(record)


class LoggingNotConfiguredError(Exception):
    ...


def get_log_filename(extension: str = ".log") -> Path:
    """
    Get a logger filename and ready it for usage.

    Parameters
    ----------
    extension : str
        The log file extension.

    Returns
    -------
    pathlib.Path :
        The log file path.
    """
    if LOG_DIR is None:
        raise LoggingNotConfiguredError(
            "Logging was not configured (LOG_DIR unset).  If in production "
            "mode, please call `configure_log_directory` first."
        )

    # Subdirectory for year/month
    dir_month = LOG_DIR / time.strftime("%Y_%m")

    # Make the log directories if they don't exist
    # Make sure each level is all permissions
    for directory in (LOG_DIR, dir_month):
        if not directory.exists():
            directory.mkdir()
            directory.chmod(0o777)

    user = os.environ["USER"]
    timestamp = time.strftime("%d_%Hh%Mm%Ss")

    logfile = dir_month / f"{user}_{timestamp}{extension}"
    logfile.touch()
    return logfile


def _read_logging_config() -> dict:
    """Read the logging configuration file into a dictionary."""
    with open(LOGGER_CFG_YAML) as f:
        return yaml.safe_load(f.read())


def get_log_directory() -> Optional[Path]:
    """Get the currently configured logging path."""
    return LOG_DIR


def configure_log_directory(dir_logs: Optional[Union[str, Path]]):
    """
    Configure the logging path.

    Parameters
    ----------
    dir_logs: ``str`` or ``Path``, optional
        Path to the log directory. If omitted, we won't use a log file.
    """
    global LOG_DIR
    LOG_DIR = Path(dir_logs).expanduser().resolve() if dir_logs else None


def setup_logging(level: int = logging.INFO):
    """
    Setup logging for BEAMS.  Involves:
    - Reading the logging config yaml file
    - Trimming the config of unused handlers if not configured (FileHandler)
    - Starting the main logging daemon thread

    Parameters
    ----------
    level : int, optional
        the desired logging level, by default logging.INFO
    """
    global LOGGER_THREAD
    if LOGGER_THREAD is not None:
        logger.info("Logger already configured")
        return

    config = _read_logging_config()

    if LOG_DIR is None:
        # Remove debug file from the config
        del config["handlers"]["debug"]
        config["root"]["handlers"].remove("debug")
        config["loggers"]["beams"]["handlers"].remove("debug")
    else:
        config["handlers"]["debug"]["filename"] = str(get_log_filename())

    logging.config.dictConfig(config)

    # setup main logger thread to listen to mp.Process loggers
    LOGGER_THREAD = threading.Thread(
        target=logger_thread, args=(LOGGER_QUEUE,), daemon=True
    )
    LOGGER_THREAD.start()

import logging
import os


def setup_logger(log_filename="binge_watch.log"):
    """
    Set up and configure a file-based logger for the application.

    This function initializes a logger that writes log messages to a specified file.
    If the file doesn't exist it will be created on the first run.
    Each log entry will include the timestamp, logger name, log level, and message.

    Arguments:
        log_filename (str): The name of the log file. Defaults to 'binge_watch.log'.

    Returns:
        logging.Logger: A configured logger instance ready to log messages.
    """

    log_filepath = os.path.join(os.getcwd(), log_filename)
    logger = logging.getLogger("binge_watch_file_logger")

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(log_filepath, mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger

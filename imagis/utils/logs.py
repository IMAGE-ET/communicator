import os
import sys
import logging
import logging.handlers

def setup_logger(name, level=logging.DEBUG, log_file=None,
                 max_bytes=5242880, count=5, send_mail=False,
                 recipients=[]):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        dir_path = os.path.dirname(log_file)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        rotating_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=count
        )
        rotating_handler.setFormatter(formatter)
        logger.addHandler(rotating_handler)

    # TODO: Add an email handler

    return logger

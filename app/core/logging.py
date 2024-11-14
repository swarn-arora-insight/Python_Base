import logging
import logging.config

# Configuration dictionary
# logging.basicConfig(
#     level=logging.DEBUG,  # Set the minimum log level to DEBUG
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler("python_base.log"),  # Save logs to app.log file
#         logging.StreamHandler()  # Also output logs to the console
#     ]
# )
logging_config = {
    "version": 1,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "python_base.log",
            "formatter": "detailed",
            "level": "INFO"
        },
        "console": {
            "class": "logging.FileHandler",
            "filename":"python_base.log",
            "formatter": "detailed",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["file", "console"],
            "level": "DEBUG",
        }
    }
}

logging.config.dictConfig(logging_config)
logger = logging.getLogger()

# Usage
logger.info("This is an info message")
logger.error("This is an error message")
logger.debug("This is an debug message")
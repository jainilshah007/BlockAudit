import logging
import sys

def setup_logger():
    """
    Sets up a centralized logger for the application.
    """
    # Prevents interference with Streamlit's default logger and duplicate handlers
    if logging.getLogger("auditor_logger").handlers:
        return logging.getLogger("auditor_logger")

    # Create a new logger with a specific name
    logger = logging.getLogger("auditor_logger")
    logger.setLevel(logging.INFO)  # Set the minimum log level (INFO, WARNING, ERROR)

    # Define the format for log messages
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create a handler to write logs to a file
    file_handler = logging.FileHandler("auditor.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create a handler to display logs in the console (terminal)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    logger.info("Logger initialized successfully.")
    return logger

# Create a logger instance to be used throughout the project
logger = setup_logger()
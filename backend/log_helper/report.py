import logging
import inspect
import os # Import the os module for path manipulation

def get_caller_info():
    frame = inspect.stack()[2]
    filename = frame.filename
    lineno = frame.lineno
    # Use os.path.basename to get just the filename from the full path
    return f"({os.path.basename(filename)}:{lineno})"

def setup_file_logging(log_file="app.log", level=logging.INFO):
    """
    Configures the logging module to save logs to a file.

    Args:
        log_file (str): The name of the log file.
        level (int): The minimum logging level to capture (e.g., logging.INFO, logging.DEBUG).
    """
    # Create a logger instance
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    # Create a file handler
    file_handler = logging.FileHandler(log_file)

    # Create a formatter and set it for the handler
    # This format includes timestamp, log level, message, and caller info
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the handler to the logger
    # Check if handler already exists to prevent duplicate logs if called multiple times
    if not logger.handlers:
        logger.addHandler(file_handler)

def log_message(message, level="info"):
    """
    Logs a message with caller information.
    """
    caller_info = get_caller_info()
    # Get the logger instance configured in setup_file_logging
    logger = logging.getLogger(__name__)
    setup_file_logging("inquisitor.log", level=logging.DEBUG)

    # Use the logger's methods directly
    match level.lower(): # Convert to lowercase for case-insensitive matching
        case "info":
            logger.info(f"{message}{caller_info}")
        case "debug":
            logger.debug(f"{message}{caller_info}")
        case "error":
            logger.error(f"{message}{caller_info}")
        case "critical":
            logger.critical(f"{message}{caller_info}")
        case "warning":
            logger.warning(f"{message}{caller_info}")
        case _: # Default case for unrecognised levels
            logger.info(f"{message}{caller_info} (Unrecognized log level '{level}', logging as info)")


# --- Example Usage ---
if __name__ == "__main__":
    # Call this once at the start of your application
    setup_file_logging("my_application.log", level=logging.DEBUG)

    log_message("This is an informational message")
    log_message("This is a debug message", level="debug")
    log_message("Something went wrong!", level="error")
    log_message("Critical system failure", level="critical")
    log_message("Be careful, something might go wrong", level="warning")

    print("Logs saved to my_application.log")

    # You can also log directly using the logger instance once configured
    # logging.getLogger(__name__).info("Another way to log info!")
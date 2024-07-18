import logging
import os  # Impo
from logging.handlers import RotatingFileHandler

GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"
RED = "\033[31m"

# Create a logger object
logger = logging.getLogger("digiHousing")
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Prevent the logger from propagating messages to the root logger


log_directory = "logs"  # Define the log directory
log_filename = "digiHousing.log"  # Define the log filename
full_log_path = os.path.join(log_directory, log_filename)  # Full path for the log file

# Ensure the directory exists
if not os.path.exists(log_directory):
    os.makedirs(log_directory)  # Create the log directory if it does not exist


# Check if handlers are already configured
if not logger.handlers:
    console_formatter = logging.Formatter(
         '%(asctime)s || %(levelname)-8s || %(name)s:%(lineno)d || %(message)s'
    )
    # file_formatter = logging.Formatter('%(asctime)s.%(msecs)03d || %(levelname)-8s || %(name)s:%(lineno)d || %(message)s')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set level to DEBUG to capture all messages
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = RotatingFileHandler(
        filename="logs/feedback_systems.log",
        maxBytes=5*1024*1024,  # 2 MB
        backupCount=10,
        delay=True,
        encoding="utf-8",
    )
    file_handler.setFormatter(console_formatter)
    # file_handler.setLevel(logging.DEBUG)  
    logger.addHandler(file_handler)

def configure_logging():
    return logger
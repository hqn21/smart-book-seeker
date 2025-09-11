import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs", datetime_str)
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "messages.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5)
    ]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
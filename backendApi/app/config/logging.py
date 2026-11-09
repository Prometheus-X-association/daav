import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config.settings import Settings

def setup_logging(settings : Settings):
    """Setup centralized logging configuration using settings, including security logger."""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # --- Main app logger ---
    log_level = getattr(logging, settings.log_level.upper())
    log_file = log_dir / settings.log_file
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=_parse_size(settings.log_max_size),
        backupCount=settings.log_backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)

    # --- Security logger ---
    security_log_file = log_dir / settings.security_log_file
    security_log_level = getattr(logging, settings.security_log_level.upper())
    security_formatter = logging.Formatter('[SECURITY] %(asctime)s - %(levelname)s - %(message)s')
    security_handler = RotatingFileHandler(
        security_log_file,
        maxBytes=_parse_size(settings.security_log_max_size),
        backupCount=settings.security_log_backup_count,
        encoding='utf-8'
    )
    security_handler.setFormatter(security_formatter)
    security_handler.setLevel(security_log_level)
    security_logger = logging.getLogger("security")
    security_logger.setLevel(security_log_level)
    security_logger.handlers.clear()
    security_logger.addHandler(security_handler)
    security_logger.propagate = False

    # Set specific loggers levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # With --reload, uvicorn (>= 0.48) imports the app in the reloader process, so
    # watchfiles logs to logs/app.log, which is in the watched directory: each
    # "change detected" line would trigger the next one in an endless loop.
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    #logging.getLogger("beanie").setLevel(logging.DEBUG)
    #logging.getLogger("motor").setLevel(logging.DEBUG)
    #logging.getLogger("pymongo").setLevel(logging.DEBUG)
    #logging.getLogger("pymongo.command").setLevel(logging.DEBUG)
    
    return root_logger

def _parse_size(size_str):
    """Parse size string like '10MB', '100KB', '1GB' to bytes."""
    size_str = str(size_str).upper()
    if size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    elif size_str.isdigit():
        return int(size_str)
    else:
        return 10 * 1024 * 1024  # Default 10MB

"""
Logging Configuration
Centralized logging setup for the Discord bot
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logger(name: Optional[str] = None, level: str = None) -> logging.Logger:
    """
    Setup and configure the main logger
    
    Args:
        name: Logger name (defaults to 'discord_bot')
        level: Logging level (defaults to environment variable or INFO)
        
    Returns:
        Configured logger instance
    """
    logger_name = name or 'discord_bot'
    log_level = level or os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logger
    logger = logging.getLogger(logger_name)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set level
    try:
        logger.setLevel(getattr(logging, log_level))
    except AttributeError:
        logger.setLevel(logging.INFO)
        logger.warning(f"Invalid log level '{log_level}', defaulting to INFO")
    
    # Create formatters
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if logs directory exists or can be created)
    log_dir = os.getenv('LOG_DIR', 'logs')
    if log_dir:
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f'discord_bot_{datetime.now().strftime("%Y%m%d")}.log')
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not create file handler: {e}")
    
    # Set third-party library log levels
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('google.generativeai').setLevel(logging.WARNING)
    
    logger.info(f"Logger '{logger_name}' initialized with level {log_level}")
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Logger instance
    """
    # Create a child logger
    main_logger = logging.getLogger('discord_bot')
    
    # Extract just the module name from full path
    if '.' in name:
        module_name = name.split('.')[-1]
    else:
        module_name = name
    
    child_logger = main_logger.getChild(module_name)
    return child_logger

class LoggerContextManager:
    """Context manager for temporary log level changes"""
    
    def __init__(self, logger: logging.Logger, level: str):
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = logger.level
    
    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)

def with_log_level(logger: logging.Logger, level: str):
    """
    Context manager for temporarily changing log level
    
    Args:
        logger: Logger instance
        level: Temporary log level
        
    Returns:
        Context manager
    """
    return LoggerContextManager(logger, level)

# Performance logging decorator
def log_performance(logger: logging.Logger):
    """
    Decorator to log function execution time
    
    Args:
        logger: Logger instance to use
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator

# Async performance logging decorator
def log_async_performance(logger: logging.Logger):
    """
    Decorator to log async function execution time
    
    Args:
        logger: Logger instance to use
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator

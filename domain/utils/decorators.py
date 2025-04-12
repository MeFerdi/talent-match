import functools
import time
from typing import Callable, Any, TypeVar
from domain.utils.logging import logger

F = TypeVar('F', bound=Callable[..., Any])

def validate_input(func: F) -> F:
    """Decorator to validate function inputs using type hints"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        type_hints = func.__annotations__
        params = list(type_hints.keys())
        
        # Skip 'self' for instance methods
        start_idx = 1 if 'self' in params and len(args) > 0 and args[0] is params[0] else 0
        
        # Validate args
        for i, arg in enumerate(args[start_idx:], start=start_idx):
            if i < len(params):
                param_name = params[i]
                expected_type = type_hints[param_name]
                if not isinstance(arg, expected_type):
                    raise TypeError(f"Argument '{param_name}' must be {expected_type.__name__}")
        
        # Validate kwargs
        for k, v in kwargs.items():
            if k in type_hints and not isinstance(v, type_hints[k]):
                raise TypeError(f"Argument '{k}' must be {type_hints[k].__name__}")
                
        return func(*args, **kwargs)
    return wrapper

def retry(max_retries: int = 3, delay: float = 1.0, retry_on: tuple = (Exception,)):
    """Decorator to retry failed operations"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:  # Retry only on specified exceptions
                    last_exception = e
                    logger.warning(f"Attempt {attempt} failed: {str(e)}")
                    if attempt < max_retries:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

def timed(func: F, log_level: str = "info") -> F:
    """Decorator to log execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        log_message = f"{func.__name__} executed in {end_time - start_time:.4f}s"
        if log_level.lower() == "debug":
            logger.debug(log_message)
        elif log_level.lower() == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
        return result
    return wrapper
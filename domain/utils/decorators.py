import functools
import time
from typing import Callable, Any, TypeVar
from domain.utils.logging import logger

F = TypeVar('F', bound=Callable[..., Any])

def validate_input(func: F) -> F:
    """Decorator to validate function inputs using type hints"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get type hints
        type_hints = func.__annotations__
        
        # Validate args
        for i, arg in enumerate(args):
            param_name = list(type_hints.keys())[i]
            expected_type = type_hints[param_name]
            if not isinstance(arg, expected_type):
                raise TypeError(f"Argument '{param_name}' must be {expected_type.__name__}")
        
        # Validate kwargs
        for k, v in kwargs.items():
            if k in type_hints and not isinstance(v, type_hints[k]):
                raise TypeError(f"Argument '{k}' must be {type_hints[k].__name__}")
                
        return func(*args, **kwargs)
    return wrapper

def retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry failed operations"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt} failed: {str(e)}")
                    if attempt < max_retries:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

def timed(func: F) -> F:
    """Decorator to log execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.info(f"{func.__name__} executed in {end_time - start_time:.4f}s")
        return result
    return wrapper
import functools
import inspect
import time
from typing import Callable, Any, TypeVar, Union
from domain.utils.logging import logger

F = TypeVar('F', bound=Callable[..., Any])

def validate_input(func: F) -> F:
    """Decorator to validate function inputs using type hints"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get type hints, skipping return type if present
        type_hints = {
            k: v for k, v in func.__annotations__.items() 
            if k != 'return'
        }
        
        # Handle bound methods (skip 'self' parameter)
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Validate all parameters
        for param_name, value in bound_args.arguments.items():
            if param_name in type_hints:
                expected_type = type_hints[param_name]
                origin_type = getattr(expected_type, "__origin__", expected_type)
                
                # Handle Optional types
                if origin_type is Union:
                    type_args = expected_type.__args__
                    if type(None) in type_args:
                        expected_type = Union[tuple(
                            t for t in type_args if t is not type(None)
                        )]
                
                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"Argument '{param_name}' must be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
        
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
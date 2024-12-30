import functools
import logging
from typing import Type, Callable, Any
from .exceptions import BilibiliBlacklistError

def error_handler(error_types: tuple = (Exception,),
                 message: str = None,
                 cleanup: Callable = None):
    """统一的错误处理装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except error_types as e:
                logging.error(f"{func.__name__} failed: {str(e)}")
                if message:
                    logging.error(message)
                if cleanup:
                    cleanup()
                raise BilibiliBlacklistError(
                    message or str(e),
                    cause=e
                )
        return wrapper
    return decorator

def retry(max_retries: int = 3, 
         delay: float = 1.0,
         exceptions: tuple = (Exception,)):
    """重试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for i in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if i < max_retries - 1:
                        await asyncio.sleep(delay)
            raise last_error
        return wrapper
    return decorator 
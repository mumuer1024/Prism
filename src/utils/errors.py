"""
统一错误处理和日志工具模块

提供标准化的错误处理、日志记录、装饰器等功能
"""
import logging
from functools import wraps
from typing import Callable, TypeVar, Any, Optional
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PrismError(Exception):
    """项目基础异常类"""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class SensorError(PrismError):
    """数据采集相关错误"""
    
    def __init__(self, message: str, source: str = ""):
        super().__init__(message, code="SENSOR_ERROR")
        self.source = source


class APIError(PrismError):
    """API 调用相关错误"""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, code="API_ERROR")
        self.status_code = status_code


def handle_errors(
    log_level: str = "error",
    reraise: bool = False,
    default_return: Any = None
) -> Callable:
    """统一错误处理装饰器
    
    Args:
        log_level: 日志级别 (debug, info, warning, error, exception)
        reraise: 是否重新抛出异常
        default_return: 异常时的默认返回值
        
    Returns:
        装饰后的函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            log_func = getattr(logger, log_level, logger.error)
            try:
                return func(*args, **kwargs)
            except HTTPException:
                # FastAPI HTTPException 不处理，直接抛出
                raise
            except httpx.TimeoutException as e:
                log_func(f"{func.__name__} timeout: {e}")
                if reraise:
                    raise
                return default_return
            except httpx.HTTPStatusError as e:
                log_func(f"{func.__name__} HTTP error: {e.response.status_code}")
                if reraise:
                    raise
                return default_return
            except PrismError as e:
                log_func(f"{func.__name__} PrismError [{e.code}]: {e.message}")
                if reraise:
                    raise
                return default_return
            except Exception as e:
                logger.exception(f"{func.__name__} unexpected error: {e}")
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (httpx.HTTPError,),
) -> Callable:
    """请求重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍增因子
        exceptions: 需要重试的异常类型
        
    Returns:
        装饰后的函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1} failed, "
                            f"retrying in {current_delay}s: {e}"
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
            
            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed after {max_retries} retries")
        
        return wrapper
    return decorator


# 预定义错误处理器
def handle_sensor_error(source_name: str) -> Callable:
    """为传感器创建专用错误处理器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except httpx.TimeoutException:
                logger.warning(f"{source_name} timeout")
                raise SensorError(f"{source_name} 请求超时", source=source_name)
            except httpx.HTTPStatusError as e:
                logger.warning(f"{source_name} HTTP {e.response.status_code}")
                raise SensorError(f"{source_name} HTTP错误: {e.response.status_code}", source=source_name)
            except Exception as e:
                logger.exception(f"{source_name} unexpected error: {e}")
                raise SensorError(f"{source_name} 未知错误: {str(e)}", source=source_name)
        return wrapper
    return decorator

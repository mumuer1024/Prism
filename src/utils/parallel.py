"""
并行处理工具模块

提供并行执行、缓存等性能优化工具
"""
import time
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from typing import Callable, List, Iterable, TypeVar, Any, Optional, Dict, Tuple

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


# ═══════════════════════════════════════════════════════════
# 并行处理
# ═══════════════════════════════════════════════════════════

def parallel_map(
    func: Callable[[T], R],
    items: Iterable[T],
    max_workers: int = 5,
    timeout: Optional[float] = 30.0,
    fail_silently: bool = True,
) -> List[Optional[R]]:
    """并行执行函数并返回结果列表
    
    Args:
        func: 要执行的函数
        items: 输入数据列表
        max_workers: 最大并行数
        timeout: 单个任务超时时间
        fail_silently: 失败时返回 None 而非抛出异常
        
    Returns:
        结果列表（保持原始顺序）
    """
    results: List[Optional[R]] = []
    items_list = list(items)
    total = len(items_list)
    
    if total == 0:
        return []
    
    if total == 1:
        # 单个项目无需并行
        try:
            results.append(func(items_list[0]))
        except Exception as e:
            if fail_silently:
                logger.warning(f"Task failed: {e}")
                results.append(None)
            else:
                raise
        return results
    
    results = [None] * total
    
    with ThreadPoolExecutor(max_workers=min(max_workers, total)) as executor:
        future_to_index: Dict[Any, int] = {}
        
        for i, item in enumerate(items_list):
            future = executor.submit(func, item)
            future_to_index[future] = i
        
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                if timeout:
                    results[idx] = future.result(timeout=timeout)
                else:
                    results[idx] = future.result()
            except Exception as e:
                if fail_silently:
                    logger.warning(f"Task {idx} failed: {e}")
                    results[idx] = None
                else:
                    logger.error(f"Task {idx} failed: {e}")
                    raise
    
    success_count = sum(1 for r in results if r is not None)
    logger.debug(f"parallel_map completed: {success_count}/{total} succeeded")
    
    return results


def parallel_map_with_errors(
    func: Callable[[T], R],
    items: Iterable[T],
    max_workers: int = 5,
    timeout: Optional[float] = 30.0,
) -> List[Tuple[Optional[R], Optional[Exception]]]:
    """并行执行，返回结果和错误元组列表
    
    Returns:
        [(result1, error1), (result2, error2), ...]
        成功时 result 不为 None，error 为 None
        失败时 result 为 None，error 不为 None
    """
    items_list = list(items)
    results: List[Tuple[Optional[R], Optional[Exception]]] = [(None, None) for _ in items_list]
    
    if not items_list:
        return []
    
    with ThreadPoolExecutor(max_workers=min(max_workers, len(items_list))) as executor:
        future_to_index = {
            executor.submit(func, item): i 
            for i, item in enumerate(items_list)
        }
        
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = (future.result(timeout=timeout), None)
            except Exception as e:
                results[idx] = (None, e)
    
    return results


# ═══════════════════════════════════════════════════════════
# 缓存
# ═══════════════════════════════════════════════════════════

class SimpleCache:
    """简单的内存缓存"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._default_ttl = default_ttl
    
    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """生成缓存 key"""
        key_data = f"{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._default_ttl:
                return value
            del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        self._cache[key] = (value, time.time())
    
    def delete(self, key: str) -> None:
        """删除缓存"""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """清理过期缓存，返回清理数量"""
        now = time.time()
        expired_keys = [
            k for k, (_, timestamp) in self._cache.items()
            if now - timestamp >= self._default_ttl
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# 全局缓存实例
_cache = SimpleCache(default_ttl=300)


def cached(
    ttl_seconds: int = 300,
    key_prefix: str = "",
    cache: Optional[SimpleCache] = None,
) -> Callable:
    """缓存装饰器
    
    Args:
        ttl_seconds: 缓存有效期（秒）
        key_prefix: key 前缀
        cache: 缓存实例，默认使用全局缓存
        
    Returns:
        装饰后的函数
    """
    _cache_instance = cache or _cache
    
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # 生成缓存 key
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.append(str(args))
            if kwargs:
                key_parts.append(str(sorted(kwargs.items())))
            key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # 尝试从缓存获取
            cached_value = _cache_instance.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            _cache_instance.set(key, result, ttl_seconds)
            logger.debug(f"Cache miss: {func.__name__}")
            
            return result
        
        # 暴露清理方法
        wrapper.clear_cache = lambda: _cache_instance.clear()
        wrapper.clear_cache_for_func = lambda: _cache_instance.clear()  # 可扩展
        return wrapper
    
    return decorator


# ═══════════════════════════════════════════════════════════
# 速率限制
# ═══════════════════════════════════════════════════════════

class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self._calls: List[float] = []
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            now = time.time()
            
            # 清理过期调用记录
            self._calls = [t for t in self._calls if now - t < self.time_window]
            
            if len(self._calls) >= self.max_calls:
                sleep_time = self.time_window - (now - self._calls[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, sleeping {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    self._calls = []
            
            self._calls.append(time.time())
            return func(*args, **kwargs)
        
        return wrapper


# ═══════════════════════════════════════════════════════════
# 使用示例
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 示例：并行获取多个数据源
    def fetch_source_data(source: str) -> dict:
        """模拟获取数据源数据"""
        import random
        time.sleep(random.uniform(0.1, 0.5))
        return {"source": source, "data": [1, 2, 3]}
    
    sources = ["HN", "GitHub", "V2EX", "36Kr", "ProductHunt"]
    
    print("=== 串行执行 ===")
    start = time.time()
    results = [fetch_source_data(s) for s in sources]
    print(f"耗时: {time.time() - start:.2f}s")
    
    print("\n=== 并行执行 ===")
    start = time.time()
    results = parallel_map(fetch_source_data, sources, max_workers=3)
    print(f"耗时: {time.time() - start:.2f}s")
    
    print("\n=== 缓存示例 ===")
    @cached(ttl_seconds=10)
    def slow_function(x: int) -> int:
        time.sleep(1)
        return x * 2
    
    start = time.time()
    print(f"结果: {slow_function(5)}")  # 慢
    print(f"耗时: {time.time() - start:.2f}s")
    
    start = time.time()
    print(f"结果: {slow_function(5)}")  # 快
    print(f"耗时: {time.time() - start:.2f}s")

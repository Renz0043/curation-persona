import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar

import httpx

logger = logging.getLogger(__name__)

RETRY_CONFIG = {
    "max_retries": 3,
    "initial_delay_sec": 1,
    "max_delay_sec": 30,
    "exponential_base": 2,
}

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

T = TypeVar("T")


def is_retryable(exception: Exception) -> bool:
    if isinstance(exception, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in RETRYABLE_STATUS_CODES
    return False


def with_retry(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        delay = RETRY_CONFIG["initial_delay_sec"]
        max_retries = RETRY_CONFIG["max_retries"]
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if not is_retryable(e):
                    logger.error(f"Non-retryable error: {e}")
                    raise
                logger.warning(f"Retry {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay = min(
                        delay * RETRY_CONFIG["exponential_base"],
                        RETRY_CONFIG["max_delay_sec"],
                    )

        logger.error(f"All {max_retries} retries exhausted")
        raise last_exception

    return wrapper

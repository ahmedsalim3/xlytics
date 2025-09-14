import asyncio
import time
from functools import wraps

from ...commons.logger import Logger

logger = Logger()


def retry_on_exception(max_retries=3, delay=60, backoff=2, exceptions=(Exception,)):
    """Decorator for retry logic with exponential backoff"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    logger.debug(
                        f"Executing {func.__name__} (attempt {attempt + 1}/{max_retries})"
                    )
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(
                        f"[{func.__name__}] Attempt {attempt + 1} failed: {e}"
                    )
                    if attempt < max_retries - 1:
                        logger.info(
                            f"Waiting {current_delay} seconds before retry {attempt + 2}/{max_retries}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"[{func.__name__}] All {max_retries} attempts failed"
                        )
                        raise
            return None

        return wrapper

    return decorator


def retry_on_exception_async(
    max_retries=3, delay=60, backoff=2, exceptions=(Exception,)
):
    """Async decorator for retry logic with exponential backoff"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    logger.debug(
                        f"Executing {func.__name__} async (attempt {attempt + 1}/{max_retries})"
                    )
                    return await func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(
                        f"[{func.__name__}] Attempt {attempt + 1} failed: {e}"
                    )
                    if attempt < max_retries - 1:
                        logger.info(
                            f"Waiting {current_delay} seconds before retry {attempt + 2}/{max_retries}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"[{func.__name__}] All {max_retries} attempts failed"
                        )
                        raise
            return None

        return wrapper

    return decorator

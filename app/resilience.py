import time
import logging

logger = logging.getLogger(__name__)

# -----------------------------
# Retry + timeout config
# -----------------------------
MAX_RETRIES = 2
RETRY_DELAY = 1.0  # seconds between retries


def with_retry(func, *args, retries=MAX_RETRIES, delay=RETRY_DELAY, **kwargs):
    """
    Wrap a function call with retry logic.
    Retries on any exception up to `retries` times.
    """
    last_error = None
    for attempt in range(1, retries + 2):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt <= retries:
                logger.warning(
                    f"Attempt {attempt} failed: {str(e)}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"All {retries + 1} attempts failed. "
                    f"Last error: {str(e)}"
                )
    raise last_error
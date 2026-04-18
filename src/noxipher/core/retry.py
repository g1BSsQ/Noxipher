import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .exceptions import NetworkError

def with_retry(max_attempts: int = 3):
    """
    Decorator for adding exponential backoff retries to async network calls.
    Retries on httpx.RequestError and NetworkError.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=(
            retry_if_exception_type(httpx.RequestError) |
            retry_if_exception_type(NetworkError)
        ),
        reraise=True
    )

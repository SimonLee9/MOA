"""
Retry Utilities for Pipeline Nodes
Implements exponential backoff and retry logic
"""

import asyncio
import logging
from typing import TypeVar, Callable, Awaitable, Optional, Type, Tuple
from functools import wraps

from pipeline.errors import (
    PipelineError,
    ErrorSeverity,
    MaxRetriesExceededError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    ):
        """
        Initialize retry configuration

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential_base: Base for exponential backoff
            jitter: Add randomness to delays to prevent thundering herd
            retry_on: Tuple of exception types to retry on (default: all PipelineError)
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or (PipelineError,)


# Default configurations for different scenarios
RETRY_CONFIGS = {
    "stt": RetryConfig(
        max_retries=3,
        initial_delay=5.0,
        max_delay=120.0,
    ),
    "llm": RetryConfig(
        max_retries=3,
        initial_delay=2.0,
        max_delay=60.0,
    ),
    "mcp": RetryConfig(
        max_retries=2,
        initial_delay=1.0,
        max_delay=30.0,
    ),
    "default": RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        max_delay=60.0,
    ),
}


def calculate_delay(
    attempt: int,
    config: RetryConfig,
    error: Optional[PipelineError] = None,
) -> float:
    """
    Calculate delay before next retry attempt

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
        error: Optional error with retry_delay hint

    Returns:
        Delay in seconds
    """
    # Use error's suggested delay if available
    if error and hasattr(error, "retry_delay") and error.retry_delay > 0:
        base_delay = error.retry_delay
    else:
        # Exponential backoff
        base_delay = config.initial_delay * (config.exponential_base ** attempt)

    # Cap at max delay
    delay = min(base_delay, config.max_delay)

    # Add jitter (0-50% of delay)
    if config.jitter:
        import random
        jitter_amount = delay * random.uniform(0, 0.5)
        delay += jitter_amount

    return delay


def should_retry(
    error: Exception,
    config: RetryConfig,
    attempt: int,
) -> bool:
    """
    Determine if an error should be retried

    Args:
        error: The exception that occurred
        config: Retry configuration
        attempt: Current attempt number

    Returns:
        True if should retry, False otherwise
    """
    # Check max retries
    if attempt >= config.max_retries:
        return False

    # Check if error type is retryable
    if not isinstance(error, config.retry_on):
        return False

    # Check PipelineError specific flags
    if isinstance(error, PipelineError):
        if not error.recoverable:
            return False
        if error.severity == ErrorSeverity.CRITICAL:
            return False

    return True


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args,
    config: Optional[RetryConfig] = None,
    node_name: str = "unknown",
    **kwargs,
) -> T:
    """
    Execute an async function with retry logic

    Args:
        func: Async function to execute
        *args: Positional arguments for func
        config: Retry configuration (uses default if None)
        node_name: Name of the node for logging
        **kwargs: Keyword arguments for func

    Returns:
        Result of the function call

    Raises:
        MaxRetriesExceededError: If all retries exhausted
        Exception: Original exception if not retryable
    """
    config = config or RETRY_CONFIGS.get(node_name, RETRY_CONFIGS["default"])

    last_error: Optional[Exception] = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            last_error = e

            if not should_retry(e, config, attempt):
                logger.error(
                    f"[{node_name}] Non-retryable error on attempt {attempt + 1}: {e}"
                )
                raise

            delay = calculate_delay(attempt, config, e if isinstance(e, PipelineError) else None)

            logger.warning(
                f"[{node_name}] Attempt {attempt + 1}/{config.max_retries + 1} failed: {e}. "
                f"Retrying in {delay:.1f}s..."
            )

            await asyncio.sleep(delay)

    # All retries exhausted
    raise MaxRetriesExceededError(
        message=f"Max retries ({config.max_retries}) exceeded for {node_name}",
        node=node_name,
        max_retries=config.max_retries,
        context={"last_error": str(last_error)},
    )


def with_retry(
    config: Optional[RetryConfig] = None,
    node_name: str = "unknown",
):
    """
    Decorator for adding retry logic to async functions

    Usage:
        @with_retry(config=RETRY_CONFIGS["llm"], node_name="summarizer")
        async def generate_summary(...):
            ...

    Args:
        config: Retry configuration
        node_name: Name of the node for logging

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_async(
                func,
                *args,
                config=config,
                node_name=node_name,
                **kwargs,
            )
        return wrapper
    return decorator


class RetryContext:
    """
    Context manager for tracking retry state within a node

    Usage:
        async with RetryContext(config, "stt") as ctx:
            while ctx.should_continue():
                try:
                    result = await do_something()
                    break
                except Exception as e:
                    await ctx.handle_error(e)
    """

    def __init__(self, config: RetryConfig, node_name: str = "unknown"):
        self.config = config
        self.node_name = node_name
        self.attempt = 0
        self.last_error: Optional[Exception] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def should_continue(self) -> bool:
        """Check if more attempts are allowed"""
        return self.attempt <= self.config.max_retries

    async def handle_error(self, error: Exception) -> None:
        """
        Handle an error and prepare for retry

        Raises:
            Exception: If error is not retryable
            MaxRetriesExceededError: If max retries exceeded
        """
        self.last_error = error
        self.attempt += 1

        if not should_retry(error, self.config, self.attempt - 1):
            raise error

        if self.attempt > self.config.max_retries:
            raise MaxRetriesExceededError(
                message=f"Max retries exceeded for {self.node_name}",
                node=self.node_name,
                max_retries=self.config.max_retries,
                context={"last_error": str(error)},
            )

        delay = calculate_delay(
            self.attempt - 1,
            self.config,
            error if isinstance(error, PipelineError) else None,
        )

        logger.warning(
            f"[{self.node_name}] Attempt {self.attempt}/{self.config.max_retries + 1} "
            f"failed: {error}. Retrying in {delay:.1f}s..."
        )

        await asyncio.sleep(delay)

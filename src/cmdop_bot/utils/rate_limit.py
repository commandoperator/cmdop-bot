"""Rate limiting utilities."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar

from cmdop_bot.exceptions import RateLimitError

T = TypeVar("T")


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    requests_per_minute: int = 60
    requests_per_second: int = 5
    burst_size: int = 10


@dataclass
class TokenBucket:
    """Token bucket rate limiter.

    Implements the token bucket algorithm for smooth rate limiting.
    Tokens are added at a constant rate, and each request consumes one token.

    Example:
        >>> bucket = TokenBucket(rate=10.0, capacity=20)
        >>> if bucket.consume():
        ...     # Request allowed
        ...     pass
        >>> else:
        ...     # Rate limited
        ...     pass
    """

    rate: float  # Tokens per second
    capacity: int  # Maximum tokens
    tokens: float = field(init=False)
    last_update: float = field(init=False)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)
        self.last_update = time.monotonic()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if rate limited
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_time(self) -> float:
        """Get time to wait until a token is available."""
        self._refill()
        if self.tokens >= 1:
            return 0.0
        return (1 - self.tokens) / self.rate

    async def wait_and_consume(self, tokens: int = 1) -> None:
        """Wait until tokens are available and consume them."""
        while not self.consume(tokens):
            wait = self.wait_time()
            await asyncio.sleep(wait)


class RateLimiter:
    """Per-user/channel rate limiter.

    Manages rate limits for multiple users across multiple channels.

    Example:
        >>> limiter = RateLimiter()
        >>> if limiter.check("telegram:123"):
        ...     # Request allowed
        ...     pass
        >>> else:
        ...     # Rate limited
        ...     raise RateLimitError("Too many requests", retry_after=limiter.retry_after("telegram:123"))
    """

    def __init__(
        self,
        config: RateLimitConfig | None = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self._config = config or RateLimitConfig()
        self._buckets: dict[str, TokenBucket] = {}

    def _get_bucket(self, key: str) -> TokenBucket:
        """Get or create bucket for key."""
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                rate=self._config.requests_per_second,
                capacity=self._config.burst_size,
            )
        return self._buckets[key]

    def check(self, user_id: str) -> bool:
        """Check if request is allowed.

        Args:
            user_id: User identifier (e.g., "telegram:123")

        Returns:
            True if allowed, False if rate limited
        """
        bucket = self._get_bucket(user_id)
        return bucket.consume()

    def retry_after(self, user_id: str) -> float:
        """Get seconds until user can retry.

        Args:
            user_id: User identifier

        Returns:
            Seconds to wait
        """
        bucket = self._get_bucket(user_id)
        return bucket.wait_time()

    async def wait(self, user_id: str) -> None:
        """Wait until request is allowed.

        Args:
            user_id: User identifier
        """
        bucket = self._get_bucket(user_id)
        await bucket.wait_and_consume()

    def check_or_raise(self, user_id: str) -> None:
        """Check rate limit, raise if exceeded.

        Args:
            user_id: User identifier

        Raises:
            RateLimitError: If rate limit exceeded
        """
        if not self.check(user_id):
            retry = self.retry_after(user_id)
            raise RateLimitError(
                f"Rate limit exceeded. Try again in {retry:.1f}s",
                retry_after=retry,
            )

    def reset(self, user_id: str) -> None:
        """Reset rate limit for user.

        Args:
            user_id: User identifier
        """
        if user_id in self._buckets:
            del self._buckets[user_id]

    def reset_all(self) -> None:
        """Reset all rate limits."""
        self._buckets.clear()


def rate_limited(
    limiter: RateLimiter,
    get_user_id: Callable[[T], str],
) -> Callable:
    """Decorator for rate-limited functions.

    Args:
        limiter: RateLimiter instance
        get_user_id: Function to extract user_id from first argument

    Example:
        >>> limiter = RateLimiter()
        >>> @rate_limited(limiter, lambda msg: msg.user.unique_id)
        ... async def handle_message(msg: Message) -> None:
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(arg: T, *args, **kwargs):
            user_id = get_user_id(arg)
            limiter.check_or_raise(user_id)
            return await func(arg, *args, **kwargs)
        return wrapper
    return decorator

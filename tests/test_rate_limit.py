"""Tests for rate limiter."""

import pytest
import asyncio

from cmdop_bot.utils.rate_limit import (
    TokenBucket,
    RateLimiter,
    RateLimitConfig,
)
from cmdop_bot.exceptions import RateLimitError


class TestTokenBucket:
    """Tests for TokenBucket."""

    def test_initial_capacity(self):
        """Test bucket starts with full capacity."""
        bucket = TokenBucket(rate=1.0, capacity=10)
        assert bucket.tokens == 10

    def test_consume_single(self):
        """Test consuming single token."""
        bucket = TokenBucket(rate=1.0, capacity=10)
        assert bucket.consume() is True
        assert bucket.tokens == 9

    def test_consume_multiple(self):
        """Test consuming multiple tokens."""
        bucket = TokenBucket(rate=1.0, capacity=10)
        assert bucket.consume(5) is True
        assert bucket.tokens == 5

    def test_consume_exceeds_capacity(self):
        """Test consuming more than available."""
        bucket = TokenBucket(rate=1.0, capacity=5)
        assert bucket.consume(10) is False
        assert bucket.tokens == 5  # Unchanged

    def test_refill_over_time(self):
        """Test tokens refill over time."""
        bucket = TokenBucket(rate=10.0, capacity=10)  # 10 tokens/sec
        bucket.tokens = 0
        bucket.last_update -= 0.5  # Simulate 0.5 seconds passed

        bucket._refill()
        assert bucket.tokens == pytest.approx(5.0, rel=0.1)

    def test_refill_capped_at_capacity(self):
        """Test tokens don't exceed capacity."""
        bucket = TokenBucket(rate=10.0, capacity=10)
        bucket.last_update -= 100  # Lots of time passed

        bucket._refill()
        assert bucket.tokens == 10

    def test_wait_time_when_empty(self):
        """Test wait time calculation when empty."""
        bucket = TokenBucket(rate=10.0, capacity=10)  # 10 tokens/sec
        bucket.tokens = 0

        wait = bucket.wait_time()
        assert wait == pytest.approx(0.1, rel=0.1)  # 1/10 seconds

    def test_wait_time_when_available(self):
        """Test wait time is 0 when tokens available."""
        bucket = TokenBucket(rate=1.0, capacity=10)
        assert bucket.wait_time() == 0.0


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_default_config(self):
        """Test limiter with default config."""
        limiter = RateLimiter()
        # Should allow initial requests
        for _ in range(10):  # burst_size = 10
            assert limiter.check("user1") is True

    def test_per_user_limits(self):
        """Test each user has separate limits."""
        limiter = RateLimiter(RateLimitConfig(burst_size=2))

        # User 1 uses their limit
        assert limiter.check("user1") is True
        assert limiter.check("user1") is True
        assert limiter.check("user1") is False

        # User 2 still has their limit
        assert limiter.check("user2") is True

    def test_retry_after(self):
        """Test retry_after returns positive value when limited."""
        limiter = RateLimiter(RateLimitConfig(burst_size=1, requests_per_second=1))

        limiter.check("user1")  # Use the one token
        retry = limiter.retry_after("user1")

        assert retry > 0
        assert retry <= 1.0

    def test_check_or_raise(self):
        """Test check_or_raise raises on limit."""
        limiter = RateLimiter(RateLimitConfig(burst_size=1))

        limiter.check("user1")  # Use the one token

        with pytest.raises(RateLimitError) as exc_info:
            limiter.check_or_raise("user1")

        assert exc_info.value.retry_after > 0

    def test_reset_user(self):
        """Test resetting single user."""
        limiter = RateLimiter(RateLimitConfig(burst_size=1))

        limiter.check("user1")
        assert limiter.check("user1") is False

        limiter.reset("user1")
        assert limiter.check("user1") is True

    def test_reset_all(self):
        """Test resetting all users."""
        limiter = RateLimiter(RateLimitConfig(burst_size=1))

        limiter.check("user1")
        limiter.check("user2")

        limiter.reset_all()

        assert limiter.check("user1") is True
        assert limiter.check("user2") is True


@pytest.mark.asyncio
class TestAsyncRateLimiter:
    """Async tests for RateLimiter."""

    async def test_wait_and_consume(self):
        """Test async wait and consume."""
        bucket = TokenBucket(rate=100.0, capacity=10)  # Fast rate
        bucket.tokens = 0

        start = asyncio.get_event_loop().time()
        await bucket.wait_and_consume()
        elapsed = asyncio.get_event_loop().time() - start

        # Should have waited ~0.01 seconds (1/100)
        assert elapsed < 0.1

    async def test_limiter_wait(self):
        """Test limiter wait method."""
        limiter = RateLimiter(RateLimitConfig(
            burst_size=1,
            requests_per_second=100,
        ))

        limiter.check("user1")  # Use token

        start = asyncio.get_event_loop().time()
        await limiter.wait("user1")
        elapsed = asyncio.get_event_loop().time() - start

        assert elapsed < 0.1

"""In-memory login rate limiter (`app/services/rate_limit.py`, Phase 1.1)."""

import time

from app.services.rate_limit import LoginRateLimiter


def test_blocks_after_max_failures_per_username() -> None:
    limiter = LoginRateLimiter(max_per_username=3, max_per_ip=100, window_s=900)

    for _ in range(3):
        assert limiter.is_blocked(username="alice", client_ip="1.1.1.1") is False
        limiter.record_failure(username="alice", client_ip="1.1.1.1")

    assert limiter.is_blocked(username="alice", client_ip="1.1.1.1") is True


def test_blocks_after_max_failures_per_ip_across_usernames() -> None:
    limiter = LoginRateLimiter(max_per_username=100, max_per_ip=2, window_s=900)

    limiter.record_failure(username="alice", client_ip="1.1.1.1")
    limiter.record_failure(username="bob", client_ip="1.1.1.1")

    assert limiter.is_blocked(username="carol", client_ip="1.1.1.1") is True
    assert limiter.is_blocked(username="carol", client_ip="2.2.2.2") is False


def test_record_success_clears_only_that_username() -> None:
    limiter = LoginRateLimiter(max_per_username=2, max_per_ip=100, window_s=900)
    limiter.record_failure(username="alice", client_ip="1.1.1.1")
    limiter.record_failure(username="bob", client_ip="9.9.9.9")

    limiter.record_success(username="alice")

    assert limiter.is_blocked(username="alice", client_ip="1.1.1.1") is False
    limiter.record_failure(username="bob", client_ip="9.9.9.9")
    assert limiter.is_blocked(username="bob", client_ip="9.9.9.9") is True


def test_failures_outside_window_are_pruned() -> None:
    limiter = LoginRateLimiter(max_per_username=1, max_per_ip=100, window_s=0.05)

    limiter.record_failure(username="alice", client_ip="1.1.1.1")
    assert limiter.is_blocked(username="alice", client_ip="1.1.1.1") is True

    time.sleep(0.1)

    assert limiter.is_blocked(username="alice", client_ip="1.1.1.1") is False

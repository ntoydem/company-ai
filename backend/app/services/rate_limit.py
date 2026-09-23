"""In-memory login rate limiting (SPEC_02 §7, ADR-015).

No Redis/Valkey in this stack; the backend runs as a single process (`entrypoint.sh`
starts one `uvicorn` worker), so a module-level in-memory limiter is architecturally
sound for V0. State resets on process restart — an accepted trade-off, not a gap to
fix here.

Limited on both username and client IP: username-only limiting doesn't stop credential
stuffing across many accounts from one source; IP-only limiting doesn't stop a targeted
brute force against one account from rotating source IPs.
"""

import time
from collections import defaultdict, deque


class LoginRateLimiter:
    def __init__(
        self, *, max_per_username: int = 5, max_per_ip: int = 20, window_s: float = 900
    ) -> None:
        self._max_per_username = max_per_username
        self._max_per_ip = max_per_ip
        self._window_s = window_s
        self._by_username: dict[str, deque[float]] = defaultdict(deque)
        self._by_ip: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, failures: deque[float], now: float) -> None:
        while failures and now - failures[0] > self._window_s:
            failures.popleft()

    def is_blocked(self, *, username: str, client_ip: str) -> bool:
        now = time.monotonic()
        username_failures = self._by_username[username]
        ip_failures = self._by_ip[client_ip]
        self._prune(username_failures, now)
        self._prune(ip_failures, now)
        return (
            len(username_failures) >= self._max_per_username or len(ip_failures) >= self._max_per_ip
        )

    def record_failure(self, *, username: str, client_ip: str) -> None:
        now = time.monotonic()
        self._by_username[username].append(now)
        self._by_ip[client_ip].append(now)

    def record_success(self, *, username: str) -> None:
        self._by_username.pop(username, None)

import threading
import time
from typing import Optional


class SimpleRateLimiter:
    """
    Very lightweight rate limiter that enforces a minimum delay between requests.

    It is process-local and thread-safe. Use for client-side politeness and to
    smooth bursts. For strict per-hour quotas, prefer a token bucket.
    """

    def __init__(self, min_delay_seconds: float = 0.0) -> None:
        self._min_delay_seconds: float = max(0.0, float(min_delay_seconds))
        self._lock = threading.Lock()
        self._last_request_monotonic: Optional[float] = None

    def acquire(self) -> None:
        """Blocks to ensure at least min_delay_seconds since last acquire."""
        if self._min_delay_seconds <= 0:
            return
        with self._lock:
            now = time.monotonic()
            if self._last_request_monotonic is None:
                self._last_request_monotonic = now
                return
            elapsed = now - self._last_request_monotonic
            sleep_for = self._min_delay_seconds - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)
            self._last_request_monotonic = time.monotonic()



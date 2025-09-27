from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests
from requests import Response

from src.utils.config import settings
from .rate_limiter import SimpleRateLimiter


class MercadoLibreClient:
    """
    Minimal MercadoLibre public API client using requests.
    - Adds simple rate limit delay between requests
    - Retries with exponential backoff on 429 and 5xx
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        request_delay_seconds: Optional[float] = None,
        max_retries: int = 3,
        timeout_seconds: float = 15.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url: str = (base_url or settings.ML_API_BASE_URL).rstrip("/")
        self.timeout_seconds: float = float(timeout_seconds)
        self.max_retries: int = int(max_retries)
        min_delay = request_delay_seconds if request_delay_seconds is not None else settings.REQUEST_DELAY_SECONDS
        self._limiter = SimpleRateLimiter(min_delay_seconds=float(min_delay))
        self.session = session or requests.Session()

    # -------------- public methods --------------
    def get_product_info(self, item_id: str) -> Dict[str, Any]:
        if self._is_offline():
            return self._offline_get_product_info(item_id)
        return self._get(f"/items/{item_id}")

    def get_product_reviews(self, item_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        if self._is_offline():
            return self._offline_get_product_reviews(item_id, limit=limit, offset=offset)
        params = {"limit": max(1, min(50, int(limit))), "offset": max(0, int(offset))}
        # Reviews endpoint may vary by site. Using /reviews/item/ endpoint used publicly
        return self._get(f"/reviews/item/{item_id}", params=params)

    def search_products(self, query: str, site_id: str = "MLA", limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        if self._is_offline():
            return self._offline_search_products(query=query, site_id=site_id, limit=limit, offset=offset)
        params = {"q": query, "limit": max(1, min(50, int(limit))), "offset": max(0, int(offset))}
        return self._get(f"/sites/{site_id}/search", params=params)

    # -------------- internal helpers --------------
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            self._limiter.acquire()
            try:
                headers: Dict[str, str] = {}
                if settings.ML_ACCESS_TOKEN:
                    headers["Authorization"] = f"Bearer {settings.ML_ACCESS_TOKEN}"
                response = self.session.get(url, params=params, headers=headers, timeout=self.timeout_seconds)
                if self._is_retryable_status(response.status_code):
                    self._maybe_sleep_backoff(attempt, response)
                    last_error = self._http_error(response)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                last_error = exc
                # Network or timeout: backoff and retry
                self._maybe_sleep_backoff(attempt)
        # Exhausted retries
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected request failure without exception")

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code < 600

    def _maybe_sleep_backoff(self, attempt: int, response: Optional[Response] = None) -> None:
        if attempt >= self.max_retries:
            return
        # Exponential backoff with jitter
        base = 0.5
        delay = base * (2 ** attempt)
        # Respect Retry-After if present
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    pass
        time.sleep(min(delay, 10.0))

    @staticmethod
    def _http_error(response: Response) -> requests.HTTPError:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        return requests.HTTPError(f"HTTP {response.status_code}: {detail}", response=response)

    # -------------- offline helpers --------------
    @staticmethod
    def _is_offline() -> bool:
        # Offline if explicitly enabled or if there is no token available
        return bool(getattr(settings, "ML_OFFLINE_MODE", False)) or not bool(getattr(settings, "ML_ACCESS_TOKEN", ""))

    @staticmethod
    def _offline_search_products(query: str, site_id: str, limit: int, offset: int) -> Dict[str, Any]:
        # Simple deterministic fixture for local development
        base_results = [
            {"id": f"{site_id}TEST1", "title": f"{query.title()} Test 1", "price": 1000, "site_id": site_id},
            {"id": f"{site_id}TEST2", "title": f"{query.title()} Test 2", "price": 2000, "site_id": site_id},
            {"id": f"{site_id}TEST3", "title": f"{query.title()} Test 3", "price": 3000, "site_id": site_id},
            {"id": f"{site_id}TEST4", "title": f"{query.title()} Test 4", "price": 4000, "site_id": site_id},
            {"id": f"{site_id}TEST5", "title": f"{query.title()} Test 5", "price": 5000, "site_id": site_id},
        ]
        start = max(0, int(offset))
        end = start + max(1, min(50, int(limit)))
        sliced = base_results[start:end]
        return {
            "site_id": site_id,
            "query": query,
            "paging": {"total": len(base_results), "offset": start, "limit": len(sliced), "primary_results": len(sliced)},
            "results": sliced,
        }

    @staticmethod
    def _offline_get_product_info(item_id: str) -> Dict[str, Any]:
        return {
            "id": item_id,
            "title": f"Offline {item_id}",
            "price": 1234,
            "currency_id": "ARS",
            "available_quantity": 10,
            "sold_quantity": 5,
            "condition": "new",
        }

    @staticmethod
    def _offline_get_product_reviews(item_id: str, limit: int, offset: int) -> Dict[str, Any]:
        dummy = [
            {"id": f"R{item_id}1", "rate": 5, "title": "Excelente", "content": "Muy bueno", "date_created": "2024-01-01T00:00:00Z"},
            {"id": f"R{item_id}2", "rate": 3, "title": "Normal", "content": "Cumple", "date_created": "2024-02-01T00:00:00Z"},
        ]
        start = max(0, int(offset))
        end = start + max(1, min(50, int(limit)))
        sliced = dummy[start:end]
        return {"paging": {"total": len(dummy), "offset": start, "limit": len(sliced)}, "reviews": sliced}



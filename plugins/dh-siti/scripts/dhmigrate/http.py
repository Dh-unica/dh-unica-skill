"""Sessione HTTP condivisa con retry e user agent identificabile."""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "dhmigrate/0.1 (+https://dh.unica.it; migrazione minisiti)"
TIMEOUT = 60


def make_session(retries: int = 3) -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    retry = Retry(
        total=retries,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_all(session: requests.Session, url: str, params: dict | None = None, **kwargs) -> list[dict]:
    """GET paginato su una collezione WP REST (usa l'header X-WP-TotalPages)."""
    items: list[dict] = []
    page = 1
    while True:
        query = {"per_page": 100, **(params or {}), "page": page}
        resp = session.get(url, params=query, timeout=TIMEOUT, **kwargs)
        resp.raise_for_status()
        items.extend(resp.json())
        total_pages = int(resp.headers.get("X-WP-TotalPages", "1"))
        if page >= total_pages:
            return items
        page += 1

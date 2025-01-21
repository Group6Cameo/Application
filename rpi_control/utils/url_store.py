"""Utility module for storing and retrieving the backend URL."""

import json
from pathlib import Path

URL_STORE_PATH = Path("/tmp/cameo_backend_url.json")


def clean_backend_url() -> None:
    """Remove any existing backend URL file."""
    if URL_STORE_PATH.exists():
        URL_STORE_PATH.unlink()


def save_backend_url(url: str) -> None:
    """Save the backend URL to a file."""
    URL_STORE_PATH.write_text(json.dumps({"backend_url": url}))


def get_backend_url() -> str:
    """Retrieve the backend URL from file."""
    try:
        data = json.loads(URL_STORE_PATH.read_text())
        return data.get("backend_url")
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# gutenberg_api.py
"""
Helper utilities for retrieving Project Gutenberg texts through RapidAPI.
"""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
import requests

load_dotenv()

RAPIDAPI_KEY = os.getenv("GUTENBERG_RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv(
    "GUTENBERG_RAPIDAPI_HOST", "project-gutenberg-free-books-api1.p.rapidapi.com"
)
BASE_URL = os.getenv(
    "GUTENBERG_BASE_URL", "https://project-gutenberg-free-books-api1.p.rapidapi.com/books"
)
DEFAULT_CLEANING_MODE = os.getenv("GUTENBERG_CLEANING_MODE", "simple")


class GutenbergAPIError(RuntimeError):
    """Raised when the Gutenberg RapidAPI call fails or returns unexpected data."""


def _validate_config() -> None:
    if not RAPIDAPI_KEY:
        raise GutenbergAPIError(
            "Missing RapidAPI key. Set GUTENBERG_RAPIDAPI_KEY in your .env file."
        )


def _extract_text(payload: Any) -> str:
    """
    Try to extract the actual book text from different possible payload shapes.
    RapidAPI variants often return either a string, a `text` field, or a `data.text`.
    """
    if isinstance(payload, str):
        return payload

    if isinstance(payload, dict):
        candidate_keys = [
            "text",
            "data",
            "output",
            "book_text",
            "content",
            "result",
        ]
        for key in candidate_keys:
            if key not in payload:
                continue
            value = payload[key]
            if isinstance(value, str):
                return value
            if isinstance(value, dict) and isinstance(value.get("text"), str):
                return value["text"]

    raise GutenbergAPIError("Could not find text field in API response.")


def fetch_book_text(book_id: str) -> tuple[str, str]:
    """
    Fetches a Project Gutenberg book via RapidAPI.

    Returns:
        (title, text) tuple.
    """
    _validate_config()

    url = f"{BASE_URL}/{book_id}/text"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    params = {}
    if DEFAULT_CLEANING_MODE:
        params["cleaning_mode"] = DEFAULT_CLEANING_MODE

    resp = requests.get(url, headers=headers, params=params, timeout=60)
    if resp.status_code != 200:
        raise GutenbergAPIError(f"RapidAPI request failed ({resp.status_code}): {resp.text[:200]}")

    payload = resp.json()

    # Try to derive a title; fall back to the book ID.
    title = book_id
    if isinstance(payload, dict):
        title = payload.get("title") or payload.get("book", {}).get("title") or book_id

    text = _extract_text(payload)
    if not text.strip():
        raise GutenbergAPIError("Received empty text from API.")

    return title, text

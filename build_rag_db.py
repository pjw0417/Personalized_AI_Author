"""
Utility script that pulls books from the Project Gutenberg RapidAPI and
persists them into the Chroma vector store.
"""
from __future__ import annotations

import os
from typing import Iterable

from dotenv import load_dotenv

from gutenberg_api import GutenbergAPIError, fetch_book_text
from rag_store import build_vectorstore_from_texts

DEFAULT_BOOK_IDS = ["1342", "1661", "98"]  


def load_books_from_api(book_ids: Iterable[str]) -> dict[str, str]:
    """
    Fetches a list of book IDs from the RapidAPI endpoint and returns {title: text}.
    """
    book_texts: dict[str, str] = {}
    for book_id in book_ids:
        if not book_id:
            continue
        print(f"📚 Fetching book {book_id} ...")
        title, text = fetch_book_text(book_id)
        book_texts[title] = text
        print(f"   ↳ Loaded '{title}' ({len(text)} chars)")
    if not book_texts:
        raise GutenbergAPIError("No books were fetched; check your book IDs and API credentials.")
    return book_texts


def _resolve_book_ids() -> list[str]:
    raw_ids = os.getenv("GUTENBERG_BOOK_IDS")
    if raw_ids:
        ids = [item.strip() for item in raw_ids.split(",") if item.strip()]
        if ids:
            return ids
    print("⚠️  GUTENBERG_BOOK_IDS not set; falling back to DEFAULT_BOOK_IDS.")
    return DEFAULT_BOOK_IDS


if __name__ == "__main__":
    load_dotenv()
    ids = _resolve_book_ids()
    books = load_books_from_api(ids)
    build_vectorstore_from_texts(books)

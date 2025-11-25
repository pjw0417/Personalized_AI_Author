"""Helpers for naming and saving generated artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4


def _sanitize_filename(name: str, fallback: str = "book") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9\-_]+", "_", name).strip("._ ")
    cleaned = re.sub(r"^[_\-\d]+", "", cleaned)  # drop leading digits/underscores
    if not cleaned:
        cleaned = fallback
    return cleaned[:80]


def guess_book_title(plan: str, final_text: str, fallback: str = "book") -> str:
    """
    Extract a best-effort title from the plan (preferred) or final text.
    """
    candidates = []
    skip_substrings = ("working title", "optional subtitle", "deliverables")

    def add_lines(text: str) -> None:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                candidates.append(stripped)

    add_lines(plan)
    add_lines(final_text)

    for idx, line in enumerate(candidates):
        match = re.search(r"(?i)\b(?:working\s+)?title[^:]*[:\-]\s*(.+)", line)
        if match:
            title = match.group(1).strip("\"' ")
            if title:
                return _sanitize_filename(title, fallback)
        if any(term in line.lower() for term in skip_substrings):
            # Use the following line if it looks like a free-standing title
            if idx + 1 < len(candidates):
                next_line = candidates[idx + 1].strip("\"' ")
                if next_line and not any(term in next_line.lower() for term in skip_substrings):
                    return _sanitize_filename(next_line, fallback)

    for line in candidates:
        lowered = line.lower()
        if any(term in lowered for term in skip_substrings):
            continue
        if len(line) <= 80 and not re.match(r"(?i)^(chapter|section)\b", line) and not re.match(r"^\d+[). ]", line):
            return _sanitize_filename(line, fallback)

    return _sanitize_filename(fallback, fallback)


def make_pdf_path(output_dir: Path, title: str) -> Path:
    base = _sanitize_filename(title)
    candidate = output_dir / f"{base}.pdf"
    if candidate.exists():
        candidate = output_dir / f"{base}_{uuid4().hex[:4]}.pdf"
    return candidate

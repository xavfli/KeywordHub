from __future__ import annotations

import csv
import io
from typing import Iterable

from keywordhub.analyzer import KeywordItem
from keywordhub.suggestions import SuggestionPanel


def keywords_to_text(title: str, items: Iterable[KeywordItem]) -> str:
    lines = [title]
    lines.extend(f"{item.term}\t{item.score}\t{item.source}" for item in items)
    return "\n".join(lines)


def suggestions_to_text(panels: Iterable[SuggestionPanel]) -> str:
    lines: list[str] = []
    for panel in panels:
        lines.append(f"[{panel.source}]")
        lines.extend(f"{item.text}\t{item.url}" for item in panel.suggestions)
        lines.append("")
    return "\n".join(lines).strip()


def rows_to_csv_bytes(headers: list[str], rows: list[list[str]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")

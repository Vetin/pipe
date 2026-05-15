"""Markdown report formatting helpers for pipelinebench."""

from __future__ import annotations

from typing import Any

def format_soft_scores(scores: dict[str, Any]) -> str:
    parts = []
    for key, value in scores.items():
        if isinstance(value, dict) and "score" in value:
            comment = f" ({value['comment']})" if value.get("comment") else ""
            threshold = f" minimum={value['minimum']} passed={value.get('passed')}" if "minimum" in value else ""
            parts.append(f"{key}: {value.get('score')}/{value.get('max')}{threshold}{comment}")
        else:
            parts.append(f"{key}: {value}")
    return ", ".join(parts)

def markdown_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")

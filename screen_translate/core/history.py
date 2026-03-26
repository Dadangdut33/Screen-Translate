"""Translation history persistence (JSON, same format as original app)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_data_dir

logger = logging.getLogger(__name__)

_HISTORY_PATH: Path = Path(user_data_dir("screen-translate", "Dadangdut33")) / "history.json"


@dataclass
class HistoryEntry:
    """A single translation history record."""

    id: int
    from_lang: str
    to_lang: str
    query: str
    result: str
    engine: str


def _ensure_dir() -> None:
    _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_history() -> list[HistoryEntry]:
    """Load history from disk.

    Returns:
        List of HistoryEntry objects (oldest first).
    """
    _ensure_dir()
    try:
        data = json.loads(_HISTORY_PATH.read_text("utf-8"))
        return [
            HistoryEntry(
                id=item["id"],
                from_lang=item.get("from", ""),
                to_lang=item.get("to", ""),
                query=item.get("query", ""),
                result=item.get("result", ""),
                engine=item.get("engine", ""),
            )
            for item in data.get("tl_history", [])
        ]
    except FileNotFoundError:
        return []
    except Exception as exc:
        logger.exception("Error reading history: %s", exc)
        return []


def append_history(entry: dict[str, str]) -> None:
    """Append a new translation record to history.

    Args:
        entry: Dict with keys ``from``, ``to``, ``query``, ``result``, ``engine``.
    """
    _ensure_dir()
    existing = load_history()
    new_id = len(existing)
    record = HistoryEntry(
        id=new_id,
        from_lang=entry.get("from", ""),
        to_lang=entry.get("to", ""),
        query=entry.get("query", ""),
        result=entry.get("result", ""),
        engine=entry.get("engine", ""),
    )
    existing.append(record)
    _save(existing)


def delete_history_by_ids(ids: set[int]) -> None:
    """Remove entries matching the given IDs and re-index.

    Args:
        ids: Set of record IDs to remove.
    """
    entries = [e for e in load_history() if e.id not in ids]
    for idx, entry in enumerate(entries):
        entry.id = idx
    _save(entries)


def clear_history() -> None:
    """Remove all history records."""
    _save([])


def _save(entries: list[HistoryEntry]) -> None:
    """Write entries to disk.

    Args:
        entries: List of HistoryEntry to persist.
    """
    payload = {"tl_history": [{"id": e.id, "from": e.from_lang, "to": e.to_lang, "query": e.query, "result": e.result, "engine": e.engine} for e in entries]}
    _HISTORY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")

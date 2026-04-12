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
    ocr_run_id: str = ""
    ocr_image_tags: list[str] | None = None
    ocr_image_paths: list[str] | None = None


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
                ocr_run_id=item.get("ocr_run_id", ""),
                ocr_image_tags=list(item.get("ocr_image_tags", []) or []),
                ocr_image_paths=list(item.get("ocr_image_paths", []) or []),
            )
            for item in data.get("tl_history", [])
        ]
    except FileNotFoundError:
        return []
    except Exception as exc:
        logger.exception("Error reading history: %s", exc)
        return []


def append_history(entry: dict[str, object]) -> HistoryEntry:
    """Append a new translation record to history.

    Args:
        entry: Dict with keys ``from``, ``to``, ``query``, ``result``, ``engine``.
    """
    _ensure_dir()
    existing = load_history()
    new_id = len(existing)
    record = HistoryEntry(
        id=new_id,
        from_lang=str(entry.get("from", "")),
        to_lang=str(entry.get("to", "")),
        query=str(entry.get("query", "")),
        result=str(entry.get("result", "")),
        engine=str(entry.get("engine", "")),
        ocr_run_id=str(entry.get("ocr_run_id", "")),
        ocr_image_tags=[
            str(tag) for tag in list(entry.get("ocr_image_tags", []) or [])
        ],
        ocr_image_paths=[
            str(path) for path in list(entry.get("ocr_image_paths", []) or [])
        ],
    )
    existing.append(record)
    _save(existing)
    return record


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
    payload = {
        "tl_history": [
            {
                "id": e.id,
                "from": e.from_lang,
                "to": e.to_lang,
                "query": e.query,
                "result": e.result,
                "engine": e.engine,
                "ocr_run_id": e.ocr_run_id,
                "ocr_image_tags": list(e.ocr_image_tags or []),
                "ocr_image_paths": list(e.ocr_image_paths or []),
            }
            for e in entries
        ]
    }
    _HISTORY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")

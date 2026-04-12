"""Manifest storage for saved OCR-related images."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image
from platformdirs import user_data_dir

logger = logging.getLogger(__name__)

OCR_IMAGE_MANIFEST_PATH = (
    Path(user_data_dir("screen-translate", "Dadangdut33")) / "ocr_images.json"
)


@dataclass(slots=True)
class OCRImageRecord:
    """Single saved OCR image artifact."""

    id: str
    run_id: str
    created_at: str
    tag: str
    path: str
    source: str
    history_id: int | None = None


def new_ocr_run_id() -> str:
    """Return a stable ID for one OCR pipeline run."""
    return uuid.uuid4().hex


def manifest_path() -> Path:
    """Return the OCR image manifest path."""
    return OCR_IMAGE_MANIFEST_PATH


def load_ocr_image_manifest() -> list[OCRImageRecord]:
    """Load OCR image records from disk."""
    try:
        data = json.loads(manifest_path().read_text("utf-8"))
    except FileNotFoundError:
        return []
    except Exception as exc:
        logger.exception("Could not read OCR image manifest: %s", exc)
        return []

    records: list[OCRImageRecord] = []
    for item in data.get("ocr_images", []):
        if not isinstance(item, dict):
            continue
        try:
            records.append(
                OCRImageRecord(
                    id=str(item.get("id", "")),
                    run_id=str(item.get("run_id", "")),
                    created_at=str(item.get("created_at", "")),
                    tag=str(item.get("tag", "")),
                    path=str(item.get("path", "")),
                    source=str(item.get("source", "")),
                    history_id=(
                        int(item["history_id"])
                        if item.get("history_id") is not None
                        else None
                    ),
                )
            )
        except Exception:
            continue
    return records


def save_ocr_image_manifest(records: list[OCRImageRecord]) -> None:
    """Persist OCR image records to disk."""
    path = manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ocr_images": [asdict(record) for record in records]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")


def append_ocr_image_record(
    *,
    run_id: str,
    tag: str,
    path: str | Path,
    source: str,
    history_id: int | None = None,
    created_at: str | None = None,
) -> OCRImageRecord:
    """Append a saved OCR image record to the manifest."""
    records = load_ocr_image_manifest()
    existing_run_record = next(
        (record for record in records if record.run_id == run_id),
        None,
    )
    record = OCRImageRecord(
        id=uuid.uuid4().hex,
        run_id=run_id,
        created_at=created_at
        or (
            existing_run_record.created_at
            if existing_run_record is not None
            else datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        ),
        tag=tag,
        path=str(Path(path)),
        source=source,
        history_id=history_id,
    )
    records.append(record)
    save_ocr_image_manifest(records)
    return record


def save_ocr_image(
    image: Image.Image,
    *,
    output_path: str | Path,
    run_id: str,
    tag: str,
    source: str,
    history_id: int | None = None,
) -> OCRImageRecord:
    """Save an image and register it in the OCR image manifest."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return append_ocr_image_record(
        run_id=run_id,
        tag=tag,
        path=path,
        source=source,
        history_id=history_id,
    )


def list_ocr_images_for_run(run_id: str) -> list[OCRImageRecord]:
    """Return all OCR images associated with one run."""
    return [record for record in load_ocr_image_manifest() if record.run_id == run_id]


def link_history_to_ocr_run(run_id: str, history_id: int) -> None:
    """Attach a saved history entry ID to all manifest records from one OCR run."""
    records = load_ocr_image_manifest()
    changed = False
    for record in records:
        if record.run_id == run_id and record.history_id != history_id:
            record.history_id = history_id
            changed = True
    if changed:
        save_ocr_image_manifest(records)


def list_captured_orphans(captured_directory: Path) -> list[dict[str, Any]]:
    """Return image files in captured/ that are not registered in the manifest."""
    known_paths = {Path(record.path).resolve() for record in load_ocr_image_manifest()}
    orphaned: list[dict[str, Any]] = []
    if not captured_directory.exists():
        return orphaned

    for path in sorted(captured_directory.glob("*.png")):
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        if resolved in known_paths:
            continue
        try:
            created_at = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
        except OSError:
            created_at = datetime.now().astimezone()
        orphaned.append(
            {
                "id": f"orphan:{path.name}",
                "run_id": "",
                "created_at": created_at.isoformat(timespec="seconds"),
                "tag": "imported",
                "path": str(path),
                "source": "filesystem",
                "history_id": None,
            }
        )
    return orphaned


def delete_ocr_image_records(
    record_ids: set[str],
    *,
    delete_files: bool = True,
) -> int:
    """Delete manifest records by ID, optionally deleting the underlying files."""
    if not record_ids:
        return 0

    records = load_ocr_image_manifest()
    kept: list[OCRImageRecord] = []
    removed = 0
    for record in records:
        if record.id not in record_ids:
            kept.append(record)
            continue
        removed += 1
        if delete_files:
            try:
                Path(record.path).unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("Could not delete OCR image file %s: %s", record.path, exc)

    if removed:
        save_ocr_image_manifest(kept)
    return removed


def clear_all_captured_images(captured_directory: Path | None = None) -> tuple[int, int]:
    """Delete all captured PNG files and clear the OCR image manifest."""
    directory = captured_directory or (
        Path(user_data_dir("screen-translate", "Dadangdut33")) / "captured"
    )
    removed_files = 0
    if directory.exists():
        for path in directory.glob("*.png"):
            try:
                path.unlink()
                removed_files += 1
            except Exception as exc:
                logger.warning("Could not delete captured image %s: %s", path, exc)

    removed_records = len(load_ocr_image_manifest())
    save_ocr_image_manifest([])
    return removed_records, removed_files


def delete_unavailable_ocr_records(*, delete_files: bool = True) -> int:
    """Delete manifest records whose file is missing or cannot be previewed."""
    records = load_ocr_image_manifest()
    stale_ids: set[str] = set()
    for record in records:
        path = Path(record.path)
        if not path.exists():
            stale_ids.add(record.id)
            continue
        try:
            with Image.open(path) as image:
                image.verify()
        except Exception:
            stale_ids.add(record.id)
    return delete_ocr_image_records(stale_ids, delete_files=delete_files)

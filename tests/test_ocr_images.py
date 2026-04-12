"""Tests for OCR image manifest and history linkage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture()
def tmp_ocr_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[Path, Path]:
    """Redirect OCR image/history storage to temporary files."""
    from screen_translate.core import history as history_mod
    from screen_translate.core import ocr_images as ocr_images_mod

    history_path = tmp_path / "history.json"
    manifest_path = tmp_path / "ocr_images.json"
    monkeypatch.setattr(history_mod, "_HISTORY_PATH", history_path)
    monkeypatch.setattr(ocr_images_mod, "OCR_IMAGE_MANIFEST_PATH", manifest_path)
    return history_path, manifest_path


def test_history_roundtrip_keeps_ocr_image_fields(
    tmp_ocr_storage: tuple[Path, Path],
) -> None:
    """New history fields should survive save/load round-trips."""
    from screen_translate.core.history import append_history, load_history

    entry = append_history(
        {
            "from": "ja",
            "to": "en",
            "query": "source",
            "result": "result",
            "engine": "translators-google",
            "ocr_run_id": "run-123",
            "ocr_image_tags": ["snip_cropped", "cv2_contour"],
            "ocr_image_paths": ["/tmp/a.png", "/tmp/b.png"],
        }
    )
    assert entry.id == 0

    loaded = load_history()
    assert loaded[0].ocr_run_id == "run-123"
    assert loaded[0].ocr_image_tags == ["snip_cropped", "cv2_contour"]
    assert loaded[0].ocr_image_paths == ["/tmp/a.png", "/tmp/b.png"]


def test_manifest_run_linking_and_orphan_scan(
    tmp_ocr_storage: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """Saved OCR images should share run IDs, link to history, and leave orphans detectable."""
    from screen_translate.core.ocr_images import (
        link_history_to_ocr_run,
        list_captured_orphans,
        list_ocr_images_for_run,
        new_ocr_run_id,
        save_ocr_image,
    )

    run_id = new_ocr_run_id()
    captured = tmp_path / "captured"
    captured.mkdir()
    image = Image.new("RGB", (20, 20), color="red")

    save_ocr_image(
        image,
        output_path=captured / "one.png",
        run_id=run_id,
        tag="capture_cropped",
        source="capture-window",
    )
    save_ocr_image(
        image,
        output_path=captured / "two.png",
        run_id=run_id,
        tag="cv2_contour",
        source="tesseract",
    )

    run_records = list_ocr_images_for_run(run_id)
    assert len(run_records) == 2
    assert {record.tag for record in run_records} == {"capture_cropped", "cv2_contour"}

    link_history_to_ocr_run(run_id, 7)
    relinked = list_ocr_images_for_run(run_id)
    assert all(record.history_id == 7 for record in relinked)

    orphan_path = captured / "legacy.png"
    image.save(orphan_path)
    orphans = list_captured_orphans(captured)
    assert len(orphans) == 1
    assert orphans[0]["path"] == str(orphan_path)
    assert orphans[0]["tag"] == "imported"


def test_delete_helpers_remove_records_and_files(
    tmp_ocr_storage: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """Delete helpers should remove stale records and clear captured images."""
    from screen_translate.core.ocr_images import (
        clear_all_captured_images,
        delete_ocr_image_records,
        delete_unavailable_ocr_records,
        load_ocr_image_manifest,
        new_ocr_run_id,
        save_ocr_image,
    )

    run_id = new_ocr_run_id()
    captured = tmp_path / "captured"
    captured.mkdir()
    image = Image.new("RGB", (12, 12), color="blue")

    record = save_ocr_image(
        image,
        output_path=captured / "keep.png",
        run_id=run_id,
        tag="ocr_input",
        source="ocr",
    )
    removed = delete_ocr_image_records({record.id}, delete_files=True)
    assert removed == 1
    assert not Path(record.path).exists()
    assert load_ocr_image_manifest() == []

    stale = save_ocr_image(
        image,
        output_path=captured / "stale.png",
        run_id=new_ocr_run_id(),
        tag="capture_cropped",
        source="capture-window",
    )
    Path(stale.path).unlink()
    pruned = delete_unavailable_ocr_records(delete_files=True)
    assert pruned == 1
    assert load_ocr_image_manifest() == []

    save_ocr_image(
        image,
        output_path=captured / "a.png",
        run_id=new_ocr_run_id(),
        tag="capture_cropped",
        source="capture-window",
    )
    image.save(captured / "orphan.png")
    removed_records, removed_files = clear_all_captured_images(captured)
    assert removed_records == 1
    assert removed_files == 2
    assert load_ocr_image_manifest() == []

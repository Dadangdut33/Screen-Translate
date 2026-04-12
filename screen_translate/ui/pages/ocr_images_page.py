"""Embedded gallery page for saved OCR images."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    DropDownPushButton,
    LineEdit,
    MessageBox,
    PushButton,
    RoundMenu,
    TitleLabel,
)

from qfluentwidgets.components.layout.flow_layout import AdaptiveFlowLayout

from screen_translate.core.ocr_images import (
    clear_all_captured_images,
    delete_ocr_image_records,
    delete_unavailable_ocr_records,
    list_captured_orphans,
    load_ocr_image_manifest,
)
from screen_translate.ui.screen_capture import captured_dir
from screen_translate.ui.theme.style_sheet import StyleSheet


def _parse_created_at(value: str) -> datetime:
    """Parse stored timestamps defensively."""
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.now().astimezone()


def _display_timestamp(value: str) -> str:
    """Return a compact local timestamp string."""
    return _parse_created_at(value).strftime("%Y-%m-%d %H:%M")


class _ImageCard(QFrame):
    """Small gallery card for one saved OCR image."""

    def __init__(
        self,
        item: dict[str, Any],
        *,
        delete_callback: Callable[[dict[str, Any]], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.item = item
        self._delete_callback = delete_callback
        self.setObjectName("OCRImageCard")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.setMinimumHeight(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        preview = QLabel(self)
        preview.setObjectName("OCRImagePreview")
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setMinimumHeight(140)
        preview.setMaximumHeight(140)
        pixmap = QPixmap(str(item["path"]))
        if not pixmap.isNull():
            preview.setPixmap(
                pixmap.scaled(
                    260,
                    140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            preview.setText("Preview unavailable")
        layout.addWidget(preview)

        tag = BodyLabel(f"Tag: {item['tag']}", self)
        tag.setObjectName("OCRImageTag")
        layout.addWidget(tag)

        layout.addWidget(BodyLabel(_display_timestamp(str(item["created_at"])), self))
        layout.addWidget(BodyLabel(Path(str(item["path"])).name, self))

        source = str(item.get("source", "")).strip()
        if source:
            layout.addWidget(BodyLabel(f"Source: {source}", self))

        history_id = item.get("history_id")
        if history_id is not None:
            layout.addWidget(BodyLabel(f"History ID: {history_id}", self))

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)
        btn_open = PushButton("Open", self)
        btn_open.clicked.connect(self._open_image)
        buttons.addWidget(btn_open)
        btn_folder = PushButton("Open Folder", self)
        btn_folder.clicked.connect(self._open_folder)
        buttons.addWidget(btn_folder)
        btn_delete = PushButton("Delete", self)
        btn_delete.clicked.connect(self._delete_image)
        buttons.addWidget(btn_delete)
        buttons.addStretch(1)
        layout.addLayout(buttons)

    def _open_image(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.item["path"])))

    def _open_folder(self) -> None:
        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(Path(self.item["path"]).parent))
        )

    def mousePressEvent(self, event: object) -> None:  # type: ignore[override]
        self._open_image()
        super().mousePressEvent(event)  # type: ignore[arg-type]

    def _delete_image(self) -> None:
        if self._delete_callback is not None:
            self._delete_callback(self.item)


class OCRImagesPage(QWidget):
    """Gallery page for saved OCR images and capture artifacts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("OCRImagesPage")
        StyleSheet.AUXILIARY_WINDOW.apply(self)
        self._focused_paths: set[str] = set()
        self._focused_run_id: str = ""
        self._build_ui()
        self.refresh_gallery()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        header_card = QFrame(self)
        header_card.setObjectName("PageHeaderCard")
        header_card_layout = QVBoxLayout(header_card)
        header_card_layout.setContentsMargins(16, 16, 16, 16)
        header_card_layout.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(TitleLabel("OCR Images", self))
        title_row.addStretch(1)
        header_card_layout.addLayout(title_row)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        self._group_by = ComboBox()
        self._group_by.addItem("By Tag", userData="tag")
        self._group_by.addItem("By Date", userData="date")
        self._group_by.currentIndexChanged.connect(self.refresh_gallery)
        header.addWidget(self._group_by)

        self._scope = ComboBox()
        self._scope.addItem("OCR-related only", userData="ocr_only")
        self._scope.addItem("All saved captures", userData="all")
        self._scope.currentIndexChanged.connect(self._on_filter_changed)
        header.addWidget(self._scope)

        self._search = LineEdit(self)
        self._search.setPlaceholderText("Search tag, file name, source...")
        self._search.textChanged.connect(self._on_search_changed)
        self._search.setMinimumWidth(220)
        header.addWidget(self._search)

        btn_refresh = PushButton("Refresh", self)
        btn_refresh.clicked.connect(self.refresh_gallery)
        header.addWidget(btn_refresh)

        self._btn_utils = DropDownPushButton("Utilities", self)
        self._utils_menu = self._build_utils_menu()
        self._btn_utils.setMenu(self._utils_menu)
        header.addWidget(self._btn_utils)

        header_card_layout.addLayout(header)
        layout.addWidget(header_card)

        self._content = QWidget(self)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(18)
        layout.addWidget(self._content)

    def _build_utils_menu(self) -> RoundMenu:
        """Build the gallery utilities menu."""
        menu = RoundMenu(parent=self)
        action_clear = QAction("Clear all images", menu)
        action_clear.triggered.connect(self._clear_all_images)
        menu.addAction(action_clear)

        action_prune = QAction(
            "Delete dangling records (unavailable preview)",
            menu,
        )
        action_prune.triggered.connect(self._delete_unavailable_records)
        menu.addAction(action_prune)
        return menu

    def _on_filter_changed(self) -> None:
        """Refresh after grouping/scope changes."""
        self.refresh_gallery()

    def _on_search_changed(self, _: str) -> None:
        """Clear exact-path focus when the user types manually."""
        self._focused_paths = set()
        self._focused_run_id = ""
        self.refresh_gallery()

    def _clear_content(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                while child_layout.count():
                    inner = child_layout.takeAt(0)
                    if inner.widget() is not None:
                        inner.widget().deleteLater()

    def _manifest_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": record.id,
                "run_id": record.run_id,
                "created_at": record.created_at,
                "tag": record.tag,
                "path": record.path,
                "source": record.source,
                "history_id": record.history_id,
            }
            for record in load_ocr_image_manifest()
        ]

    def _all_items(self) -> list[dict[str, Any]]:
        items = self._manifest_items()
        if self._scope.currentData() == "all":
            items.extend(list_captured_orphans(captured_dir()))

        if self._focused_paths:
            items = [
                item
                for item in items
                if str(item.get("path", "")) in self._focused_paths
            ]
        elif self._focused_run_id:
            items = [
                item
                for item in items
                if str(item.get("run_id", "")) == self._focused_run_id
            ]

        query = self._search.text().strip().lower()
        if not query:
            return items

        filtered: list[dict[str, Any]] = []
        for item in items:
            haystack = " ".join(
                [
                    str(item.get("tag", "")),
                    str(item.get("path", "")),
                    str(item.get("source", "")),
                    str(item.get("history_id", "")),
                    str(item.get("run_id", "")),
                    _display_timestamp(str(item.get("created_at", ""))),
                ]
            ).lower()
            if query in haystack:
                filtered.append(item)
        return filtered

    def refresh_gallery(self) -> None:
        """Rebuild the gallery using current grouping and scope selections."""
        self._clear_content()
        items = sorted(
            self._all_items(),
            key=lambda item: _parse_created_at(str(item["created_at"])),
            reverse=True,
        )

        if not items:
            self._content_layout.addWidget(
                BodyLabel("No saved OCR images found.", self)
            )
            self._content_layout.addStretch(1)
            return

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if self._group_by.currentData() == "date":
            for item in items:
                key = _parse_created_at(str(item["created_at"])).strftime("%Y-%m-%d")
                grouped[key].append(item)
        else:
            for item in items:
                grouped[str(item.get("tag", "untagged"))].append(item)

        for section_name, section_items in grouped.items():
            section = QWidget(self._content)
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(0, 0, 0, 0)
            section_layout.setSpacing(10)
            section_layout.addWidget(TitleLabel(section_name, section))

            flow_host = QWidget(section)
            flow = AdaptiveFlowLayout(flow_host)
            flow.setContentsMargins(0, 0, 0, 0)
            flow.setHorizontalSpacing(12)
            flow.setVerticalSpacing(12)
            flow.setWidgetMinimumWidth(220)
            flow.setWidgetMaximumWidth(280)
            for item in section_items:
                flow.addWidget(
                    _ImageCard(
                        item,
                        delete_callback=self._confirm_delete_image,
                        parent=flow_host,
                    )
                )
            section_layout.addWidget(flow_host)
            self._content_layout.addWidget(section)

        self._content_layout.addStretch(1)

    def show_image_paths(self, paths: list[str]) -> None:
        """Focus the gallery on specific saved image paths."""
        normalized = [str(Path(path)) for path in paths if str(path).strip()]
        self._focused_paths = set(normalized)
        self._focused_run_id = ""
        first_label = Path(normalized[0]).name if normalized else ""
        self._search.blockSignals(True)
        self._search.setText(first_label)
        self._search.blockSignals(False)
        self.refresh_gallery()

    def show_run(self, run_id: str) -> None:
        """Focus the gallery on one OCR run."""
        normalized_run_id = run_id.strip()
        self._focused_run_id = normalized_run_id
        self._focused_paths = set()
        items = [
            item
            for item in self._manifest_items()
            if item["run_id"] == normalized_run_id
        ]
        search_text = _display_timestamp(str(items[0]["created_at"])) if items else ""
        self._search.blockSignals(True)
        self._search.setText(search_text)
        self._search.blockSignals(False)
        self.refresh_gallery()

    def _confirm_delete_image(self, item: dict[str, Any]) -> None:
        """Confirm and delete one OCR image record."""
        box = MessageBox(
            "Delete OCR Image",
            f"Delete this OCR image?\n\n{Path(str(item['path'])).name}",
            self.window(),
        )
        box.yesButton.setText("Delete")
        box.cancelButton.setText("Cancel")
        if not box.exec():
            return
        record_id = str(item.get("id", "")).strip()
        if record_id and not record_id.startswith("orphan:"):
            delete_ocr_image_records({record_id}, delete_files=True)
        else:
            try:
                Path(str(item["path"])).unlink(missing_ok=True)
            except Exception:
                pass
        self._focused_paths.discard(str(item.get("path", "")))
        self.refresh_gallery()

    def _clear_all_images(self) -> None:
        """Confirm and clear all saved image files and manifest records."""
        box = MessageBox(
            "Clear All Images",
            "Delete all saved OCR/capture images and clear their records?",
            self.window(),
        )
        box.yesButton.setText("Delete All")
        box.cancelButton.setText("Cancel")
        if not box.exec():
            return
        clear_all_captured_images(captured_dir())
        self._focused_paths = set()
        self._focused_run_id = ""
        self._search.clear()
        self.refresh_gallery()

    def _delete_unavailable_records(self) -> None:
        """Confirm and prune manifest records with missing or invalid image files."""
        box = MessageBox(
            "Delete Unavailable Records",
            "Delete all OCR image records whose image is missing or cannot be previewed?",
            self.window(),
        )
        box.yesButton.setText("Delete Records")
        box.cancelButton.setText("Cancel")
        if not box.exec():
            return
        delete_unavailable_ocr_records(delete_files=True)
        self.refresh_gallery()

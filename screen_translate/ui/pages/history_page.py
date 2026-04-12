"""Translation history window."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import LineEdit, MessageBox, PushButton, TableWidget

from screen_translate.core.history import (
    HistoryEntry,
    clear_history,
    delete_history_by_ids,
    load_history,
)
from screen_translate.ui.theme.style_sheet import StyleSheet

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)

_COL_ID = 0
_COL_FROM = 1
_COL_TO = 2
_COL_ENGINE = 3
_COL_OCR_TAGS = 4
_COL_QUERY = 5
_COL_RESULT = 6


class HistoryPage(QWidget):
    """Embedded translation history page."""

    def __init__(self, controller: AppController) -> None:
        """Create the history page.

        Args:
            controller: Application controller.
        """
        super().__init__()
        self.controller = controller
        self.setObjectName("HistoryPage")
        StyleSheet.AUXILIARY_WINDOW.apply(self)
        self._build_ui()
        self._load()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        vl = QVBoxLayout(self)

        # Search bar
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Search:"))
        self._search = LineEdit()
        self._search.setPlaceholderText("Type to filter…")
        self._search.textChanged.connect(self._filter)
        hl.addWidget(self._search)

        self._btn_refresh = PushButton("Refresh")
        self._btn_refresh.clicked.connect(self._load)
        hl.addWidget(self._btn_refresh)

        self._btn_delete = PushButton("Delete Selected")
        self._btn_delete.clicked.connect(self._delete_selected)
        self._btn_delete.setEnabled(False)
        hl.addWidget(self._btn_delete)

        self._btn_open_images = PushButton("Open OCR Images")
        self._btn_open_images.clicked.connect(self._open_selected_images)
        self._btn_open_images.setEnabled(False)
        hl.addWidget(self._btn_open_images)

        self._btn_clear = PushButton("Clear All")
        self._btn_clear.clicked.connect(self._clear_all)
        self._btn_clear.setEnabled(False)
        hl.addWidget(self._btn_clear)

        vl.addLayout(hl)

        # Table
        self._table = TableWidget()
        self._table.setRowCount(0)
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["ID", "From", "To", "Engine", "OCR Tags", "Query", "Result"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.itemSelectionChanged.connect(self._update_action_state)
        vl.addWidget(self._table)

    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Reload history from disk and repopulate the table."""
        entries = load_history()
        self._populate(entries)
        self._update_action_state()

    def _populate(self, entries: list[HistoryEntry]) -> None:
        self._table.setRowCount(0)
        for entry in entries:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, val in enumerate(
                [
                    str(entry.id),
                    entry.from_lang,
                    entry.to_lang,
                    entry.engine,
                    ", ".join(entry.ocr_image_tags or []),
                    entry.query,
                    entry.result,
                ]
            ):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, entry.id)
                if col == _COL_OCR_TAGS:
                    item.setData(
                        Qt.ItemDataRole.UserRole + 1,
                        list(entry.ocr_image_paths or []),
                    )
                    item.setData(
                        Qt.ItemDataRole.UserRole + 2,
                        str(entry.ocr_run_id or ""),
                    )
                self._table.setItem(row, col, item)
        self._update_action_state()

    def _has_history_rows(self) -> bool:
        """Return True when the table currently contains history entries."""
        return self._table.rowCount() > 0

    def _selected_history_ids(self) -> set[int]:
        """Return ids for the currently selected table rows."""
        selected_rows = {idx.row() for idx in self._table.selectedIndexes()}
        ids: set[int] = set()
        for row in selected_rows:
            item = self._table.item(row, _COL_ID)
            if item:
                ids.add(int(item.text()))
        return ids

    def _selected_image_paths(self) -> list[str]:
        """Return OCR image paths associated with the selected rows."""
        selected_rows = {idx.row() for idx in self._table.selectedIndexes()}
        paths: list[str] = []
        for row in selected_rows:
            item = self._table.item(row, _COL_OCR_TAGS)
            if item is None:
                continue
            raw_paths = item.data(Qt.ItemDataRole.UserRole + 1)
            if isinstance(raw_paths, list):
                paths.extend(str(path) for path in raw_paths if str(path).strip())
        return paths

    def _selected_run_id(self) -> str:
        """Return the OCR run ID for the current selection, if any."""
        selected_rows = {idx.row() for idx in self._table.selectedIndexes()}
        for row in selected_rows:
            item = self._table.item(row, _COL_OCR_TAGS)
            if item is None:
                continue
            run_id = item.data(Qt.ItemDataRole.UserRole + 2)
            if isinstance(run_id, str) and run_id.strip():
                return run_id
        return ""

    @pyqtSlot()
    def _update_action_state(self) -> None:
        """Enable destructive actions only when they are valid."""
        has_history = self._has_history_rows()
        has_selection = bool(self._selected_history_ids())
        has_images = bool(self._selected_image_paths())
        self._btn_clear.setEnabled(has_history)
        self._btn_delete.setEnabled(has_history and has_selection)
        self._btn_open_images.setEnabled(has_history and has_selection and has_images)

    @pyqtSlot(str)
    def _filter(self, text: str) -> None:
        """Show only rows containing *text* in OCR tags, query, or result columns."""
        text_lower = text.lower()
        for row in range(self._table.rowCount()):
            tags_item = self._table.item(row, _COL_OCR_TAGS)
            query_item = self._table.item(row, _COL_QUERY)
            result_item = self._table.item(row, _COL_RESULT)
            match = (
                (tags_item and text_lower in tags_item.text().lower())
                or
                (query_item and text_lower in query_item.text().lower())
                or (result_item and text_lower in result_item.text().lower())
                or not text_lower
            )
            self._table.setRowHidden(row, not match)

    @pyqtSlot()
    def _delete_selected(self) -> None:
        """Delete selected rows from history."""
        ids = self._selected_history_ids()
        if not ids:
            return
        box = MessageBox(
            "Delete Selected History",
            f"Delete {len(ids)} selected history entr{'y' if len(ids) == 1 else 'ies'}?",
            self.window(),
        )
        box.yesButton.setText("Delete")
        box.cancelButton.setText("Cancel")
        if not box.exec():
            return
        delete_history_by_ids(ids)
        self._load()

    @pyqtSlot()
    def _clear_all(self) -> None:
        """Clear all history after confirmation."""
        box = MessageBox(
            "Clear History",
            "Delete all translation history?",
            self.window(),
        )
        box.yesButton.setText("Delete")
        box.cancelButton.setText("Cancel")
        if box.exec():
            clear_history()
            self._load()

    @pyqtSlot()
    def _open_selected_images(self) -> None:
        """Route to the OCR Images page and focus the selected OCR artifacts."""
        run_id = self._selected_run_id()
        paths = self._selected_image_paths()
        if not run_id and not paths:
            return
        if self.controller.ocr_images_page is not None:
            if run_id:
                self.controller.ocr_images_page.show_run(run_id)
            else:
                self.controller.ocr_images_page.show_image_paths(paths)
        if self.controller.main_window is not None:
            self.controller.main_window._open_ocr_images()


HistoryWindow = HistoryPage

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
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from screen_translate.core.history import (
    HistoryEntry,
    clear_history,
    delete_history_by_ids,
    load_history,
)

if TYPE_CHECKING:
    from screen_translate.ui.controller import AppController

logger = logging.getLogger(__name__)

_COL_ID = 0
_COL_FROM = 1
_COL_TO = 2
_COL_ENGINE = 3
_COL_QUERY = 4
_COL_RESULT = 5


class HistoryWindow(QMainWindow):
    """Displays the translation history in a searchable table."""

    def __init__(self, controller: AppController) -> None:
        """Create the history window.

        Args:
            controller: Application controller.
        """
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Translation History")
        self.resize(900, 500)
        self._build_ui()
        self._load()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        vl = QVBoxLayout(central)

        # Search bar
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Search:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Type to filter…")
        self._search.textChanged.connect(self._filter)
        hl.addWidget(self._search)

        self._btn_refresh = QPushButton("Refresh")
        self._btn_refresh.clicked.connect(self._load)
        hl.addWidget(self._btn_refresh)

        self._btn_delete = QPushButton("Delete Selected")
        self._btn_delete.clicked.connect(self._delete_selected)
        hl.addWidget(self._btn_delete)

        self._btn_clear = QPushButton("Clear All")
        self._btn_clear.clicked.connect(self._clear_all)
        hl.addWidget(self._btn_clear)

        vl.addLayout(hl)

        # Table
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["ID", "From", "To", "Engine", "Query", "Result"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        vl.addWidget(self._table)

    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Reload history from disk and repopulate the table."""
        entries = load_history()
        self._populate(entries)

    def _populate(self, entries: list[HistoryEntry]) -> None:
        self._table.setRowCount(0)
        for entry in entries:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, val in enumerate([
                str(entry.id),
                entry.from_lang,
                entry.to_lang,
                entry.engine,
                entry.query,
                entry.result,
            ]):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, entry.id)
                self._table.setItem(row, col, item)

    @pyqtSlot(str)
    def _filter(self, text: str) -> None:
        """Show only rows containing *text* in query or result columns."""
        text_lower = text.lower()
        for row in range(self._table.rowCount()):
            query_item = self._table.item(row, _COL_QUERY)
            result_item = self._table.item(row, _COL_RESULT)
            match = (
                (query_item and text_lower in query_item.text().lower())
                or (result_item and text_lower in result_item.text().lower())
                or not text_lower
            )
            self._table.setRowHidden(row, not match)

    @pyqtSlot()
    def _delete_selected(self) -> None:
        """Delete selected rows from history."""
        selected_rows = {idx.row() for idx in self._table.selectedIndexes()}
        ids: set[int] = set()
        for row in selected_rows:
            item = self._table.item(row, _COL_ID)
            if item:
                ids.add(int(item.text()))
        if not ids:
            return
        delete_history_by_ids(ids)
        self._load()

    @pyqtSlot()
    def _clear_all(self) -> None:
        """Clear all history after confirmation."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Delete all translation history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_history()
            self._load()

    def show_and_raise(self) -> None:
        """Show and bring to front."""
        self._load()
        self.show()
        self.raise_()
        self.activateWindow()

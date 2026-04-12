"""Reusable editable combo box with commit-only selection behavior."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFocusEvent
from PyQt6.QtWidgets import QCompleter, QWidget
from qfluentwidgets import EditableComboBox


class SuggestionComboBox(EditableComboBox):
    """Editable combo box that allows search/completion but never adds new items."""

    committed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._last_valid_index = -1
        self._last_committed_index = -1
        self._editing = False
        self.activated.connect(self._on_item_activated)
        self.editingFinished.connect(self._on_editing_finished)

    def _onReturnPressed(self) -> None:  # type: ignore[override]
        text = self.text().strip()
        if not text:
            self._restore_current_value()
            return
        index = self.findText(text)
        if index >= 0 and index != self.currentIndex():
            self.setCurrentIndex(index)
        elif index < 0:
            matched_index = self._single_completion_index(text)
            if matched_index >= 0:
                self.setCurrentIndex(matched_index)
            else:
                self._restore_current_value()
        self._editing = False
        self._emit_commit_if_needed()

    def refresh_completer(self) -> None:
        """Rebuild the completer from the current visible items."""
        completer = QCompleter(
            [self.itemText(i) for i in range(self.count()) if self.itemText(i).strip()],
            self,
        )
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setMaxVisibleItems(10)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(completer)

    def focusInEvent(self, event: QFocusEvent) -> None:  # type: ignore[override]
        self._editing = True
        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:  # type: ignore[override]
        if self._is_completer_popup_open() or (
            event.reason() == Qt.FocusReason.PopupFocusReason
        ):
            super().focusOutEvent(event)
            return
        self._editing = False
        self._finalize_text()
        super().focusOutEvent(event)

    def _single_completion_index(self, text: str) -> int:
        """Return the only matching completion index, or -1 if ambiguous/none."""
        completer = self.completer()
        if completer is None:
            return -1
        completer.setCompletionPrefix(text)
        model = completer.completionModel()
        if model.rowCount() != 1:
            return -1
        match_text = str(model.index(0, 0).data() or "").strip()
        return self.findText(match_text)

    def _restore_current_value(self) -> None:
        """Restore the currently selected valid item text."""
        index = self._last_valid_index
        if index >= 0:
            self.setCurrentIndex(index)
        else:
            self.clear()

    def setCurrentIndex(self, index: int) -> None:  # type: ignore[override]
        super().setCurrentIndex(index)
        if index >= 0:
            self._last_valid_index = index

    def _emit_commit_if_needed(self) -> None:
        """Emit a commit signal only when the committed selection actually changed."""
        index = self.currentIndex()
        if index >= 0 and index != self._last_committed_index:
            self._last_committed_index = index
            self.committed.emit(index)

    def _finalize_text(self) -> None:
        """Validate the current editor text and commit only a valid selection."""
        text = self.text().strip()
        if text:
            exact_index = self.findText(text)
            if exact_index >= 0:
                self.setCurrentIndex(exact_index)
            else:
                matched_index = self._single_completion_index(text)
                if matched_index >= 0:
                    self.setCurrentIndex(matched_index)
                else:
                    self._restore_current_value()
        else:
            if not self._editing:
                self._restore_current_value()
        self._emit_commit_if_needed()

    def _is_completer_popup_open(self) -> bool:
        """Return whether the completer popup is currently visible."""
        completer = self.completer()
        if completer is None:
            return False
        popup = completer.popup()
        return bool(popup is not None and popup.isVisible())

    @pyqtSlot()
    def _on_editing_finished(self) -> None:
        """Commit the edited text only after real editing is complete."""
        if self._is_completer_popup_open() or self._editing:
            return
        self._finalize_text()

    @pyqtSlot(int)
    def _on_item_activated(self, index: int) -> None:
        """Commit a selection chosen from the popup list."""
        if index < 0:
            return
        self._last_valid_index = index
        self._emit_commit_if_needed()

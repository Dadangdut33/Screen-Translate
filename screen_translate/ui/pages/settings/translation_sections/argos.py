"""Argos Translate settings section and helpers."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QProcess, QUrl, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    PushButton,
    TableWidget,
)

from screen_translate.core.translation.argos_backend import (
    argos_package_dir_size,
    configure_argos_package_dir,
)
from screen_translate.ui.widgets import InfoBannerCard

from .shared import (
    argos_install_dir,
    confirm_directory_move,
    directory_has_content,
    format_bytes,
    move_directory_contents,
    paths_equivalent,
    refresh_translation_runtime,
)

logger = logging.getLogger(__name__)


def collect_argos_info(dialog: Any) -> dict[str, object]:
    """Collect Argos Translate informational data off the UI thread."""
    import argostranslate.settings as argos_settings
    import argostranslate.translate as argos_translate

    argos_translate.get_installed_languages.cache_clear()
    installed_languages = argos_translate.get_installed_languages()
    installed_count = len(installed_languages)
    configured_dir = configure_argos_package_dir(
        str(dialog.s.get("argos_package_dir", ""))
    )
    package_dir = str(getattr(argos_settings, "package_data_dir", configured_dir))
    size_bytes = argos_package_dir_size(str(dialog.s.get("argos_package_dir", "")))

    installed_pairs: set[tuple[str, str]] = set()
    for source in installed_languages:
        src_code = str(getattr(source, "code", "")).strip()
        if not src_code:
            continue
        for target in installed_languages:
            tgt_code = str(getattr(target, "code", "")).strip()
            if not tgt_code or src_code == tgt_code:
                continue
            try:
                translation = source.get_translation(target)
            except Exception:
                translation = None
            if translation is not None:
                installed_pairs.add((src_code, tgt_code))

    return {
        "installed_count": installed_count,
        "configured_dir": str(configured_dir),
        "package_dir": package_dir,
        "size_bytes": size_bytes,
        "installed_pairs": installed_pairs,
    }


def apply_argos_info(dialog: Any, payload: dict[str, object]) -> None:
    """Apply Argos Translate informational data on the UI thread."""
    installed_count = int(payload.get("installed_count", 0))
    configured_dir = str(payload.get("configured_dir", ""))
    package_dir = str(payload.get("package_dir", configured_dir))
    size_bytes = int(payload.get("size_bytes", 0))
    installed_pairs = payload.get("installed_pairs", set())
    if not isinstance(installed_pairs, set):
        installed_pairs = set()

    dialog._lbl_argos_status.setText(f"Installed language packs: {installed_count}")
    dialog._lbl_argos_dir.setText(package_dir)
    if getattr(dialog, "_argos_dir_edit", None) is not None:
        dialog._argos_dir_edit.blockSignals(True)
        dialog._argos_dir_edit.setText(configured_dir)
        dialog._argos_dir_edit.blockSignals(False)
    if getattr(dialog, "_lbl_argos_installed_codes", None) is not None:
        dialog._lbl_argos_installed_codes.setText(
            format_bytes(size_bytes) if installed_count or size_bytes else "0 B"
        )
    dialog._argos_installed_pairs = installed_pairs
    refresh_argos_table_install_state(dialog)


def collect_argos_package_index(dialog: Any) -> dict[str, object]:
    """Collect Argos package-index data off the UI thread."""
    configure_argos_package_dir(str(dialog.s.get("argos_package_dir", "")))
    import argostranslate.package as argos_package

    argos_package.update_package_index()
    available_packages = argos_package.get_available_packages()
    return {
        "available_packages": available_packages,
        "count": len(available_packages),
    }


def apply_argos_package_index(dialog: Any, payload: dict[str, object]) -> None:
    """Apply Argos package-index data on the UI thread."""
    available_packages = payload.get("available_packages", [])
    if not isinstance(available_packages, list):
        available_packages = []
    dialog._argos_packages = available_packages
    dialog._lbl_argos_index_status.setText(
        f"Available online pack pairs: {int(payload.get('count', len(available_packages)))}"
    )
    rebuild_argos_packages_table(dialog)


def refresh_argos_info(dialog: Any) -> None:
    """Refresh Argos Translate informational labels."""
    try:
        import argostranslate.settings as argos_settings
        import argostranslate.translate as argos_translate

        argos_translate.get_installed_languages.cache_clear()
        installed_languages = argos_translate.get_installed_languages()
        installed_count = len(installed_languages)
        configured_dir = configure_argos_package_dir(
            str(dialog.s.get("argos_package_dir", ""))
        )
        package_dir = str(getattr(argos_settings, "package_data_dir", configured_dir))
        dialog._lbl_argos_status.setText(f"Installed language packs: {installed_count}")
        dialog._lbl_argos_dir.setText(package_dir)
        if getattr(dialog, "_argos_dir_edit", None) is not None:
            dialog._argos_dir_edit.blockSignals(True)
            dialog._argos_dir_edit.setText(str(configured_dir))
            dialog._argos_dir_edit.blockSignals(False)
        if getattr(dialog, "_lbl_argos_installed_codes", None) is not None:
            size_bytes = argos_package_dir_size(
                str(dialog.s.get("argos_package_dir", ""))
            )
            dialog._lbl_argos_installed_codes.setText(
                format_bytes(size_bytes) if installed_count or size_bytes else "0 B"
            )
        refresh_argos_installed_set(dialog)
        refresh_argos_table_install_state(dialog)
    except Exception as exc:
        dialog._lbl_argos_status.setText("Argos Translate status unavailable")
        dialog._lbl_argos_dir.setText(f"Unavailable: {exc}")
        if getattr(dialog, "_lbl_argos_installed_codes", None) is not None:
            dialog._lbl_argos_installed_codes.setText("Unavailable")


def refresh_argos_installed_set(dialog: Any) -> None:
    """Cache installed Argos translation pairs for table state."""
    dialog._argos_installed_pairs = set()
    try:
        import argostranslate.translate as argos_translate

        argos_translate.get_installed_languages.cache_clear()
        installed_languages = argos_translate.get_installed_languages()
        for source in installed_languages:
            src_code = str(getattr(source, "code", "")).strip()
            if not src_code:
                continue
            for target in installed_languages:
                tgt_code = str(getattr(target, "code", "")).strip()
                if not tgt_code or src_code == tgt_code:
                    continue
                try:
                    translation = source.get_translation(target)
                except Exception:
                    translation = None
                if translation is not None:
                    dialog._argos_installed_pairs.add((src_code, tgt_code))
    except Exception:
        return


def refresh_argos_package_index(dialog: Any) -> None:
    """Refresh the Argos package index and rebuild the table."""
    try:
        configure_argos_package_dir(str(dialog.s.get("argos_package_dir", "")))
        import argostranslate.package as argos_package

        argos_package.update_package_index()
        available_packages = argos_package.get_available_packages()
        dialog._argos_packages = available_packages
        dialog._lbl_argos_index_status.setText(
            f"Available online pack pairs: {len(available_packages)}"
        )
        rebuild_argos_packages_table(dialog)
    except Exception as exc:
        logger.warning("Failed to refresh Argos package index: %s", exc)
        dialog._lbl_argos_index_status.setText(
            f"Argos package index unavailable: {exc}"
        )


def open_argos_dir(dialog: Any) -> None:
    """Open the Argos package directory in the desktop file manager."""
    try:
        import argostranslate.settings as argos_settings

        package_dir = Path(argos_settings.package_data_dir)
        package_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(package_dir)))
    except Exception as exc:
        dialog._lbl_argos_install_runtime.setText(
            f"Could not open Argos package directory: {exc}"
        )


def apply_argos_dir_change(dialog: Any, raw_value: str) -> None:
    """Persist a new Argos package directory and move existing content if needed."""
    old_dir = argos_install_dir(dialog)
    new_dir = configure_argos_package_dir(raw_value)

    if paths_equivalent(old_dir, new_dir):
        if getattr(dialog, "_argos_dir_edit", None) is not None:
            dialog._argos_dir_edit.blockSignals(True)
            dialog._argos_dir_edit.setText(str(new_dir))
            dialog._argos_dir_edit.blockSignals(False)
        dialog.s.set("argos_package_dir", str(new_dir))
        refresh_argos_info(dialog)
        return

    if directory_has_content(old_dir):
        confirmed = confirm_directory_move(
            dialog,
            title="Move Argos Packages",
            subject="Installed Argos language packages",
            source=old_dir,
            destination=new_dir,
        )
        if not confirmed:
            if getattr(dialog, "_argos_dir_edit", None) is not None:
                dialog._argos_dir_edit.blockSignals(True)
                dialog._argos_dir_edit.setText(str(old_dir))
                dialog._argos_dir_edit.blockSignals(False)
            return
        try:
            move_directory_contents(old_dir, new_dir)
        except Exception as exc:
            dialog._lbl_argos_install_runtime.setText(
                f"Could not move Argos packages: {exc}"
            )
            if getattr(dialog, "_argos_dir_edit", None) is not None:
                dialog._argos_dir_edit.blockSignals(True)
                dialog._argos_dir_edit.setText(str(old_dir))
                dialog._argos_dir_edit.blockSignals(False)
            configure_argos_package_dir(str(old_dir))
            return

    dialog.s.set("argos_package_dir", str(new_dir))
    configure_argos_package_dir(str(new_dir))
    if dialog.controller.local_libretranslate_enabled():
        dialog.controller.stop_local_libretranslate_server()
        from .libre import refresh_libre_local_info

        refresh_libre_local_info(dialog)
    refresh_argos_info(dialog)
    refresh_translation_runtime(dialog)


def browse_argos_dir(dialog: Any) -> None:
    """Choose the Argos package directory."""
    current = str(argos_install_dir(dialog))
    chosen = QFileDialog.getExistingDirectory(
        dialog, "Choose Argos package directory", current
    )
    if not chosen:
        return
    apply_argos_dir_change(dialog, chosen)


def set_argos_busy(dialog: Any, busy: bool, status_text: str = "") -> None:
    """Update the Argos install UI busy state."""
    for widget_name in (
        "_btn_argos_refresh",
        "_btn_argos_load_index",
        "_btn_argos_install_all",
        "_btn_argos_open_dir",
        "_btn_argos_browse_dir",
        "_le_argos_search",
        "_tbl_argos_packs",
    ):
        widget = getattr(dialog, widget_name, None)
        if widget is not None:
            widget.setEnabled(not busy)
    cancel_btn = getattr(dialog, "_btn_argos_cancel", None)
    if cancel_btn is not None:
        cancel_btn.setEnabled(busy)
    if status_text:
        dialog._lbl_argos_install_runtime.setText(status_text)


def set_progress(bar: QProgressBar | None, value: int, maximum: int) -> None:
    """Update a progress bar safely."""
    if bar is None:
        return
    bar.setMaximum(maximum)
    bar.setValue(value)


def handle_argos_process_output(dialog: Any) -> None:
    """Parse progress markers from the Argos install subprocess."""
    process: QProcess | None = getattr(dialog, "_argos_install_process", None)
    if process is None:
        return
    output = bytes(process.readAllStandardOutput()).decode(errors="replace")
    output += bytes(process.readAllStandardError()).decode(errors="replace")
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("STEP "):
            try:
                meta, description = stripped.split(":", 1)
                progress = meta.removeprefix("STEP ").strip()
                current_s, total_s = progress.split("/", 1)
                current = int(current_s)
                total = int(total_s)
                set_progress(getattr(dialog, "_argos_progress", None), current, total)
                dialog._lbl_argos_install_runtime.setText(description.strip())
            except Exception:
                dialog._lbl_argos_install_runtime.setText(stripped)
        elif stripped:
            dialog._lbl_argos_install_runtime.setText(stripped)


def finish_argos_install(
    dialog: Any, exit_code: int, exit_status: QProcess.ExitStatus
) -> None:
    """Handle completion of the Argos pack-install subprocess."""
    process: QProcess | None = getattr(dialog, "_argos_install_process", None)
    if process is None:
        return
    was_cancelled = bool(getattr(dialog, "_argos_install_cancelled", False))
    dialog._argos_install_process = None
    dialog._argos_install_cancelled = False

    if was_cancelled:
        set_progress(getattr(dialog, "_argos_progress", None), 0, 1)
        set_argos_busy(dialog, False, "Argos download canceled.")
        return

    if exit_status != QProcess.ExitStatus.NormalExit or exit_code != 0:
        stdout = bytes(process.readAllStandardOutput()).decode(errors="replace").strip()
        stderr = bytes(process.readAllStandardError()).decode(errors="replace").strip()
        details = stderr or stdout or f"Command failed with exit code {exit_code}."
        set_argos_busy(dialog, False, f"Argos pack install failed: {details}")
        return

    set_progress(
        getattr(dialog, "_argos_progress", None),
        getattr(dialog, "_argos_progress_total", 0),
        getattr(dialog, "_argos_progress_total", 0) or 1,
    )
    set_argos_busy(dialog, False, "Argos pack installed successfully.")
    refresh_argos_info(dialog)
    refresh_argos_package_index(dialog)
    if dialog.controller.local_libretranslate_enabled():
        dialog.controller.stop_local_libretranslate_server()
        from .libre import refresh_libre_local_info

        refresh_libre_local_info(dialog)
    dialog.controller.invalidate_translation_backend_languages("LibreTranslate")
    refresh_translation_runtime(dialog)


def start_argos_install(dialog: Any, pairs: list[tuple[str, str]]) -> None:
    """Install one or more Argos language packs via subprocess."""
    if not pairs:
        dialog._lbl_argos_install_runtime.setText("No Argos packs selected to install.")
        return

    process = QProcess(dialog)
    process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
    process.readyReadStandardOutput.connect(lambda: handle_argos_process_output(dialog))
    process.readyReadStandardError.connect(lambda: handle_argos_process_output(dialog))
    process.finished.connect(
        lambda exit_code, exit_status: finish_argos_install(
            dialog, exit_code, exit_status
        )
    )
    dialog._argos_install_process = process
    dialog._argos_install_cancelled = False
    dialog._argos_progress_total = max(1, len(pairs) * 3)
    set_progress(
        getattr(dialog, "_argos_progress", None), 0, dialog._argos_progress_total
    )

    payload = json.dumps(
        {
            "package_dir": str(argos_install_dir(dialog)),
            "pairs": [[src, tgt] for src, tgt in pairs],
        }
    )
    command = [
        sys.executable,
        "-c",
        (
            "import json; "
            "from screen_translate.core.translation.argos_backend import run_argos_install_cli; "
            f"run_argos_install_cli(**json.loads({payload!r}))"
        ),
    ]
    if len(pairs) == 1:
        src, tgt = pairs[0]
        set_argos_busy(dialog, True, f"Installing Argos pack {src} → {tgt}…")
    else:
        set_argos_busy(dialog, True, f"Installing {len(pairs)} Argos language packs…")
    process.start(command[0], command[1:])


def cancel_argos_install(dialog: Any) -> None:
    """Cancel the active Argos package install process."""
    process: QProcess | None = getattr(dialog, "_argos_install_process", None)
    if process is None:
        return
    dialog._argos_install_cancelled = True
    dialog._lbl_argos_install_runtime.setText("Canceling Argos download…")
    process.terminate()
    if not process.waitForFinished(1500):
        process.kill()


def install_argos_table_pack(dialog: Any, from_code: str, to_code: str) -> None:
    """Install a specific Argos language pack from the packages table."""
    start_argos_install(dialog, [(from_code, to_code)])


def install_all_argos_packs(dialog: Any) -> None:
    """Install every Argos language pack shown in the package table."""
    packages = getattr(dialog, "_argos_packages", [])
    installed_pairs = getattr(dialog, "_argos_installed_pairs", set())
    pairs = [
        (
            str(getattr(pkg, "from_code", "")).strip(),
            str(getattr(pkg, "to_code", "")).strip(),
        )
        for pkg in packages
        if (
            str(getattr(pkg, "from_code", "")).strip(),
            str(getattr(pkg, "to_code", "")).strip(),
        )
        not in installed_pairs
    ]
    pairs = [(src, tgt) for src, tgt in pairs if src and tgt]
    start_argos_install(dialog, pairs)


def refresh_argos_table_install_state(dialog: Any) -> None:
    """Refresh installed-state labels and button states in the Argos packages table."""
    table: TableWidget | None = getattr(dialog, "_tbl_argos_packs", None)
    if table is None:
        return
    installed_pairs = getattr(dialog, "_argos_installed_pairs", set())
    for row in range(table.rowCount()):
        source_item = table.item(row, 0)
        target_item = table.item(row, 1)
        status_item = table.item(row, 2)
        action_widget = table.cellWidget(row, 3)
        if source_item is None or target_item is None or status_item is None:
            continue
        pair = (source_item.text(), target_item.text())
        installed = pair in installed_pairs
        status_item.setText("Installed" if installed else "Available")
        if isinstance(action_widget, PushButton):
            action_widget.setEnabled(not installed)
            action_widget.setText("Installed" if installed else "Install")


def filter_argos_packages_table(dialog: Any, text: str = "") -> None:
    """Filter visible Argos pack rows by language code or status."""
    table: TableWidget | None = getattr(dialog, "_tbl_argos_packs", None)
    if table is None:
        return
    needle = text.strip().lower()
    for row in range(table.rowCount()):
        values: list[str] = []
        for column in range(3):
            item = table.item(row, column)
            if item is not None:
                values.append(item.text())
        haystack = " ".join(values).lower()
        table.setRowHidden(row, bool(needle) and needle not in haystack)


def rebuild_argos_packages_table(dialog: Any) -> None:
    """Rebuild the Argos language-packs table from the loaded package index."""
    table: TableWidget | None = getattr(dialog, "_tbl_argos_packs", None)
    if table is None:
        return
    packages = getattr(dialog, "_argos_packages", [])
    refresh_argos_installed_set(dialog)

    table.setRowCount(len(packages))
    for row, pkg in enumerate(packages):
        from_code = str(getattr(pkg, "from_code", "")).strip()
        to_code = str(getattr(pkg, "to_code", "")).strip()
        table.setItem(row, 0, QTableWidgetItem(from_code))
        table.setItem(row, 1, QTableWidgetItem(to_code))
        table.setItem(row, 2, QTableWidgetItem(""))
        action_btn = PushButton("Install")
        action_btn.clicked.connect(
            lambda _checked=False, src=from_code, tgt=to_code: install_argos_table_pack(
                dialog, src, tgt
            )
        )
        table.setCellWidget(row, 3, action_btn)

    refresh_argos_table_install_state(dialog)
    search_widget = getattr(dialog, "_le_argos_search", None)
    search_text = search_widget.text() if isinstance(search_widget, LineEdit) else ""
    filter_argos_packages_table(dialog, search_text)


def build_argos_section(dialog: Any) -> QWidget:
    """Build the Argos Translate settings section."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    from .shared import default_argos_package_dir, make_passthrough_line_edit

    grp_argos, fl_argos = dialog._group_form("Argos Translate")
    argos_banner = InfoBannerCard(
        "Argos Translate",
        "Direct offline backend. Screen Translate talks to installed Argos language packs in-process, "
        "without an HTTP server. Use LibreTranslate if you want a local or remote API/server workflow.",
        page,
    )
    layout.addWidget(argos_banner)
    lbl_argos = QLabel(
        "Argos Translate is the offline backend. It uses installed language packs and "
        "does not use network proxy settings."
    )
    lbl_argos.setWordWrap(True)
    fl_argos.addRow(lbl_argos)
    dialog._lbl_argos_status = QLabel()
    dialog._lbl_argos_dir = QLabel()
    dialog._lbl_argos_dir.setWordWrap(True)
    dialog._argos_dir_edit = make_passthrough_line_edit(
        dialog,
        "argos_package_dir",
        str(default_argos_package_dir()),
    )
    dialog._argos_dir_edit.editingFinished.connect(
        lambda: apply_argos_dir_change(dialog, dialog._argos_dir_edit.text())
    )
    dialog._lbl_argos_installed_codes = QLabel()
    dialog._lbl_argos_installed_codes.setWordWrap(True)
    dialog._btn_argos_refresh = PushButton("Refresh Installed Info")
    dialog._btn_argos_refresh.clicked.connect(lambda: refresh_argos_info(dialog))
    fl_argos.addRow("Status:", dialog._lbl_argos_status)
    fl_argos.addRow("Active package dir:", dialog._lbl_argos_dir)
    dir_row = QHBoxLayout()
    dialog._btn_argos_browse_dir = PushButton("Browse")
    dialog._btn_argos_browse_dir.clicked.connect(lambda: browse_argos_dir(dialog))
    dialog._btn_argos_open_dir = PushButton("Open Package Folder")
    dialog._btn_argos_open_dir.clicked.connect(lambda: open_argos_dir(dialog))
    dir_row.addWidget(dialog._argos_dir_edit, 1)
    dir_row.addWidget(dialog._btn_argos_browse_dir)
    dir_row.addWidget(dialog._btn_argos_open_dir)
    fl_argos.addRow("Configured dir:", dir_row)
    fl_argos.addRow("Disk usage:", dialog._lbl_argos_installed_codes)
    fl_argos.addRow("", dialog._btn_argos_refresh)
    layout.addWidget(grp_argos)

    grp_argos_manage, fl_argos_manage = dialog._group_form(
        "Manage Argos Language Packs"
    )
    lbl_manage = BodyLabel(
        "Use the Argos package index to install offline translation packs for the "
        "direct Argos backend. Search the table below and install packs from the action column."
    )
    lbl_manage.setWordWrap(True)
    fl_argos_manage.addRow(lbl_manage)
    dialog._lbl_argos_index_status = QLabel("Refreshing package index…")
    dialog._lbl_argos_index_status.setWordWrap(True)
    fl_argos_manage.addRow("Index status:", dialog._lbl_argos_index_status)

    dialog._le_argos_search = LineEdit()
    dialog._le_argos_search.setPlaceholderText(
        "Search by source code, target code, or status…"
    )
    dialog._le_argos_search.textChanged.connect(
        lambda text: filter_argos_packages_table(dialog, text)
    )
    fl_argos_manage.addRow("Search:", dialog._le_argos_search)

    button_row = QHBoxLayout()
    dialog._btn_argos_load_index = PushButton("Refresh Package Index")
    dialog._btn_argos_load_index.clicked.connect(
        lambda: refresh_argos_package_index(dialog)
    )
    dialog._btn_argos_install_all = PushButton("Install All Packs")
    dialog._btn_argos_install_all.clicked.connect(
        lambda: install_all_argos_packs(dialog)
    )
    dialog._btn_argos_cancel = PushButton("Stop Download")
    dialog._btn_argos_cancel.setEnabled(False)
    dialog._btn_argos_cancel.clicked.connect(lambda: cancel_argos_install(dialog))
    button_row.addWidget(dialog._btn_argos_load_index)
    button_row.addWidget(dialog._btn_argos_install_all)
    button_row.addWidget(dialog._btn_argos_cancel)
    button_row.addStretch(1)
    fl_argos_manage.addRow(button_row)

    dialog._argos_progress = QProgressBar()
    dialog._argos_progress.setTextVisible(True)
    dialog._argos_progress.setValue(0)
    fl_argos_manage.addRow("Progress:", dialog._argos_progress)
    dialog._lbl_argos_install_runtime = QLabel()
    dialog._lbl_argos_install_runtime.setWordWrap(True)
    fl_argos_manage.addRow("Runtime:", dialog._lbl_argos_install_runtime)

    dialog._tbl_argos_packs = TableWidget()
    dialog._tbl_argos_packs.setRowCount(0)
    dialog._tbl_argos_packs.setColumnCount(4)
    dialog._tbl_argos_packs.setHorizontalHeaderLabels(
        ["From", "To", "Status", "Action"]
    )
    dialog._tbl_argos_packs.verticalHeader().setVisible(False)
    header = dialog._tbl_argos_packs.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
    dialog._tbl_argos_packs.setMinimumHeight(280)
    layout.addWidget(grp_argos_manage)
    layout.addWidget(dialog._tbl_argos_packs, 1)
    layout.addStretch()
    return page

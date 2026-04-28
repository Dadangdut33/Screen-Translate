"""LibreTranslate settings section and helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import QProcess, QProcessEnvironment, QUrl, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, CheckBox, FluentIcon as FIF, PushButton

from screen_translate.core.translation.argos_backend import configure_argos_package_dir
from screen_translate.core.translation.libretranslate_local import (
    default_local_libretranslate_dir,
    inspect_local_libretranslate,
    local_libretranslate_command,
    local_libretranslate_setup_steps,
)

from .shared import (
    confirm_directory_move,
    directory_has_content,
    format_bytes,
    libre_install_dir,
    libre_package_dir,
    make_passthrough_line_edit,
    make_reload_line_edit,
    move_directory_contents,
    normalize_path,
    paths_equivalent,
    persist_backend_setting,
    refresh_translation_runtime,
    update_libre_mode_visibility,
)


def _collect_local_libre_language_summary(dialog: Any) -> tuple[str, str]:
    """Return a summary and details of locally available LibreTranslate languages."""
    if dialog.controller.is_local_libretranslate_running():
        backend = dialog.controller._backends.get("LibreTranslate")
        if backend is not None:
            dialog.controller.invalidate_translation_backend_languages("LibreTranslate")
            codes = [
                code
                for code in backend.available_languages()
                if code not in {"auto", "Auto"}
            ]
            if codes:
                return (
                    f"{len(codes)} language codes available through the local LibreTranslate API",
                    ", ".join(codes),
                )
    try:
        configure_argos_package_dir(str(libre_package_dir(dialog)))
        import argostranslate.package as argos_package

        packages = [
            pkg
            for pkg in argos_package.get_installed_packages()
            if str(getattr(pkg, "type", "translate")) == "translate"
        ]
        codes = sorted(
            {
                str(getattr(pkg, "from_code", "")).strip()
                for pkg in packages
                if str(getattr(pkg, "from_code", "")).strip()
            }
            | {
                str(getattr(pkg, "to_code", "")).strip()
                for pkg in packages
                if str(getattr(pkg, "to_code", "")).strip()
            }
        )
        if codes:
            return (
                f"{len(codes)} installed language codes from {len(packages)} local model pairs",
                ", ".join(codes),
            )
    except Exception:
        pass
    return (
        "No local language models detected yet.",
        "Run Update Installed Models to download more LibreTranslate models.",
    )


def refresh_libre_local_info(dialog: Any) -> None:
    """Refresh the app-local LibreTranslate installation summary."""
    install_dir = libre_install_dir(dialog)
    dialog._libre_local_dir.blockSignals(True)
    dialog._libre_local_dir.setText(str(install_dir))
    dialog._libre_local_dir.blockSignals(False)

    info = inspect_local_libretranslate(install_dir)
    port = str(dialog.s.get("libre_local_port", "5000")).strip() or "5000"
    status = "Installed" if info.installed else "Not installed"
    version = info.package_version or "n/a"
    dialog._lbl_libre_local_status.setText(f"{status}  |  libretranslate: {version}")
    if getattr(dialog, "_btn_libre_setup", None) is not None:
        dialog._btn_libre_setup.setText(
            "Update LibreTranslate" if info.installed else "Setup LibreTranslate"
        )
    dialog._lbl_libre_local_size.setText(format_bytes(info.size_bytes))
    dialog._lbl_libre_local_python.setText(str(info.python_executable))
    dialog._lbl_libre_local_command.setText(str(info.command_executable))
    if getattr(dialog, "_libre_local_package_dir", None) is not None:
        dialog._libre_local_package_dir.blockSignals(True)
        dialog._libre_local_package_dir.setText(str(libre_package_dir(dialog)))
        dialog._libre_local_package_dir.blockSignals(False)
    endpoint = f"http://127.0.0.1:{port}"
    dialog._lbl_libre_local_endpoint.setText(endpoint)
    is_running = dialog.controller.is_local_libretranslate_running()
    if getattr(dialog, "_lbl_libre_local_running", None) is not None:
        if is_running:
            dialog._lbl_libre_local_running.setText(
                "Running and reachable on the configured local endpoint."
            )
        elif info.installed:
            dialog._lbl_libre_local_running.setText(
                "Stopped. Screen Translate will auto-start it when the local LibreTranslate backend is used."
            )
        else:
            dialog._lbl_libre_local_running.setText("Not installed yet.")
    if getattr(dialog, "_lbl_libre_local_note", None) is not None:
        dialog._lbl_libre_local_note.setText(
            "Screen Translate will auto-start the managed local LibreTranslate server when needed "
            "and stop it when the app exits."
        )

    installed_items = info.installed_items or [
        "No managed LibreTranslate components found yet."
    ]
    dialog._libre_local_details.setPlainText("\n".join(installed_items))
    summary, details = _collect_local_libre_language_summary(dialog)
    dialog._lbl_libre_local_languages.setText(summary)
    dialog._libre_local_language_details.setPlainText(details)


def set_libre_setup_busy(dialog: Any, busy: bool, status_text: str = "") -> None:
    """Update the local LibreTranslate setup UI busy state."""
    dialog._btn_libre_setup.setEnabled(not busy)
    dialog._btn_libre_update_models.setEnabled(not busy)
    dialog._btn_libre_cancel_models.setEnabled(
        bool(getattr(dialog, "_libre_model_update_busy", False))
    )
    dialog._btn_libre_browse.setEnabled(not busy)
    dialog._btn_libre_open_dir.setEnabled(not busy)
    dialog._btn_libre_package_browse.setEnabled(not busy)
    dialog._btn_libre_package_open_dir.setEnabled(not busy)
    if getattr(dialog, "_libre_local_port", None) is not None:
        dialog._libre_local_port.setEnabled(not busy)
    if getattr(dialog, "_libre_local_package_dir", None) is not None:
        dialog._libre_local_package_dir.setEnabled(not busy)
    if status_text:
        dialog._lbl_libre_setup_runtime.setText(status_text)


def _append_libre_runtime_output(dialog: Any, text: str) -> None:
    """Append readable subprocess output to the Libre runtime output box."""
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not lines:
        return
    for line in lines:
        dialog._libre_runtime_output.appendPlainText(line)
    dialog._libre_runtime_output.verticalScrollBar().setValue(
        dialog._libre_runtime_output.verticalScrollBar().maximum()
    )


def _on_libre_setup_ready_read(dialog: Any) -> None:
    """Handle streamed output from LibreTranslate setup subprocess."""
    process: QProcess | None = getattr(dialog, "_libre_setup_process", None)
    if process is None:
        return
    output = bytes(process.readAllStandardOutput()).decode(errors="replace")
    output += bytes(process.readAllStandardError()).decode(errors="replace")
    if output:
        _append_libre_runtime_output(dialog, output)


def _run_next_libre_setup_step(dialog: Any) -> None:
    """Run the next queued LibreTranslate setup subprocess step."""
    process: QProcess | None = getattr(dialog, "_libre_setup_process", None)
    steps: list[list[str]] = getattr(dialog, "_libre_setup_steps", [])

    if process is None:
        return
    if not steps:
        dialog._libre_progress.setMaximum(
            getattr(dialog, "_libre_progress_total", 0) or 1
        )
        dialog._libre_progress.setValue(getattr(dialog, "_libre_progress_total", 0))
        set_libre_setup_busy(dialog, False, "LibreTranslate setup completed.")
        refresh_libre_local_info(dialog)
        return

    step_number = getattr(dialog, "_libre_progress_step", 0) + 1
    dialog._libre_progress_step = step_number
    command = steps.pop(0)
    descriptions = getattr(dialog, "_libre_setup_descriptions", [])
    description = (
        descriptions[step_number - 1]
        if step_number - 1 < len(descriptions)
        else "Running setup step"
    )
    dialog._libre_progress.setMaximum(
        getattr(dialog, "_libre_progress_total", len(descriptions) or 1)
    )
    dialog._libre_progress.setValue(step_number - 1)
    dialog._lbl_libre_setup_runtime.setText(
        f"Step {step_number}/{getattr(dialog, '_libre_progress_total', len(descriptions) or 1)}: {description}"
    )
    process.start(command[0], command[1:])


def _finish_libre_setup(
    dialog: Any, exit_code: int, exit_status: QProcess.ExitStatus
) -> None:
    """Handle completion of one LibreTranslate setup step."""
    process: QProcess | None = getattr(dialog, "_libre_setup_process", None)
    if process is None:
        return
    dialog._libre_setup_process = None

    if exit_status != QProcess.ExitStatus.NormalExit or exit_code != 0:
        stdout = bytes(process.readAllStandardOutput()).decode(errors="replace").strip()
        stderr = bytes(process.readAllStandardError()).decode(errors="replace").strip()
        details = stderr or stdout or f"Command failed with exit code {exit_code}."
        set_libre_setup_busy(dialog, False, f"LibreTranslate setup failed: {details}")
        return

    _run_next_libre_setup_step(dialog)


def setup_local_libretranslate(dialog: Any) -> None:
    """Create or update the app-managed local LibreTranslate installation."""
    install_dir = libre_install_dir(dialog)
    install_dir.mkdir(parents=True, exist_ok=True)

    steps = local_libretranslate_setup_steps(install_dir)
    dialog._libre_setup_descriptions = [
        "Creating virtual environment",
        "Upgrading pip",
        "Installing libretranslate package",
    ]
    process = QProcess(dialog)
    process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
    env = QProcessEnvironment.systemEnvironment()
    package_dir = str(libre_package_dir(dialog))
    env.insert("ARGOS_PACKAGES_DIR", package_dir)
    env.insert("ARGOS_PACKAGE_DIR", package_dir)
    env.insert("ARGOS_TRANSLATE_PACKAGE_DIR", package_dir)
    env.insert("PYTHONUNBUFFERED", "1")
    env.insert(
        "PYTHONWARNINGS",
        "ignore::requests.exceptions.RequestsDependencyWarning",
    )
    process.setProcessEnvironment(env)
    process.readyReadStandardOutput.connect(lambda: _on_libre_setup_ready_read(dialog))
    process.readyReadStandardError.connect(lambda: _on_libre_setup_ready_read(dialog))
    process.finished.connect(
        lambda exit_code, exit_status: _finish_libre_setup(
            dialog, exit_code, exit_status
        )
    )

    dialog._libre_setup_process = process
    dialog._libre_setup_steps = steps
    dialog._libre_progress_total = len(steps)
    dialog._libre_progress_step = 0
    dialog._libre_progress.setMaximum(len(steps) or 1)
    dialog._libre_progress.setValue(0)
    dialog._libre_runtime_output.clear()
    set_libre_setup_busy(dialog, True, "Preparing local LibreTranslate setup…")
    _run_next_libre_setup_step(dialog)


def update_local_libre_models(dialog: Any) -> None:
    """Run `libretranslate --update-models` for the managed local instance."""
    install_dir = libre_install_dir(dialog)
    info = inspect_local_libretranslate(install_dir)
    if not info.command_executable.exists():
        dialog._lbl_libre_setup_runtime.setText(
            "LibreTranslate is not installed yet. Run setup first."
        )
        return

    dialog.controller.stop_local_libretranslate_server()

    process = QProcess(dialog)
    process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
    env = QProcessEnvironment.systemEnvironment()
    package_dir = str(libre_package_dir(dialog))
    env.insert("ARGOS_PACKAGES_DIR", package_dir)
    env.insert("ARGOS_PACKAGE_DIR", package_dir)
    env.insert("ARGOS_TRANSLATE_PACKAGE_DIR", package_dir)
    env.insert("PYTHONUNBUFFERED", "1")
    env.insert(
        "PYTHONWARNINGS",
        "ignore::requests.exceptions.RequestsDependencyWarning",
    )
    process.setProcessEnvironment(env)
    process.readyReadStandardOutput.connect(
        lambda: _append_libre_runtime_output(
            dialog,
            bytes(process.readAllStandardOutput()).decode(errors="replace"),
        )
    )
    process.readyReadStandardError.connect(
        lambda: _append_libre_runtime_output(
            dialog,
            bytes(process.readAllStandardError()).decode(errors="replace"),
        )
    )
    dialog._libre_model_update_process = process
    dialog._libre_model_update_cancelled = False
    dialog._libre_model_update_busy = True

    def _finish_models(exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        dialog._libre_model_update_process = None
        dialog._libre_model_update_busy = False
        was_cancelled = bool(getattr(dialog, "_libre_model_update_cancelled", False))
        dialog._libre_model_update_cancelled = False
        if was_cancelled:
            dialog._libre_progress.setMaximum(1)
            dialog._libre_progress.setValue(0)
            set_libre_setup_busy(dialog, False, "LibreTranslate model update canceled.")
            return
        if exit_status != QProcess.ExitStatus.NormalExit or exit_code != 0:
            output = (
                bytes(process.readAllStandardOutput()).decode(errors="replace").strip()
            )
            dialog._libre_progress.setMaximum(1)
            dialog._libre_progress.setValue(0)
            set_libre_setup_busy(
                dialog,
                False,
                f"LibreTranslate model update failed: {output or f'exit code {exit_code}'}",
            )
            return
        dialog.controller.invalidate_translation_backend_languages("LibreTranslate")
        refresh_translation_runtime(dialog)
        dialog._libre_progress.setMaximum(1)
        dialog._libre_progress.setValue(1)
        set_libre_setup_busy(
            dialog, False, "LibreTranslate models updated successfully."
        )
        refresh_libre_local_info(dialog)

    process.finished.connect(_finish_models)
    dialog._libre_progress.setRange(0, 0)
    dialog._libre_runtime_output.clear()
    set_libre_setup_busy(dialog, True, "Updating installed LibreTranslate models…")
    process.start(str(local_libretranslate_command(install_dir)), ["--update-models"])


def cancel_local_libre_models_update(dialog: Any) -> None:
    """Cancel the active LibreTranslate model update process."""
    process: QProcess | None = getattr(dialog, "_libre_model_update_process", None)
    if process is None:
        return
    dialog._libre_model_update_cancelled = True
    dialog._lbl_libre_setup_runtime.setText("Canceling LibreTranslate model update…")
    process.terminate()
    if not process.waitForFinished(1500):
        process.kill()


def browse_libre_local_dir(dialog: Any) -> None:
    """Choose the managed LibreTranslate installation directory."""
    current = str(libre_install_dir(dialog))
    chosen = QFileDialog.getExistingDirectory(
        dialog,
        "Choose LibreTranslate install directory",
        current,
    )
    if not chosen:
        return
    apply_libre_local_dir_change(dialog, chosen)


def open_libre_local_dir(dialog: Any) -> None:
    """Open the managed LibreTranslate install directory."""
    install_dir = libre_install_dir(dialog)
    install_dir.mkdir(parents=True, exist_ok=True)
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(install_dir)))


def browse_libre_package_dir(dialog: Any) -> None:
    """Choose the local LibreTranslate model/package directory."""
    current = str(libre_package_dir(dialog))
    chosen = QFileDialog.getExistingDirectory(
        dialog,
        "Choose LibreTranslate model package directory",
        current,
    )
    if not chosen:
        return
    apply_libre_package_dir_change(dialog, chosen)


def apply_libre_local_dir_change(dialog: Any, raw_value: str) -> None:
    """Persist a new managed LibreTranslate install directory and move content."""
    old_dir = libre_install_dir(dialog)
    new_dir = normalize_path(raw_value or default_local_libretranslate_dir())

    if paths_equivalent(old_dir, new_dir):
        dialog._libre_local_dir.blockSignals(True)
        dialog._libre_local_dir.setText(str(new_dir))
        dialog._libre_local_dir.blockSignals(False)
        dialog.s.set("libre_local_dir", str(new_dir))
        refresh_libre_local_info(dialog)
        return

    dialog.controller.stop_local_libretranslate_server()

    if directory_has_content(old_dir):
        confirmed = confirm_directory_move(
            dialog,
            title="Move LibreTranslate Runtime",
            subject="The managed LibreTranslate Python environment and runtime files",
            source=old_dir,
            destination=new_dir,
        )
        if not confirmed:
            dialog._libre_local_dir.blockSignals(True)
            dialog._libre_local_dir.setText(str(old_dir))
            dialog._libre_local_dir.blockSignals(False)
            refresh_libre_local_info(dialog)
            return
        try:
            move_directory_contents(old_dir, new_dir)
        except Exception as exc:
            dialog._lbl_libre_setup_runtime.setText(
                f"Could not move LibreTranslate runtime: {exc}"
            )
            dialog._libre_local_dir.blockSignals(True)
            dialog._libre_local_dir.setText(str(old_dir))
            dialog._libre_local_dir.blockSignals(False)
            refresh_libre_local_info(dialog)
            return

    dialog.s.set("libre_local_dir", str(new_dir))
    refresh_libre_local_info(dialog)


def apply_libre_package_dir_change(dialog: Any, raw_value: str) -> None:
    """Persist a new local LibreTranslate package directory and move models."""
    old_dir = libre_package_dir(dialog)
    raw_text = raw_value.strip()
    new_dir = normalize_path(raw_text) if raw_text else normalize_path(argos_install_dir(dialog))

    if paths_equivalent(old_dir, new_dir):
        dialog._libre_local_package_dir.blockSignals(True)
        dialog._libre_local_package_dir.setText(str(new_dir))
        dialog._libre_local_package_dir.blockSignals(False)
        dialog.s.set("libre_local_package_dir", raw_text)
        refresh_libre_local_info(dialog)
        refresh_translation_runtime(dialog)
        return

    dialog.controller.stop_local_libretranslate_server()

    if directory_has_content(old_dir):
        confirmed = confirm_directory_move(
            dialog,
            title="Move LibreTranslate Models",
            subject="The local LibreTranslate model packages",
            source=old_dir,
            destination=new_dir,
        )
        if not confirmed:
            dialog._libre_local_package_dir.blockSignals(True)
            dialog._libre_local_package_dir.setText(str(old_dir))
            dialog._libre_local_package_dir.blockSignals(False)
            refresh_libre_local_info(dialog)
            return
        try:
            move_directory_contents(old_dir, new_dir)
        except Exception as exc:
            dialog._lbl_libre_setup_runtime.setText(
                f"Could not move LibreTranslate model packages: {exc}"
            )
            dialog._libre_local_package_dir.blockSignals(True)
            dialog._libre_local_package_dir.setText(str(old_dir))
            dialog._libre_local_package_dir.blockSignals(False)
            refresh_libre_local_info(dialog)
            return

    dialog.s.set("libre_local_package_dir", raw_text)
    refresh_libre_local_info(dialog)
    refresh_translation_runtime(dialog)


def open_libre_package_dir(dialog: Any) -> None:
    """Open the local LibreTranslate model/package directory."""
    package_dir = libre_package_dir(dialog)
    package_dir.mkdir(parents=True, exist_ok=True)
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(package_dir)))


def on_libre_use_local_toggled(dialog: Any, checked: bool) -> None:
    """Persist local LibreTranslate mode and refresh UI/backend state."""
    dialog.s.set("libre_use_local", checked)
    update_libre_mode_visibility(dialog)
    refresh_translation_runtime(dialog)


def _build_banner_card(title: str, content: str, parent: QWidget) -> QFrame:
    """Build a simple explanatory card."""
    card = QFrame(parent)
    card.setStyleSheet(
        """
        QFrame {
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            background-color: rgba(255, 255, 255, 0.03);
        }
        QLabel {
            border: none;
            background: transparent;
        }
        """
    )
    layout = QHBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(12)

    icon_label = QLabel(card)
    icon_label.setPixmap(FIF.INFO.icon().pixmap(18, 18))
    layout.addWidget(icon_label, 0)
    layout.setAlignment(icon_label, Qt.AlignmentFlag.AlignTop)

    text_layout = QVBoxLayout()
    text_layout.setContentsMargins(0, 0, 0, 0)
    text_layout.setSpacing(6)
    title_label = QLabel(title, card)
    title_label.setStyleSheet("font-weight: 600;")
    body_label = BodyLabel(content, card)
    body_label.setWordWrap(True)
    text_layout.addWidget(title_label)
    text_layout.addWidget(body_label)
    layout.addLayout(text_layout, 1)
    return card


def build_libre_section(dialog: Any) -> QWidget:
    """Build the LibreTranslate settings section."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    grp_libre, fl_libre = dialog._group_form("LibreTranslate")
    libre_banner = _build_banner_card(
        "LibreTranslate",
        "Server/API backend. In local mode, Screen Translate manages a local LibreTranslate runtime "
        "and model directory for you. Unlike Argos Translate, this backend runs through an HTTP service "
        "instead of direct in-process translation.",
        page,
    )
    layout.addWidget(libre_banner)
    dialog._chk_libre_use_local = CheckBox("Use local LibreTranslate installation")
    dialog._chk_libre_use_local.setChecked(bool(dialog.s.get("libre_use_local", False)))
    dialog._chk_libre_use_local.toggled.connect(
        lambda checked: on_libre_use_local_toggled(dialog, checked)
    )
    fl_libre.addRow(dialog._chk_libre_use_local)

    dialog._grp_libre_local = QWidget()
    libre_local_layout = QVBoxLayout(dialog._grp_libre_local)
    libre_local_layout.setContentsMargins(0, 0, 0, 0)
    libre_local_layout.setSpacing(8)

    local_intro = BodyLabel(
        "Screen Translate can maintain a local LibreTranslate Python environment for "
        "you. It can also update the local model set used by the managed server."
    )
    local_intro.setWordWrap(True)
    libre_local_layout.addWidget(local_intro)

    dir_row = QHBoxLayout()
    dialog._libre_local_dir = make_passthrough_line_edit(
        dialog,
        "libre_local_dir",
        str(default_local_libretranslate_dir()),
    )
    dialog._libre_local_dir.editingFinished.connect(
        lambda: apply_libre_local_dir_change(dialog, dialog._libre_local_dir.text())
    )
    dialog._btn_libre_browse = PushButton("Browse")
    dialog._btn_libre_browse.clicked.connect(lambda: browse_libre_local_dir(dialog))
    dialog._btn_libre_open_dir = PushButton("Open Folder")
    dialog._btn_libre_open_dir.clicked.connect(lambda: open_libre_local_dir(dialog))
    dir_row.addWidget(dialog._libre_local_dir, 1)
    dir_row.addWidget(dialog._btn_libre_browse)
    dir_row.addWidget(dialog._btn_libre_open_dir)
    libre_local_layout.addLayout(dir_row)

    package_row = QHBoxLayout()
    dialog._libre_local_package_dir = make_passthrough_line_edit(
        dialog,
        "libre_local_package_dir",
        str(libre_package_dir(dialog)),
    )
    dialog._libre_local_package_dir.editingFinished.connect(
        lambda: apply_libre_package_dir_change(
            dialog, dialog._libre_local_package_dir.text()
        )
    )
    dialog._btn_libre_package_browse = PushButton("Browse")
    dialog._btn_libre_package_browse.clicked.connect(
        lambda: browse_libre_package_dir(dialog)
    )
    dialog._btn_libre_package_open_dir = PushButton("Open Package Folder")
    dialog._btn_libre_package_open_dir.clicked.connect(
        lambda: open_libre_package_dir(dialog)
    )
    package_row.addWidget(dialog._libre_local_package_dir, 1)
    package_row.addWidget(dialog._btn_libre_package_browse)
    package_row.addWidget(dialog._btn_libre_package_open_dir)
    libre_local_layout.addWidget(QLabel("Local model package dir:"))
    libre_local_layout.addLayout(package_row)

    port_row = QHBoxLayout()
    dialog._libre_local_port = make_reload_line_edit(dialog, "libre_local_port", "5000")
    dialog._libre_local_port.editingFinished.connect(
        lambda: refresh_libre_local_info(dialog)
    )
    port_row.addWidget(dialog._libre_local_port, 1)
    libre_local_layout.addWidget(QLabel("Local port:"))
    libre_local_layout.addLayout(port_row)

    dialog._lbl_libre_local_status = QLabel()
    dialog._lbl_libre_local_size = QLabel()
    dialog._lbl_libre_local_python = QLabel()
    dialog._lbl_libre_local_command = QLabel()
    dialog._lbl_libre_local_endpoint = QLabel()
    dialog._lbl_libre_local_running = QLabel()
    dialog._lbl_libre_local_note = QLabel()
    dialog._lbl_libre_local_languages = QLabel()
    for label in (
        dialog._lbl_libre_local_status,
        dialog._lbl_libre_local_endpoint,
        dialog._lbl_libre_local_running,
        dialog._lbl_libre_local_python,
        dialog._lbl_libre_local_command,
        dialog._lbl_libre_local_note,
        dialog._lbl_libre_local_languages,
    ):
        label.setWordWrap(True)
    libre_status_group, libre_status_form = dialog._group_form("Managed Local Runtime")
    libre_status_form.addRow("Install status:", dialog._lbl_libre_local_status)
    libre_status_form.addRow("Managed endpoint:", dialog._lbl_libre_local_endpoint)
    libre_status_form.addRow("Local instance status:", dialog._lbl_libre_local_running)
    libre_status_form.addRow("Managed Python:", dialog._lbl_libre_local_python)
    libre_status_form.addRow("Managed command:", dialog._lbl_libre_local_command)
    libre_status_form.addRow("Total install size:", dialog._lbl_libre_local_size)
    libre_status_form.addRow("Installed languages:", dialog._lbl_libre_local_languages)
    libre_status_form.addRow(dialog._lbl_libre_local_note)
    libre_local_layout.addWidget(libre_status_group)

    dialog._libre_local_language_details = QPlainTextEdit()
    dialog._libre_local_language_details.setReadOnly(True)
    dialog._libre_local_language_details.setFixedHeight(72)
    libre_local_layout.addWidget(QLabel("Language details:"))
    libre_local_layout.addWidget(dialog._libre_local_language_details)

    dialog._libre_local_details = QPlainTextEdit()
    dialog._libre_local_details.setReadOnly(True)
    dialog._libre_local_details.setFixedHeight(90)
    libre_local_layout.addWidget(QLabel("Installed components:"))
    libre_local_layout.addWidget(dialog._libre_local_details)

    setup_row = QHBoxLayout()
    dialog._btn_libre_setup = PushButton("Setup LibreTranslate")
    dialog._btn_libre_setup.clicked.connect(lambda: setup_local_libretranslate(dialog))
    dialog._btn_libre_update_models = PushButton("Update Installed Models")
    dialog._btn_libre_update_models.clicked.connect(
        lambda: update_local_libre_models(dialog)
    )
    dialog._btn_libre_cancel_models = PushButton("Cancel Download")
    dialog._btn_libre_cancel_models.setEnabled(False)
    dialog._btn_libre_cancel_models.clicked.connect(
        lambda: cancel_local_libre_models_update(dialog)
    )
    setup_row.addWidget(dialog._btn_libre_setup)
    setup_row.addWidget(dialog._btn_libre_update_models)
    setup_row.addWidget(dialog._btn_libre_cancel_models)
    libre_local_layout.addLayout(setup_row)
    dialog._lbl_libre_setup_runtime = QLabel()
    dialog._lbl_libre_setup_runtime.setWordWrap(True)
    libre_local_layout.addWidget(dialog._lbl_libre_setup_runtime)
    dialog._libre_progress = QProgressBar()
    dialog._libre_progress.setTextVisible(True)
    dialog._libre_progress.setValue(0)
    libre_local_layout.addWidget(dialog._libre_progress)
    dialog._libre_runtime_output = QPlainTextEdit()
    dialog._libre_runtime_output.setReadOnly(True)
    dialog._libre_runtime_output.setFixedHeight(90)
    libre_local_layout.addWidget(dialog._libre_runtime_output)

    fl_libre.addRow(dialog._grp_libre_local)

    dialog._grp_libre_remote = QWidget()
    libre_remote_layout = QVBoxLayout(dialog._grp_libre_remote)
    libre_remote_layout.setContentsMargins(0, 0, 0, 0)
    libre_remote_layout.setSpacing(8)

    remote_intro = QLabel(
        "When local LibreTranslate is disabled, Screen Translate talks to a remote "
        "LibreTranslate-compatible server using the endpoint below."
    )
    remote_intro.setWordWrap(True)
    libre_remote_layout.addWidget(remote_intro)

    remote_host = make_reload_line_edit(
        dialog, "libre_host", "translate.argosopentech.com"
    )
    remote_port = make_reload_line_edit(dialog, "libre_port", "5000 or blank")
    remote_api_key = make_reload_line_edit(
        dialog, "libre_api_key", "optional", password=True
    )
    remote_https = CheckBox("Use HTTPS")
    remote_https.setChecked(bool(dialog.s.get("libre_https", True)))
    remote_https.toggled.connect(
        lambda checked: persist_backend_setting(dialog, "libre_https", checked)
    )

    grp_remote_form, fl_remote = dialog._group_form("Remote LibreTranslate Endpoint")
    fl_remote.addRow("Host:", remote_host)
    fl_remote.addRow("Port:", remote_port)
    fl_remote.addRow("", remote_https)
    fl_remote.addRow("API Key:", remote_api_key)
    libre_remote_layout.addWidget(grp_remote_form)

    fl_libre.addRow(dialog._grp_libre_remote)
    layout.addWidget(grp_libre)
    layout.addStretch()
    return page

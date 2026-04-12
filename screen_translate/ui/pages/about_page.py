"""About application page."""

from __future__ import annotations

import json
import importlib.resources
from pathlib import Path
from urllib.parse import quote, urlparse

from PyQt6.QtCore import QThreadPool, Qt, QUrl, pyqtSlot
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    Dialog,
    InfoBar,
    InfoBarIcon,
    InfoBarPosition,
    PrimaryPushButton,
    PushButton,
    RoundMenu,
    TitleLabel,
)
import qtawesome as qta

from screen_translate import __version__
from screen_translate.config.settings import SETTINGS_PATH
from screen_translate.ui.screen_capture import captured_dir
from screen_translate.ui.theme.style_sheet import StyleSheet
from screen_translate.ui.theme.utils import load_icon
from screen_translate.ui.update_check import (
    detect_install_method,
    UpdateCheckWorker,
    detect_run_method,
    is_newer_version,
    releases_url,
    update_instructions,
)

_SOURCE_FUNDING_FILE = Path(__file__).resolve().parents[3] / ".github" / "FUNDING.yml"
_FUNDING_PLATFORM_URLS: dict[str, str] = {
    "github": "https://github.com/sponsors/{value}",
    "patreon": "https://patreon.com/{value}",
    "open_collective": "https://opencollective.com/{value}",
    "ko_fi": "https://ko-fi.com/{value}",
    "liberapay": "https://liberapay.com/{value}",
    "issuehunt": "https://issuehunt.io/r/{value}",
    "otechie": "https://otechie.com/{value}",
}
_FUNDING_PLATFORM_ICONS: dict[str, str] = {
    "github": "mdi6.github",
    "patreon": "mdi6.patreon",
    "open_collective": "mdi6.hand-heart",
    "ko_fi": "mdi6.coffee-outline",
    "liberapay": "mdi6.currency-usd",
    "issuehunt": "mdi6.bug-outline",
    "otechie": "mdi6.lifebuoy",
    "custom": "mdi6.cash",
    "paypal": "mdi6.paypal",
    "buymeacoffee": "mdi6.coffee",
}


def _human_bytes(size: int) -> str:
    """Return a human-friendly size string."""
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{size} B"


def _settings_directory() -> Path:
    """Return the parent directory that stores settings.ini."""
    return Path(SETTINGS_PATH).parent


def _directory_size(path: Path) -> tuple[int, int]:
    """Return (bytes, file_count) for a directory tree."""
    if not path.exists():
        return 0, 0
    total_size = 0
    file_count = 0
    for child in path.rglob("*"):
        if child.is_file():
            file_count += 1
            try:
                total_size += child.stat().st_size
            except OSError:
                continue
    return total_size, file_count


def _parse_funding_value(raw: str) -> list[str]:
    """Parse a single FUNDING.yml scalar or simple list value."""
    value = raw.split("#", 1)[0].strip()
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip("'\"") for part in inner.split(",") if part.strip()]
    return [value.strip().strip("'\"")]


def _detect_custom_funding_target(url: str) -> tuple[str, str]:
    """Infer a friendlier label/icon key for custom funding URLs."""
    host = urlparse(url).netloc.lower()
    if "paypal.me" in host or "paypal.com" in host:
        return "PayPal", "paypal"
    if "buymeacoffee.com" in host:
        return "Buy Me a Coffee", "buymeacoffee"
    if "ko-fi.com" in host:
        return "Ko-fi", "ko_fi"
    if "github.com" in host and "/sponsors/" in url.lower():
        return "GitHub Sponsors", "github"
    return "Custom", "custom"


def _funding_icon(icon_key: str) -> object:
    """Return a qtawesome mdi6 icon for a funding entry."""
    icon_name = _FUNDING_PLATFORM_ICONS.get(icon_key, "mdi6.cash")
    try:
        return qta.icon(icon_name)
    except Exception:
        return qta.icon("mdi6.cash")


def _read_funding_text() -> str:
    """Read funding metadata from source tree or packaged assets."""
    if _SOURCE_FUNDING_FILE.exists():
        try:
            return _SOURCE_FUNDING_FILE.read_text(encoding="utf-8")
        except OSError:
            pass

    try:
        asset = importlib.resources.files("screen_translate.assets").joinpath(
            "FUNDING.yml"
        )
        return asset.read_text(encoding="utf-8")
    except Exception:
        return ""


def _load_funding_links() -> list[tuple[str, str, str]]:
    """Read simple GitHub funding metadata without requiring a YAML dependency."""
    funding_text = _read_funding_text()
    if not funding_text.strip():
        return []

    links: list[tuple[str, str, str]] = []
    try:
        for line in funding_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or ":" not in stripped:
                continue
            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            values = _parse_funding_value(raw_value)
            if not values:
                continue

            if key == "custom":
                for value in values:
                    if value:
                        label, icon_key = _detect_custom_funding_target(value)
                        links.append((label, value, icon_key))
                continue

            template = _FUNDING_PLATFORM_URLS.get(key)
            if template is None:
                continue
            label = key.replace("_", " ").title()
            for value in values:
                if value:
                    links.append(
                        (
                            label,
                            template.format(value=quote(value, safe="")),
                            key,
                        )
                    )
    except OSError:
        return []

    return links


class AboutPage(QWidget):
    """Embedded About page showing app metadata, update status, and paths."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._latest_release_url = releases_url()
        self._update_worker_running = False
        self._funding_links = _load_funding_links()

        self.setWindowTitle("About")
        self.setObjectName("AboutPage")
        StyleSheet.AUXILIARY_WINDOW.apply(self)
        self._build_ui()
        self._refresh_runtime_details()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setSpacing(16)

        hero = QFrame(self)
        hero.setObjectName("AboutHeroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 22, 22, 22)
        hero_layout.setSpacing(12)

        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        icon_label = QLabel(hero)
        icon = load_icon()
        if not icon.isNull():
            pixmap = icon.pixmap(72, 72)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap)
        header_row.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(6)
        title = TitleLabel("Screen Translate", hero)
        title_col.addWidget(title)

        self._version_label = BodyLabel(f"Version {__version__}", hero)
        self._version_label.setObjectName("AboutVersion")
        title_col.addWidget(self._version_label)

        desc = BodyLabel(
            "A desktop OCR and translation tool for quick screen capture, snipping, "
            "and translation workflows across multiple engines.",
            hero,
        )
        desc.setWordWrap(True)
        title_col.addWidget(desc)
        header_row.addLayout(title_col, 1)
        hero_layout.addLayout(header_row)

        update_row = QHBoxLayout()
        update_row.setSpacing(10)
        self._btn_check_update = PrimaryPushButton("Check for Updates", hero)
        self._btn_check_update.clicked.connect(self._check_for_updates)
        update_row.addWidget(self._btn_check_update)

        self._btn_funding = PushButton("Funding", hero)
        self._btn_funding.setIcon(_funding_icon("custom"))
        self._btn_funding.clicked.connect(self._open_funding)
        self._btn_funding.setEnabled(bool(self._funding_links))
        update_row.addWidget(self._btn_funding)

        self._update_status = BodyLabel("Update status: not checked yet", hero)
        self._update_status.setObjectName("AboutUpdateStatus")
        update_row.addWidget(self._update_status, 1)
        hero_layout.addLayout(update_row)

        self._update_banner = InfoBar(
            InfoBarIcon.INFORMATION,
            "Update Available",
            "A newer version is available.",
            duration=-1,
            position=InfoBarPosition.NONE,
            parent=hero,
            isClosable=False,
        )
        self._btn_open_release = PushButton("Open Release Page", self._update_banner)
        self._btn_open_release.clicked.connect(self._open_release_page)
        self._update_banner.addWidget(self._btn_open_release)
        self._update_banner.hide()
        hero_layout.addWidget(self._update_banner)

        outer.addWidget(hero)

        info = QFrame(self)
        info.setObjectName("AboutInfoCard")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(22, 22, 22, 22)
        info_layout.setSpacing(12)

        info_title = TitleLabel("Environment", info)
        info_title.setObjectName("AboutSectionTitle")
        info_layout.addWidget(info_title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)

        version_row = QWidget(info)
        version_row_layout = QHBoxLayout(version_row)
        version_row_layout.setContentsMargins(0, 0, 0, 0)
        version_row_layout.setSpacing(10)
        version_row_layout.addWidget(BodyLabel(__version__, version_row), 0)
        version_row_layout.addStretch(1)
        form.addRow("App version:", version_row)

        self._settings_path_label = BodyLabel("", info)
        self._settings_path_label.setWordWrap(True)
        settings_row = self._path_row(
            self._settings_path_label, self._open_settings_dir
        )
        form.addRow("Settings directory:", settings_row)

        self._capture_path_label = BodyLabel("", info)
        self._capture_path_label.setWordWrap(True)
        capture_row = self._path_row(self._capture_path_label, self._open_capture_dir)
        form.addRow("Saved images:", capture_row)

        self._install_method_label = BodyLabel("", info)
        self._install_method_label.setWordWrap(True)
        form.addRow("Install method:", self._install_method_label)

        self._run_method_label = BodyLabel("", info)
        self._run_method_label.setWordWrap(True)
        form.addRow("Run method:", self._run_method_label)

        info_layout.addLayout(form)
        outer.addWidget(info)
        outer.addStretch(1)

    def _path_row(self, label: BodyLabel, open_slot: object) -> QWidget:
        """Create a path row with an inline open button."""
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(label, 1)
        button = PushButton("Open", row)
        button.clicked.connect(open_slot)
        layout.addWidget(button)
        return row

    def showEvent(self, event: object) -> None:  # type: ignore[override]
        """Refresh path and storage details whenever the page is shown."""
        super().showEvent(event)
        self._refresh_runtime_details()

    def _refresh_runtime_details(self) -> None:
        """Refresh settings/capture paths and runtime metadata."""
        settings_dir = _settings_directory()
        capture_path = captured_dir()
        capture_path.mkdir(parents=True, exist_ok=True)
        total_size, file_count = _directory_size(capture_path)

        self._settings_path_label.setText(str(settings_dir))
        self._capture_path_label.setText(
            f"{capture_path}\n{file_count} file(s), {_human_bytes(total_size)}"
        )
        self._install_method_label.setText(detect_install_method())
        self._run_method_label.setText(detect_run_method())

    @pyqtSlot()
    def _check_for_updates(self) -> None:
        """Fetch the latest release and compare it with the running version."""
        if self._update_worker_running:
            return
        self._update_worker_running = True
        self._btn_check_update.setEnabled(False)
        self._update_status.setText("Checking GitHub releases...")

        worker = UpdateCheckWorker()
        worker.signals.finished.connect(self._on_update_check_finished)
        worker.signals.error.connect(self._on_update_check_error)
        QThreadPool.globalInstance().start(worker)

    @pyqtSlot(str, str, str)
    def _on_update_check_finished(
        self,
        latest_version: str,
        release_url: str,
        release_title: str,
    ) -> None:
        """Handle a completed update check."""
        self._update_worker_running = False
        self._btn_check_update.setEnabled(True)
        self._latest_release_url = release_url

        if is_newer_version(latest_version, __version__):
            self._update_status.setText(
                f"Update available: {latest_version} ({release_title})"
            )
            self._update_banner.contentLabel.setText(
                f"Version {latest_version} is available. Open the release page for download and notes."
            )
            self._update_banner.show()
            dialog = Dialog(
                "Update Available",
                (
                    f"A newer version is available: {latest_version}\n\n"
                    f"Detected install method:\n{detect_install_method()}\n\n"
                    f"How to update:\n{update_instructions()}"
                ),
                self,
            )
            dialog.yesButton.setText("Open Release Page")
            dialog.cancelButton.setText("Later")
            if dialog.exec():
                self._open_release_page()
            return

        self._update_banner.hide()
        self._update_status.setText("You are already on the latest version.")
        QMessageBox.information(
            self,
            "Up To Date",
            "You are already running the latest available version.",
        )

    @pyqtSlot(str)
    def _on_update_check_error(self, error: str) -> None:
        """Handle update-check failure."""
        self._update_worker_running = False
        self._btn_check_update.setEnabled(True)
        self._update_status.setText("Update check failed.")
        QMessageBox.warning(
            self,
            "Update Check Failed",
            f"Could not check for updates.\n\n{error}",
        )

    def _open_release_page(self) -> None:
        """Open the releases page for the detected update."""
        QDesktopServices.openUrl(QUrl(self._latest_release_url))

    def _open_funding(self) -> None:
        """Open a funding link or present a funding menu when multiple are available."""
        if not self._funding_links:
            return
        if len(self._funding_links) == 1:
            _, url, _ = self._funding_links[0]
            QDesktopServices.openUrl(QUrl(url))
            return

        menu = RoundMenu(parent=self)
        for label, url, icon_key in self._funding_links:
            action = QAction(_funding_icon(icon_key), label, menu)
            action.setStatusTip(url)
            action.triggered.connect(
                lambda _checked=False, target=url: QDesktopServices.openUrl(
                    QUrl(target)
                )
            )
            menu.addAction(action)
        menu.exec(self._btn_funding.mapToGlobal(self._btn_funding.rect().bottomLeft()))

    def _open_settings_dir(self) -> None:
        """Open the settings directory in the system file manager."""
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(_settings_directory())))

    def _open_capture_dir(self) -> None:
        """Open the captured-images directory in the system file manager."""
        path = captured_dir()
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


AboutDialog = AboutPage

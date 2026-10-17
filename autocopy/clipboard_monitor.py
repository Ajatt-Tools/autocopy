# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import aqt
from aqt import gui_hooks
from aqt.qt import *

from .config import AutoCopyConfig, get_global_config


def is_anki_active() -> bool:
    if aqt.mw.isActiveWindow():
        return True
    # noinspection PyProtectedMember
    for _, window in aqt.dialogs._dialogs.values():
        if window and window.isActiveWindow():
            return True
    return False


class ClipboardMonitor:
    """Handle clipboard monitoring with injected session configuration."""

    def __init__(self, cfg: AutoCopyConfig) -> None:
        """Store the same configuration used by copying and menus."""
        self._cfg = cfg

    def on_clipboard_content_changed(self, mode: QClipboard.Mode) -> None:
        if self._cfg.clipboard_monitor and mode == QClipboard.Mode.Clipboard and not is_anki_active():
            clipboard_text = QApplication.clipboard().text()
            if clipboard_text.startswith("file://"):
                return
            browser = aqt.dialogs.open("Browser", aqt.mw)
            browser.activateWindow()
            browser.form.searchEdit.lineEdit().setText(clipboard_text)
            if hasattr(browser, "onSearch"):
                browser.onSearch()
            else:
                browser.onSearchActivated()

    def connect_clipboard(self) -> None:
        """Connect after the main window has initialized the application clipboard."""
        qconnect(QApplication.clipboard().changed, self.on_clipboard_content_changed)

    def setup(self) -> None:
        gui_hooks.main_window_did_init.append(self.connect_clipboard)


def init() -> None:
    """Create the session clipboard monitor and register its initialization hook."""
    assert aqt.mw, "Anki should be open."
    # Keep explicit main-window ownership in addition to the signal closure's capture.
    aqt.mw._ajt__autocopy_clipboard_monitor = controller = ClipboardMonitor(get_global_config())
    controller.setup()

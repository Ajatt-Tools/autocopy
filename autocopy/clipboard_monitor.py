# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import aqt
from aqt import gui_hooks, mw
from aqt.qt import *

from .config import AutoCopyConfig, get_global_config


def is_anki_active() -> bool:
    if mw.isActiveWindow():
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
        """Search clipboard text when monitoring is enabled and Anki is inactive."""
        if self._cfg.clipboard_monitor and mode == QClipboard.Mode.Clipboard and not is_anki_active():
            clipboard = QApplication.clipboard()
            if clipboard is None:
                return
            clipboard_text = clipboard.text()
            if clipboard_text.startswith("file://"):
                return
            browser = aqt.dialogs.open("Browser", mw)
            browser.activateWindow()
            browser.form.searchEdit.lineEdit().setText(clipboard_text)
            if hasattr(browser, "onSearch"):
                browser.onSearch()
            else:
                browser.onSearchActivated()

    def connect_clipboard(self) -> None:
        """Connect after the main window has initialized the application clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return
        # The closure retains this non-QObject controller after the startup hook returns.
        qconnect(clipboard.changed, lambda mode: self.on_clipboard_content_changed(mode))

    def setup(self) -> None:
        """Retain the monitor through Anki's main-window initialization hook."""
        gui_hooks.main_window_did_init.append(self.connect_clipboard)


def init() -> None:
    """Create the session clipboard monitor and register its initialization hook."""
    assert mw, "Anki should be open."
    controller = ClipboardMonitor(get_global_config())
    setattr(mw, "_ajt__autocopy_clipboard_monitor", controller)
    controller.setup()

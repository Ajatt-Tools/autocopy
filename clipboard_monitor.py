# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import aqt
from aqt import gui_hooks
from aqt.qt import *

from .config import config


def is_anki_active() -> bool:
    if aqt.mw.isActiveWindow():
        return True
    # noinspection PyProtectedMember
    for _, window in aqt.dialogs._dialogs.values():
        if window and window.isActiveWindow():
            return True
    return False


def on_clipboard_content_changed(mode: QClipboard.Mode) -> None:
    if config.clipboard_monitor and mode == QClipboard.Mode.Clipboard and not is_anki_active():
        clipboard_text = QApplication.clipboard().text()
        if clipboard_text.startswith('file://'):
            return
        browser = aqt.dialogs.open('Browser', aqt.mw)
        browser.activateWindow()
        browser.form.searchEdit.lineEdit().setText(clipboard_text)
        if hasattr(browser, 'onSearch'):
            browser.onSearch()
        else:
            browser.onSearchActivated()


def setup():
    gui_hooks.main_window_did_init.append(lambda: qconnect(
        QApplication.clipboard().changed,
        on_clipboard_content_changed,
    ))

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import cast
from unittest.mock import Mock, create_autospec, patch

import pytest
from aqt import AnkiQt
from aqt.qt import QApplication, QClipboard, QDialog

from autocopy import clipboard_monitor
from autocopy.config import AutoCopyConfig
from tests.helpers import make_search_browser


class TestAnkiActive:
    """Exercise the real active-window check rather than only mocking its result."""

    @pytest.mark.parametrize(
        ("main_active", "dialog_active", "expected"),
        [(True, False, True), (False, True, True), (False, False, False), (False, None, False)],
        ids=["main-window", "dialog", "inactive", "closed-dialogs"],
    )
    def test_active_windows(self, main_active: bool, dialog_active: bool | None, expected: bool) -> None:
        """Detect active windows while ignoring registered dialogs that are already closed."""
        window = create_autospec(AnkiQt, instance=True)
        window.isActiveWindow.return_value = main_active
        dialog = create_autospec(QDialog, instance=True)
        dialog.isActiveWindow.return_value = dialog_active is True
        # Anki's registry keeps closed entries. Visit one before checking a live dialog.
        registry = {"closed": [None, None], "open": [None, dialog if dialog_active is not None else None]}
        with patch.object(clipboard_monitor, "mw", window):
            with patch.object(clipboard_monitor.aqt.dialogs, "_dialogs", registry):
                assert clipboard_monitor.is_anki_active() == expected


class TestClipboardMonitor:
    """Preserve clipboard search behavior with instance-owned configuration."""

    @pytest.mark.parametrize(
        ("enabled", "mode", "active", "text"),
        [
            (False, QClipboard.Mode.Clipboard, False, "text"),
            (True, QClipboard.Mode.Selection, False, "text"),
            (True, QClipboard.Mode.Clipboard, True, "text"),
            (True, QClipboard.Mode.Clipboard, False, "file:///picture.jpg"),
        ],
    )
    def test_ignored_changes(
        self,
        qapp: QApplication,
        isolated_clipboard: None,
        no_anki_config: AutoCopyConfig,
        enabled: bool,
        mode: QClipboard.Mode,
        active: bool,
        text: str,
    ) -> None:
        """Do not open the Browser for disabled, irrelevant, active-window, or file changes."""
        controller = clipboard_monitor.ClipboardMonitor(no_anki_config)
        no_anki_config["clipboard_monitor"] = enabled
        clipboard = qapp.clipboard()
        assert clipboard is not None
        clipboard.setText(text)
        with patch.object(clipboard_monitor, "is_anki_active", return_value=active):
            with patch.object(clipboard_monitor.aqt.dialogs, "open", autospec=True) as open_browser:
                controller.on_clipboard_content_changed(mode)
        open_browser.assert_not_called()

    @pytest.mark.parametrize("legacy", [True, False])
    def test_search(
        self, qapp: QApplication, isolated_clipboard: None, no_anki_config: AutoCopyConfig, legacy: bool
    ) -> None:
        """Populate the Browser search and support both search activation APIs."""
        no_anki_config["clipboard_monitor"] = True
        browser = make_search_browser(legacy=legacy)
        clipboard = qapp.clipboard()
        assert clipboard is not None
        clipboard.setText("日本語")
        window = create_autospec(AnkiQt, instance=True)
        with patch.object(clipboard_monitor, "mw", window):
            with patch.object(clipboard_monitor, "is_anki_active", return_value=False):
                with patch.object(clipboard_monitor.aqt.dialogs, "open", return_value=browser) as open_browser:
                    clipboard_monitor.ClipboardMonitor(no_anki_config).on_clipboard_content_changed(
                        QClipboard.Mode.Clipboard
                    )
        open_browser.assert_called_once_with("Browser", window)
        cast(Mock, browser.activateWindow).assert_called_once_with()
        search_edit = browser.form.searchEdit.lineEdit()
        assert search_edit is not None
        assert search_edit.text() == "日本語"
        cast(Mock, getattr(browser, "onSearch" if legacy else "onSearchActivated")).assert_called_once_with()

    def test_registration(self, qapp: QApplication, no_anki_config: AutoCopyConfig) -> None:
        """Delay clipboard connection until Anki initialization and retain the controller."""
        controller = clipboard_monitor.ClipboardMonitor(no_anki_config)
        # Keep the Python clipboard wrapper alive while comparing its bound Qt signal.
        clipboard = qapp.clipboard()
        assert clipboard is not None
        with patch.object(clipboard_monitor.gui_hooks.main_window_did_init, "append", autospec=True) as append:
            controller.setup()
        append.assert_called_once_with(controller.connect_clipboard)
        with patch.object(clipboard_monitor, "qconnect", autospec=True) as connect:
            append.call_args.args[0]()
        signal, callback = connect.call_args.args
        assert signal == clipboard.changed
        with patch.object(controller, "on_clipboard_content_changed", autospec=True) as changed:
            callback(QClipboard.Mode.Clipboard)
        changed.assert_called_once_with(QClipboard.Mode.Clipboard)

    @pytest.mark.parametrize("operation", ["connect", "search"])
    def test_unavailable_clipboard(self, no_anki_config: AutoCopyConfig, operation: str) -> None:
        """Ignore missing clipboards without connecting signals or opening the Browser."""
        no_anki_config["clipboard_monitor"] = True
        controller = clipboard_monitor.ClipboardMonitor(no_anki_config)
        with patch.object(clipboard_monitor.QApplication, "clipboard", return_value=None):
            with patch.object(clipboard_monitor, "is_anki_active", return_value=False):
                with patch.object(clipboard_monitor, "qconnect", autospec=True) as connect:
                    with patch.object(clipboard_monitor.aqt.dialogs, "open", autospec=True) as open_browser:
                        if operation == "connect":
                            controller.connect_clipboard()
                        else:
                            controller.on_clipboard_content_changed(QClipboard.Mode.Clipboard)
        connect.assert_not_called()
        open_browser.assert_not_called()

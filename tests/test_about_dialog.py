# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import cast
from unittest.mock import Mock, create_autospec, patch

import pytest
from aqt.qt import QApplication, QDialog, QVBoxLayout, QWidget
from aqt.webview import AnkiWebView
from beartype import beartype

from autocopy.ajt_common import about_menu, restore_geom_dialog


@beartype
def make_about_dialog(parent: QWidget) -> about_menu.AboutDialog:
    """Construct the real dialog without starting Chromium or requiring Anki UI services."""
    with patch.object(about_menu, "tweak_window", autospec=True):
        with patch.object(about_menu.AboutDialog, "make_root_layout", return_value=QVBoxLayout()):
            return about_menu.AboutDialog(parent)


class TestAboutDialog:
    """Cover the geometry-aware base class introduced by the shared-code update."""

    @pytest.mark.parametrize("active_profile", [False, True])
    @pytest.mark.parametrize("operation", ["show", "exec", "accept", "reject"])
    def test_geometry_lifecycle(self, qapp: QApplication, active_profile: bool, operation: str) -> None:
        """Restore and save geometry only when profile storage is available."""
        parent = QWidget()
        with patch.object(restore_geom_dialog, "can_access_geom_data", return_value=active_profile):
            with patch.object(restore_geom_dialog, "restoreGeom", autospec=True) as restore:
                with patch.object(restore_geom_dialog, "saveGeom", autospec=True) as save:
                    with patch.object(QDialog, "exec", return_value=QDialog.DialogCode.Accepted):
                        dialog = make_about_dialog(parent)
                        getattr(dialog, operation)()
        restore_count = (2 if operation in ("show", "exec") else 1) if active_profile else 0
        assert restore.call_args_list == [((dialog, "ajt__about_dialog"), {"adjustSize": True})] * restore_count
        assert save.call_args_list == (
            [((dialog, "ajt__about_dialog"), {})] if active_profile and operation in ("accept", "reject") else []
        )

    @pytest.mark.parametrize("html", ["", "<p>About</p>"])
    def test_webview_identity(self, qapp: QApplication, html: str) -> None:
        """Use the stable dialog identity for the embedded webview without launching Chromium."""
        parent = QWidget()
        dialog = make_about_dialog(parent)
        webview = create_autospec(AnkiWebView, instance=True)
        with patch.object(about_menu, "AnkiWebView", autospec=True, return_value=webview) as constructor:
            assert dialog.make_about_webview(html) is webview
        constructor.assert_called_once_with(parent=dialog)
        cast(Mock, webview.setObjectName).assert_called_once_with("ajt__about_dialog")

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import gc
import weakref
from unittest.mock import create_autospec, patch

import pytest
from aqt import AnkiQt
from aqt.qt import QApplication, QDialog, QMenu

from autocopy import menus
from autocopy.config import AutoCopyConfig


class TestMenus:
    """Test real menu signals, retained receivers, and shared configuration."""

    @pytest.mark.parametrize("activated", [True, False])
    def test_toggle(self, qapp: QApplication, no_anki_config: AutoCopyConfig, activated: bool) -> None:
        """Retain the owner after setup and persist menu-triggered changes."""
        no_anki_config.activated = activated
        root = QMenu()
        controller = menus.AutoCopyMenus(no_anki_config, root_menu=root)
        controller.setup()
        owner = weakref.ref(controller)
        del controller
        gc.collect()
        assert owner() is not None
        toggle, settings = root.actions()
        assert (toggle.isCheckable(), toggle.isChecked(), settings.text()) == (True, activated, "Autocopy Options...")
        with patch.object(no_anki_config, "write_config", autospec=True) as write:
            toggle.trigger()
        assert (no_anki_config.activated, toggle.isChecked()) == (not activated, not activated)
        write.assert_called_once_with()

    @pytest.mark.parametrize("activated", [True, False])
    def test_settings(self, qapp: QApplication, no_anki_config: AutoCopyConfig, activated: bool) -> None:
        """Pass the exact shared config and update the action when settings are accepted."""
        no_anki_config.activated = not activated
        root = QMenu()
        controller = menus.AutoCopyMenus(no_anki_config, root_menu=root)
        controller.setup()
        dialog = QDialog()
        no_anki_config.activated = activated
        window = create_autospec(AnkiQt, instance=True)
        # Settings are parented to Anki's main window, not the menu's containing widget.
        with patch.object(menus, "mw", window):
            with patch.object(menus, "AutocopySettingsDialog", autospec=True, return_value=dialog) as constructor:
                with patch.object(dialog, "exec", side_effect=dialog.accept) as execute:
                    root.actions()[1].trigger()
        constructor.assert_called_once_with(no_anki_config, window)
        execute.assert_called_once_with()
        assert root.actions()[0].isChecked() == activated

    def test_init(self, qapp: QApplication, no_anki_config: AutoCopyConfig, monkeypatch: pytest.MonkeyPatch) -> None:
        """Compose menu ownership from the cached config and AJT root menu only at startup."""
        root = QMenu()
        window = create_autospec(AnkiQt, instance=True)
        monkeypatch.setattr(menus, "mw", window)
        with patch.object(menus, "get_global_config", return_value=no_anki_config) as get_config:
            with patch.object(menus, "menu_root_entry", return_value=root) as get_root:
                with patch.object(menus, "AutoCopyMenus", autospec=True) as constructor:
                    menus.init()
        get_config.assert_called_once_with()
        get_root.assert_called_once_with()
        constructor.assert_called_once_with(no_anki_config, root_menu=root)
        constructor.return_value.setup.assert_called_once_with()
        assert window._ajt__autocopy_menus is constructor.return_value

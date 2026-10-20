# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
from gettext import gettext as _

from aqt import mw
from aqt.qt import *

from .ajt_common.about_menu import menu_root_entry
from .config import AutoCopyConfig, get_global_config
from .options_dialog import ADDON_NAME, AutocopySettingsDialog


class AutoCopyMenus:
    """Own Autocopy menu actions and their injected session configuration."""

    def __init__(self, cfg: AutoCopyConfig, *, root_menu: QMenu) -> None:
        """Create the toggle action within the supplied AJT menu."""
        self._cfg = cfg
        self._root_menu = root_menu
        self._toggle_action = QAction(_(f"Activate {ADDON_NAME}"), root_menu)
        self._toggle_action.setCheckable(True)
        self._setup_toggle_action()

    def _setup_toggle_action(self) -> None:
        self._update_toggle_action()
        # Qt does not retain plain Python bound-method receivers. Capture the owner explicitly
        # as a second lifetime safeguard alongside the main window's controller reference.
        qconnect(self._toggle_action.triggered, lambda: self._toggle_activated())

    def _update_toggle_action(self) -> None:
        self._toggle_action.setChecked(self._cfg.activated)

    def _on_open_settings(self) -> None:
        dialog = AutocopySettingsDialog(self._cfg, mw)
        qconnect(dialog.accepted, self._update_toggle_action)
        dialog.exec()

    def _setup_settings_action(self, parent: QWidget) -> QAction:
        action_settings = QAction(_(f"{ADDON_NAME} Options..."), parent)
        qconnect(action_settings.triggered, self._on_open_settings)
        return action_settings

    def _toggle_activated(self) -> None:
        self._cfg.activated = not self._cfg.activated
        self._update_toggle_action()
        self._cfg.write_config()

    def setup(self) -> None:
        self._root_menu.addAction(self._toggle_action)
        self._root_menu.addAction(self._setup_settings_action(self._root_menu))


def init() -> None:
    """Create menu actions sharing the session configuration."""
    assert mw, "Anki should be open."
    # Qt does not retain plain Python receivers. Keep the menu controller on the main window.
    mw._ajt__autocopy_menus = controller = AutoCopyMenus(get_global_config(), root_menu=menu_root_entry())
    controller.setup()

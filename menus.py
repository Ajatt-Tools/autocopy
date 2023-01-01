import functools
from gettext import gettext as _

from aqt import mw
from aqt.qt import *

from .ajt_common.about_menu import menu_root_entry
from .config import config
from .options_dialog import AutocopySettingsDialog, ADDON_NAME

TOGGLE_ACTION = 'ajt__toggle_autocopy_action'


def update_toggle_action():
    toggle_action: QAction = getattr(mw, TOGGLE_ACTION)
    toggle_action.setChecked(config.activated)


def on_open_settings():
    dialog = AutocopySettingsDialog(config, mw)
    qconnect(dialog.accepted, update_toggle_action)
    dialog.exec()


def setup_settings_action(parent: QWidget) -> QAction:
    action_settings = QAction(_(f"{ADDON_NAME} Options..."), parent)
    qconnect(action_settings.triggered, on_open_settings)
    return action_settings


def toggle_activated(self: QAction):
    config.activated = not config.activated
    self.setChecked(config.activated)
    config.write_config()


def setup_toggle_action(parent: QWidget) -> QAction:
    setattr(mw, TOGGLE_ACTION, toggle_action := QAction(_(f"Activate {ADDON_NAME}"), parent))
    toggle_action.setCheckable(True)
    toggle_action.setChecked(config.activated)
    qconnect(toggle_action.triggered, functools.partial(toggle_activated, self=toggle_action))
    return toggle_action


def setup():
    root_menu = menu_root_entry()
    root_menu.addAction(setup_toggle_action(root_menu))
    root_menu.addAction(setup_settings_action(root_menu))

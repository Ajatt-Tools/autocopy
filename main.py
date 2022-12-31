import functools
from gettext import gettext as _

from anki.cards import Card
from anki.utils import html_to_text_line
from aqt import gui_hooks
from aqt.qt import *

from .ajt_common.about_menu import menu_root_entry
from .config import config, write_config


def copy_content(card: Card):
    if config.activated and config.field in (note := card.note()):
        QApplication.clipboard().setText(html_to_text_line(note[config.field]), mode=QClipboard.Mode.Clipboard)


def toggle_activated(self: QAction):
    config.activated = not config.activated
    self.setChecked(config.activated)
    write_config()


def setup_menus():
    root_menu = menu_root_entry()
    toggle_active = QAction(_("Activate Auto Copy"), root_menu)
    toggle_active.setCheckable(True)
    toggle_active.setChecked(config.activated)
    qconnect(toggle_active.triggered, functools.partial(toggle_activated, self=toggle_active))
    root_menu.addAction(toggle_active)


def setup():
    gui_hooks.reviewer_did_show_answer.append(copy_content)
    setup_menus()

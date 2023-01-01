# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
from gettext import gettext as _

from anki.notes import Note
from anki.utils import html_to_text_line
from aqt import gui_hooks
from aqt.qt import *

from .ajt_common.about_menu import menu_root_entry
from .config import config


def copy_content(note: Note):
    if config.activated and config.field in note:
        QApplication.clipboard().setText(html_to_text_line(note[config.field]), mode=QClipboard.Mode.Clipboard)


def toggle_activated(self: QAction):
    config.activated = not config.activated
    self.setChecked(config.activated)
    config.write_config()


def setup_menus():
    root_menu = menu_root_entry()
    toggle_active = QAction(_("Activate Auto Copy"), root_menu)
    toggle_active.setCheckable(True)
    toggle_active.setChecked(config.activated)
    qconnect(toggle_active.triggered, functools.partial(toggle_activated, self=toggle_active))
    root_menu.addAction(toggle_active)


def on_change(note: Note, state: str):
    if config[state] is True:
        return copy_content(note)


def setup():
    gui_hooks.reviewer_did_show_question.append(lambda card: on_change(card.note(), "on_show_question"))
    gui_hooks.reviewer_did_show_answer.append(lambda card: on_change(card.note(), "on_show_answer"))
    gui_hooks.editor_did_load_note.append(lambda editor: on_change(editor.note, "on_editor_load_note"))
    setup_menus()

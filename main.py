# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from anki.notes import Note
from anki.utils import html_to_text_line
from aqt import gui_hooks
from aqt.qt import *

from .config import config


def get_fields_text(note: Note) -> str:
    return '\n'.join(note[field] for field in config.fields if field in note)


def copy_content(note: Note):
    if config.activated and (to_copy := get_fields_text(note)):
        QApplication.clipboard().setText(html_to_text_line(to_copy), mode=QClipboard.Mode.Clipboard)


def on_change(note: Note, state: str):
    if config[state] is True:
        return copy_content(note)


def setup():
    gui_hooks.reviewer_did_show_question.append(
        lambda card: on_change(card.note(), "on_show_question")
    )
    gui_hooks.reviewer_did_show_answer.append(
        lambda card: on_change(card.note(), "on_show_answer")
    )
    gui_hooks.browser_did_change_row.append(
        lambda browser: (browser.current_card and on_change(browser.current_card.note(), "on_select_note"))
    )
    gui_hooks.editor_did_load_note.append(
        lambda editor: on_change(editor.note, "on_editor_load_note")
    )

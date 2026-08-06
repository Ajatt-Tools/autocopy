# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from anki.notes import Note
from anki.utils import html_to_text_line
from aqt import gui_hooks
from aqt.editor import Editor
from aqt.qt import *

from .config import config


def get_fields_text(note: Note) -> str:
    return "\n".join(note[field] for field in config.fields if field in note)


def copy_to_clipboard(text: str) -> None:
    return QApplication.clipboard().setText(text, mode=QClipboard.Mode.Clipboard)


def copy_content(note: Note) -> None:
    if config.activated and (to_copy := get_fields_text(note)):
        copy_to_clipboard(html_to_text_line(to_copy))


def on_change(note: Note, state: str) -> None:
    if config[state] is False:
        return
    copy_content(note)


def get_editor_note(editor: Editor) -> Note | None:
    """Return the Note currently loaded in the editor, or None.

    Supports the legacy Editor (editor.note) and the NewEditor introduced in
    Anki 26.08, which only stores the note id (editor.nid) and must be fetched
    via mw.col.get_note().
    """
    if note := getattr(editor, "note", None):
        return note
    if nid := getattr(editor, "nid", None):
        assert editor.mw.col, "Collection must be open."
        return editor.mw.col.get_note(nid)
    return None


def on_editor_load_note(editor: Editor) -> None:
    """Copy configured fields when a note finishes loading in the editor.

    The config flag is checked before the note is resolved so that no database
    lookup happens when the feature is disabled.
    """
    if config["on_editor_load_note"] is False:
        return
    if note := get_editor_note(editor):
        on_change(note, "on_editor_load_note")


def setup() -> None:
    gui_hooks.reviewer_did_show_question.append(lambda card: on_change(card.note(), "on_show_question"))
    gui_hooks.reviewer_did_show_answer.append(lambda card: on_change(card.note(), "on_show_answer"))
    gui_hooks.browser_did_change_row.append(
        lambda browser: (browser.current_card and on_change(browser.current_card.note(), "on_select_note"))
    )
    gui_hooks.editor_did_load_note.append(on_editor_load_note)

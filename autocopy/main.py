# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


from collections.abc import Sequence

from anki.cards import Card
from anki.notes import Note
from anki.utils import html_to_text_line
from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.editor import Editor
from aqt.qt import *

from .config import AutoCopyConfig, get_global_config


def get_fields_text(note: Note, fields: Sequence[str]) -> str:
    return "\n".join(note[field] for field in fields if field in note)


def copy_to_clipboard(text: str) -> None:
    """Write text to the system clipboard."""
    if clipboard := QApplication.clipboard():
        clipboard.setText(text, mode=QClipboard.Mode.Clipboard)


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


class AutoCopy:
    """Handle copying callbacks with injected session configuration."""

    def __init__(self, cfg: AutoCopyConfig) -> None:
        """Store configuration supplied by the add-on startup code."""
        self._cfg = cfg

    def copy_content(self, note: Note) -> None:
        if self._cfg.activated and (to_copy := get_fields_text(note, self._cfg.fields)):
            copy_to_clipboard(html_to_text_line(to_copy))

    def on_change(self, note: Note, state: str) -> None:
        if self._cfg[state] is False:
            return
        self.copy_content(note)

    def on_editor_load_note(self, editor: Editor) -> None:
        """Copy configured fields when a note finishes loading in the editor.

        The config flag is checked before the note is resolved so that no database
        lookup happens when the feature is disabled.
        """
        if self._cfg["on_editor_load_note"] is False:
            return
        if note := get_editor_note(editor):
            self.on_change(note, "on_editor_load_note")

    def on_show_question(self, card: Card) -> None:
        """Handle the reviewer showing a question."""
        self.on_change(card.note(), "on_show_question")

    def setup(self) -> None:
        gui_hooks.reviewer_did_show_question.append(lambda card: self.on_show_question(card))
        gui_hooks.reviewer_did_show_answer.append(lambda card: self.on_change(card.note(), "on_show_answer"))
        gui_hooks.browser_did_change_row.append(
            lambda browser: (browser.current_card and self.on_change(browser.current_card.note(), "on_select_note"))
        )
        gui_hooks.editor_did_load_note.append(self.on_editor_load_note)


def init() -> None:
    """Create the session copying controller and register its callbacks."""
    assert mw, "Anki should be open."
    # The main window owns session controllers, matching the other AJT add-ons.
    mw._ajt__autocopy_events = controller = AutoCopy(get_global_config())
    controller.setup()

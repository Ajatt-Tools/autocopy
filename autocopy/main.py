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

try:
    from aqt.editor import NewEditor
except ImportError:
    # Older Anki releases expose only Editor. Keep annotations valid without weakening runtime checks.
    from aqt.editor import Editor as NewEditor  # type: ignore[assignment]

from .config import AutoCopyConfig, get_global_config


def get_fields_text(note: Note, fields: Sequence[str]) -> str:
    """Join existing fields in the configured order without converting their HTML."""
    return "\n".join(note[field] for field in fields if field in note)


def copy_to_clipboard(text: str) -> None:
    """Write text to the system clipboard."""
    if clipboard := QApplication.clipboard():
        clipboard.setText(text, mode=QClipboard.Mode.Clipboard)


def get_editor_note(editor: Editor | NewEditor) -> Note | None:
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
        """Copy configured fields using the existing single-line conversion."""
        if self._cfg.activated and (to_copy := get_fields_text(note, self._cfg.fields)):
            copy_to_clipboard(html_to_text_line(to_copy))

    def on_change(self, note: Note, state: str) -> None:
        """Copy a note only when the triggering event is enabled."""
        if self._cfg[state] is False:
            return
        self.copy_content(note)

    def on_editor_load_note(self, editor: Editor | NewEditor) -> None:
        """Copy the editor note, avoiding a database lookup when the event is disabled."""
        # Resolve the note only after checking the flag, especially for Anki's NewEditor.
        if self._cfg["on_editor_load_note"] is False:
            return
        if note := get_editor_note(editor):
            self.on_change(note, "on_editor_load_note")

    def on_show_question(self, card: Card) -> None:
        """Handle the reviewer showing a question."""
        self.on_change(card.note(), "on_show_question")

    def on_show_answer(self, card: Card) -> None:
        """Handle the reviewer showing an answer."""
        self.on_change(card.note(), "on_show_answer")

    def on_select_note(self, browser: Browser) -> None:
        """Copy the selected Browser card when one exists."""
        if card := browser.current_card:
            self.on_change(card.note(), "on_select_note")

    def setup(self) -> None:
        """Register copying callbacks on Anki's event hooks."""
        gui_hooks.reviewer_did_show_question.append(lambda card: self.on_show_question(card))
        gui_hooks.reviewer_did_show_answer.append(lambda card: self.on_show_answer(card))
        gui_hooks.browser_did_change_row.append(lambda browser: self.on_select_note(browser))
        gui_hooks.editor_did_load_note.append(self.on_editor_load_note)


def init() -> None:
    """Create the session copying controller and register its callbacks."""
    assert mw, "Anki should be open."
    controller = AutoCopy(get_global_config())
    setattr(mw, "_ajt__autocopy_events", controller)
    controller.setup()

# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Sequence

from anki.cards import Card
from anki.media import MediaManager
from anki.notes import Note
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


def html_to_clipboard_text(html: str, *, media: MediaManager) -> str:
    """Remove Anki media and convert HTML to plain text, retaining rendered line breaks."""
    # Qt preserves rendered line breaks that Anki's single-line converter flattens.
    document = QTextDocument()
    # Strip sound references and image markup before parsing HTML or decoding escaped literal text.
    document.setHtml(media.strip(html))
    return document.toPlainText()


def get_fields_text(note: Note, fields: Sequence[str]) -> str:
    """Remove field media and join plain text in order, preserving HTML line breaks."""
    return "\n".join(html_to_clipboard_text(note[field], media=note.col.media) for field in fields if field in note)


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
        """Copy nonblank field text without flattening its line breaks."""
        if not self._cfg.activated:
            return
        # Empty or media-only fields can leave separators. Do not overwrite useful clipboard text with them.
        if (to_copy := get_fields_text(note, self._cfg.fields)).strip():
            copy_to_clipboard(to_copy)

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
        # Explicit captures defend callback lifetimes in addition to main-window ownership.
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

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import importlib
from collections.abc import Sequence
from unittest.mock import create_autospec, patch

import aqt.editor
import pytest
from anki.cards import Card
from anki.collection import Collection
from aqt.browser import Browser
from aqt.editor import Editor, NewEditor
from aqt.qt import QApplication

from autocopy import main
from autocopy.config import AutoCopyConfig
from tests.helpers import make_editor, make_note


class TestFields:
    """Protect field selection and ordering independently of HTML conversion."""

    @pytest.mark.parametrize(
        ("fields", "expected"),
        [
            (("Front", "Back"), "front\nback"),
            (("Back", "Front"), "back\nfront"),
            (("Missing", "Front"), "front"),
            (("Missing",), ""),
            ((), ""),
            (("Front", "Front"), "front\nfront"),
        ],
    )
    def test_selection(self, anki_collection: Collection, fields: Sequence[str], expected: str) -> None:
        """Keep configured ordering, duplicates, and missing-field behavior."""
        note = make_note(anki_collection, front="<b>front</b>")
        assert main.get_fields_text(note, fields) == expected

    @pytest.mark.parametrize(
        ("front", "back", "expected"),
        [
            ("one<br>two", "<p>three</p><p>four</p>", "one\ntwo\nthree\nfour"),
            ("<b>one", "two</b>", "one\ntwo"),
            ("", "back", "\nback"),
            ("front", "", "front\n"),
            ('<img src="one.jpg">', '<img src="two.jpg">', "\n"),
            ("", "", "\n"),
        ],
    )
    def test_field_boundaries(self, anki_collection: Collection, front: str, back: str, expected: str) -> None:
        """Convert fields independently and retain separators even when individual fields are empty."""
        note = make_note(anki_collection, front=front, back=back)
        assert main.get_fields_text(note, ("Front", "Back")) == expected

    @pytest.mark.parametrize(
        ("html", "expected"),
        [
            ('<img src="picture.jpg">', ""),
            ('before<img src="picture.jpg">after', "beforeafter"),
            ('<img src="one.jpg"><br><img src="two.jpg">', "\n"),
            ("[sound:audio.mp3]", ""),
            ("[sound:one.mp3][sound:two.ogg]", ""),
            ("日本語[sound:audio.mp3]<br>text", "日本語\ntext"),
            ('<img src="picture.jpg">[sound:audio.mp3]', ""),
            ('one[sound:audio.mp3]<br><img src="picture.jpg">two', "one\ntwo"),
            ("[sound:日本語 音声.mp3]", ""),
            ("literal \ufffc character", "literal \ufffc character"),
            ("&lt;img src=x&gt;", "<img src=x>"),
            ("&#91;sound:audio.mp3&#93;", "[sound:audio.mp3]"),
        ],
    )
    def test_media_cleanup(self, anki_collection: Collection, html: str, expected: str) -> None:
        """Use the note's real media manager without reparsing escaped text as media references."""
        note = make_note(anki_collection, front=html)
        assert main.get_fields_text(note, ("Front",)) == expected


class TestCopyContent:
    """Preserve multiline text and avoid replacing clipboard contents with blank output."""

    @pytest.mark.parametrize(
        ("activated", "front", "expected"),
        [
            (True, "<b>日本語</b>", "日本語"),
            (True, "one<br>two", "one\ntwo"),
            (True, "one<br>", "one\n"),
            (True, "A &amp;amp; B", "A &amp; B"),
            (True, "", None),
            (True, "<b></b>", None),
            (True, '<img src="picture.jpg">', None),
            (True, "[sound:audio.mp3]", None),
            (True, "one[sound:audio.mp3]<br>two", "one\ntwo"),
            (True, "<br><br>", None),
            (True, "&nbsp;", None),
            (False, "text", None),
        ],
    )
    def test_copy(
        self,
        no_anki_config: AutoCopyConfig,
        anki_collection: Collection,
        activated: bool,
        front: str,
        expected: str | None,
    ) -> None:
        """Copy real Qt conversion output only when enabled and meaningful text exists."""
        no_anki_config.activated = activated
        no_anki_config.fields = ["Front"]
        controller = main.AutoCopy(no_anki_config)
        note = make_note(anki_collection, front=front)
        with patch.object(main, "copy_to_clipboard", autospec=True) as copy:
            controller.copy_content(note)
        if expected is None:
            copy.assert_not_called()
        else:
            copy.assert_called_once_with(expected)

    @pytest.mark.parametrize(
        ("front", "back", "expected"),
        [
            ("one<br>two", "three<br>four", "one\ntwo\nthree\nfour"),
            ("", "", "keep this text"),
            ('<img src="one.jpg">', '<img src="two.jpg">', "keep this text"),
            ("[sound:one.mp3]", "[sound:two.ogg]", "keep this text"),
            ('<img src="one.jpg">', "[sound:two.ogg]", "keep this text"),
            ("one[sound:one.mp3]<br>two", "[sound:two.ogg]three", "one\ntwo\nthree"),
            ("<br><br>", "&nbsp;", "keep this text"),
            ('<img src="one.jpg">', "back", "\nback"),
            ("front", '<img src="two.jpg">', "front\n"),
        ],
    )
    def test_multifield_clipboard(
        self,
        qapp: QApplication,
        isolated_clipboard: None,
        no_anki_config: AutoCopyConfig,
        anki_collection: Collection,
        front: str,
        back: str,
        expected: str,
    ) -> None:
        """Keep existing clipboard text after blank conversion and retain meaningful field boundaries."""
        no_anki_config.activated = True
        no_anki_config.fields = ["Front", "Back"]
        clipboard = qapp.clipboard()
        assert clipboard is not None
        clipboard.setText("keep this text")
        main.AutoCopy(no_anki_config).copy_content(make_note(anki_collection, front=front, back=back))
        assert clipboard.text() == expected

    @pytest.mark.parametrize("enabled", [True, False])
    def test_event_gate(self, no_anki_config: AutoCopyConfig, anki_collection: Collection, enabled: bool) -> None:
        """Read current configuration on every event, not a startup snapshot."""
        controller = main.AutoCopy(no_anki_config)
        no_anki_config["on_show_question"] = enabled
        note = make_note(anki_collection)
        with patch.object(controller, "copy_content", autospec=True) as copy:
            controller.on_change(note, "on_show_question")
        assert copy.call_args_list == ([((note,), {})] if enabled else [])

    @pytest.mark.parametrize("text", ["日本語", "first\nsecond"])
    def test_clipboard_round_trip(self, qapp: QApplication, isolated_clipboard: None, text: str) -> None:
        """Verify the low-level writer uses the real system clipboard mode."""
        main.copy_to_clipboard(text)
        clipboard = qapp.clipboard()
        assert clipboard is not None
        assert clipboard.text() == text

    def test_unavailable_clipboard(self) -> None:
        """Ignore unavailable clipboards without attempting a write or raising an exception."""
        with patch.object(main.QApplication, "clipboard", return_value=None) as clipboard:
            main.copy_to_clipboard("text")
        clipboard.assert_called_once_with()


class TestEditor:
    """Protect legacy and new editor behavior during callback ownership changes."""

    @pytest.mark.parametrize("new_editor_available", [False, True], ids=["older-anki", "current-anki"])
    def test_compatible_import(
        self, monkeypatch: pytest.MonkeyPatch, anki_collection: Collection, new_editor_available: bool
    ) -> None:
        """Keep legacy editor support when Anki does not export NewEditor."""
        try:
            with monkeypatch.context() as context:
                if not new_editor_available:
                    context.delattr(aqt.editor, "NewEditor")
                importlib.reload(main)
                assert main.NewEditor is (NewEditor if new_editor_available else Editor)
                assert main.get_editor_note(make_editor(anki_collection)) is None
        finally:
            # Restore real annotations before later tests exercise the newer editor class.
            importlib.reload(main)

    @pytest.mark.parametrize("new_editor", [False, True], ids=["legacy", "new"])
    @pytest.mark.parametrize("has_note", [False, True], ids=["empty", "saved"])
    def test_resolve_note(self, anki_collection: Collection, new_editor: bool, has_note: bool) -> None:
        """Resolve a saved note by object or ID without requiring an Anki window."""
        note = make_note(anki_collection)
        deck_id = anki_collection.decks.id("Default")
        assert deck_id is not None
        anki_collection.add_note(note, deck_id)
        editor = make_editor(
            anki_collection,
            note=note if has_note else None,
            nid=note.id if has_note else None,
            new_editor=new_editor,
        )
        result = main.get_editor_note(editor)
        assert (result.id if result else None) == (note.id if has_note else None)

    @pytest.mark.parametrize(("enabled", "has_note"), [(False, True), (True, True), (True, False)])
    @pytest.mark.parametrize("new_editor", [False, True], ids=["legacy", "new"])
    def test_callback(
        self,
        no_anki_config: AutoCopyConfig,
        anki_collection: Collection,
        enabled: bool,
        has_note: bool,
        new_editor: bool,
    ) -> None:
        """Skip note resolution when disabled and dispatch only resolved notes."""
        no_anki_config["on_editor_load_note"] = enabled
        controller = main.AutoCopy(no_anki_config)
        note = make_note(anki_collection)
        editor = make_editor(anki_collection, new_editor=new_editor)
        with patch.object(main, "get_editor_note", return_value=note if has_note else None) as resolve:
            with patch.object(controller, "on_change", autospec=True) as change:
                controller.on_editor_load_note(editor)
        assert resolve.call_args_list == ([((editor,), {})] if enabled else [])
        assert change.call_args_list == ([((note, "on_editor_load_note"), {})] if enabled and has_note else [])


class TestHooks:
    """Verify hook registration, routing, and retained controller ownership."""

    @pytest.mark.parametrize(
        ("hook_name", "method_name"),
        [
            ("reviewer_did_show_question", "on_show_question"),
            ("reviewer_did_show_answer", "on_show_answer"),
            ("browser_did_change_row", "on_select_note"),
            ("editor_did_load_note", "on_editor_load_note"),
        ],
    )
    def test_registration(self, no_anki_config: AutoCopyConfig, hook_name: str, method_name: str) -> None:
        """Invoke registered callbacks to verify closures forward to the correct controller method."""
        controller = main.AutoCopy(no_anki_config)
        argument_type = (
            Card if hook_name.startswith("reviewer") else Browser if method_name == "on_select_note" else Editor
        )
        argument = create_autospec(argument_type, instance=True)
        # Inspect observable routing instead of requiring closures to look like bound methods.
        with patch.object(controller, method_name, autospec=True) as callback:
            with patch.object(main, "gui_hooks", autospec=True) as hooks:
                controller.setup()
            append = getattr(hooks, hook_name).append
            append.assert_called_once()
            append.call_args.args[0](argument)
        callback.assert_called_once_with(argument)

    @pytest.mark.parametrize(
        ("method_name", "state"), [("on_show_question", "on_show_question"), ("on_show_answer", "on_show_answer")]
    )
    def test_reviewer(
        self, no_anki_config: AutoCopyConfig, anki_collection: Collection, method_name: str, state: str
    ) -> None:
        """Forward the reviewer's card note and event name."""
        controller = main.AutoCopy(no_anki_config)
        note = make_note(anki_collection)
        card = create_autospec(Card, instance=True)
        card.note.return_value = note
        with patch.object(controller, "on_change", autospec=True) as change:
            getattr(controller, method_name)(card)
        change.assert_called_once_with(note, state)

    @pytest.mark.parametrize("has_card", [True, False])
    def test_browser(self, no_anki_config: AutoCopyConfig, anki_collection: Collection, has_card: bool) -> None:
        """Ignore empty Browser selections and forward selected notes."""
        controller = main.AutoCopy(no_anki_config)
        note = make_note(anki_collection)
        browser = create_autospec(Browser, instance=True)
        card = create_autospec(Card, instance=True)
        card.note.return_value = note
        browser.current_card = card if has_card else None
        with patch.object(controller, "on_change", autospec=True) as change:
            controller.on_select_note(browser)
        assert change.call_args_list == ([((note, "on_select_note"), {})] if has_card else [])

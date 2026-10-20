# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import create_autospec

from anki.collection import Collection
from anki.notes import Note
from aqt import AnkiQt
from aqt.browser import Browser
from aqt.editor import Editor, NewEditor
from aqt.forms.browser import Ui_Dialog
from aqt.qt import QComboBox
from beartype import beartype


@beartype
def make_note(collection: Collection, *, front: str = "front", back: str = "back") -> Note:
    """Create an unsaved note through a real collection's supported API."""
    model = collection.models.by_name("Basic")
    assert model is not None
    note = collection.new_note(model)
    note["Front"] = front
    note["Back"] = back
    return note


@beartype
def make_editor(
    collection: Collection, *, note: Note | None = None, nid: int | None = None, new_editor: bool = False
) -> Editor | NewEditor:
    """Autospec the real editor class so runtime type checks exercise both Anki APIs."""
    editor = create_autospec(NewEditor if new_editor else Editor, instance=True)
    # NewEditor has no note attribute. Do not disguise a legacy mock as the newer class.
    if new_editor:
        editor.nid = nid
    else:
        editor.note = note
    editor.mw = create_autospec(AnkiQt, instance=True)
    editor.mw.col = collection
    return editor


@beartype
def make_search_browser(*, legacy: bool) -> Browser:
    """Mock the Browser boundary with a real editable search widget and explicit API version."""
    browser = create_autospec(Browser, instance=True)
    browser.form = create_autospec(Ui_Dialog, instance=True)
    browser.form.searchEdit = QComboBox()
    browser.form.searchEdit.setEditable(True)
    if legacy:
        browser.onSearch = create_autospec(Browser, instance=True).onSearchActivated
    else:
        del browser.onSearch
    return browser

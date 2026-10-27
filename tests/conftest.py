# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
import pathlib
import sys
import traceback
from collections.abc import Iterator

import anki.lang
import pytest
from anki.collection import Collection
from aqt.qt import QApplication
from beartype import beartype

from autocopy import config
from playground.no_anki_config import NoAnkiConfigView


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Runtime-check the arguments and return values of collected test functions."""
    for item in items:
        if isinstance(item, pytest.Function):
            item.obj = beartype(item.obj)


@pytest.fixture(autouse=True)
def no_qt_callback_errors() -> Iterator[None]:
    """Fail with full tracebacks when Qt reports an unhandled Python callback exception."""
    errors: list[str] = []
    # Keep our hook independent of test monkeypatch teardown and avoid retaining traceback frames.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            sys,
            "excepthook",
            lambda kind, error, tb: errors.append("".join(traceback.format_exception(kind, error, tb))),
        )
        yield
        if errors:
            pytest.fail("Unhandled Qt callback exceptions:\n" + "\n".join(errors), pytrace=False)


@pytest.fixture(scope="session", autouse=True)
def qt_offscreen_platform() -> None:
    """
    Force Qt to run without a real display so widget tests work in headless CI.
    https://github.com/Ajatt-Tools/lancet/blob/a306fd1774f2b3a70a0f836bab1135d66f4741f2/tests/conftest.py#L22
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def qapp(qt_offscreen_platform: None) -> QApplication:
    """Ensure a QApplication exists for widget tests.

    A program name must be present in argv because QtWebEngine aborts
    when QApplication is created with an empty argument list.

    https://github.com/Ajatt-Tools/lancet/blob/a306fd1774f2b3a70a0f836bab1135d66f4741f2/tests/conftest.py#L28
    """
    match instance := QApplication.instance():
        case None:
            return QApplication(["pytest"])  # argv can't be empty
        case QApplication():
            return instance
        case _:
            raise RuntimeError("A QCoreApplication already exists. Widget tests require QApplication")


@pytest.fixture
def anki_collection(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Collection]:
    """Open an isolated Anki collection with its own text-processing backend."""
    collection = Collection(str(tmp_path / "collection.anki2"))
    # Anki's HTML helpers use this backend outside the full application too.
    monkeypatch.setattr(anki.lang, "current_i18n", collection._backend)
    try:
        yield collection
    finally:
        collection.close()


@pytest.fixture
def clear_config_cache() -> Iterator[None]:
    """Isolate tests of the real configuration accessor without resetting injected dependencies."""
    # Ordinary controller tests inject fresh configuration and never populate this cache.
    config.get_global_config.cache_clear()
    yield
    config.get_global_config.cache_clear()


@pytest.fixture
def no_anki_config() -> NoAnkiConfigView:
    """Provide fresh standalone configuration, as in AJT_Media_Converter."""
    return NoAnkiConfigView()


@pytest.fixture
def isolated_clipboard(qapp: QApplication) -> Iterator[None]:
    """Restore clipboard text after tests that interact with the real Qt clipboard."""
    clipboard = qapp.clipboard()
    assert clipboard is not None, "A QApplication clipboard must be available."
    previous_text = clipboard.text()
    try:
        yield
    finally:
        clipboard.setText(previous_text)

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import importlib
from contextlib import ExitStack
from unittest.mock import Mock, call, create_autospec, patch

import aqt
import pytest
from aqt import AnkiQt

import autocopy
from autocopy import clipboard_monitor, main, menus
from autocopy.config import AutoCopyConfig


class TestStartup:
    """Verify startup boundaries and explicit main-window controller ownership."""

    def test_start_order(self) -> None:
        """Initialize each component in the same order as the existing startup code."""
        calls = Mock()
        with patch.object(main, "init", autospec=True) as copying:
            with patch.object(menus, "init", autospec=True) as menu:
                with patch.object(clipboard_monitor, "init", autospec=True) as monitoring:
                    # One mock call sequence observes ordering across all three entry points.
                    calls.attach_mock(copying, "copying")
                    calls.attach_mock(menu, "menus")
                    calls.attach_mock(monitoring, "monitor")
                    autocopy.start_addon()
        assert calls.mock_calls == [call.copying(), call.menus(), call.monitor()]

    @pytest.mark.parametrize("has_main_window", [False, True])
    def test_import_does_not_start_under_pytest(self, monkeypatch: pytest.MonkeyPatch, has_main_window: bool) -> None:
        """Skip startup during pytest collection, including when a main window is available."""
        with monkeypatch.context() as context:
            context.setattr(aqt, "mw", create_autospec(AnkiQt, instance=True) if has_main_window else None)
            with ExitStack() as stack:
                entry_points = [
                    stack.enter_context(patch.object(module, "init")) for module in (main, menus, clipboard_monitor)
                ]
                importlib.reload(autocopy)
                for entry_point in entry_points:
                    entry_point.assert_not_called()
        importlib.reload(autocopy)

    @pytest.mark.parametrize("component", ["main", "clipboard_monitor"])
    def test_controller_composition(
        self, no_anki_config: AutoCopyConfig, component: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inject the exact shared config and retain the constructed controller on mw."""
        module = main if component == "main" else clipboard_monitor
        controller_type = "AutoCopy" if component == "main" else "ClipboardMonitor"
        attribute = "_ajt__autocopy_events" if component == "main" else "_ajt__autocopy_clipboard_monitor"
        window = create_autospec(AnkiQt, instance=True)
        # Patch the name read by init(), including modules that import mw directly.
        monkeypatch.setattr(module, "mw", window)
        with patch.object(module, "get_global_config", return_value=no_anki_config) as get_config:
            with patch.object(module, controller_type, autospec=True) as constructor:
                module.init()
        get_config.assert_called_once_with()
        constructor.assert_called_once_with(no_anki_config)
        constructor.return_value.setup.assert_called_once_with()
        assert getattr(window, attribute) is constructor.return_value

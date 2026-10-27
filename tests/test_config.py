# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import patch

import pytest

from autocopy import config
from autocopy.config import AutoCopyConfig
from playground.no_anki_config import NoAnkiConfigView


@pytest.mark.usefixtures("clear_config_cache")
class TestGlobalConfig:
    """Verify lazy shared configuration and retry behavior after initialization failures."""

    @pytest.mark.parametrize("access_count", [1, 3])
    def test_cached_construction(self, no_anki_config: AutoCopyConfig, access_count: int) -> None:
        """Construct exactly once, on first access rather than while importing the module."""
        with patch.object(config, "AutoCopyConfig", autospec=True, return_value=no_anki_config) as constructor:
            assert config.get_global_config.cache_info().currsize == 0
            constructor.assert_not_called()
            results = [config.get_global_config() for _ in range(access_count)]
        assert all(result is no_anki_config for result in results)
        constructor.assert_called_once_with()

    @pytest.mark.parametrize("error", [RuntimeError, AssertionError])
    def test_failed_initialization_is_not_cached(self, no_anki_config: AutoCopyConfig, error: type[Exception]) -> None:
        """A caller may retry after the Anki configuration boundary becomes available."""
        with patch.object(
            config, "AutoCopyConfig", autospec=True, side_effect=[error("not ready"), no_anki_config]
        ) as constructor:
            with pytest.raises(error, match="not ready"):
                config.get_global_config()
            assert config.get_global_config() is no_anki_config
        assert constructor.call_count == 2


class TestStandaloneConfig:
    """Protect fresh standalone settings and their no-write behavior."""

    @pytest.mark.parametrize("activated", [True, False])
    def test_isolation(self, no_anki_config: NoAnkiConfigView, activated: bool) -> None:
        """Editing one instance must not change its defaults or another instance."""
        no_anki_config.activated = activated
        no_anki_config.fields = ["Front"]
        other = NoAnkiConfigView()
        assert no_anki_config.default_config["fields"] == ["SentKanji", "VocabKanji", "VocabDef"]
        assert other.fields == ["SentKanji", "VocabKanji", "VocabDef"]
        assert other.activated is True
        assert no_anki_config.fields == ["Front"]
        assert no_anki_config.activated == activated

    def test_ignored_writes(self, no_anki_config: NoAnkiConfigView) -> None:
        """Standalone writes never reach Anki's configuration persistence boundary."""
        with patch("autocopy.ajt_common.addon_config.write_config", autospec=True) as write:
            no_anki_config.write_config()
        write.assert_not_called()

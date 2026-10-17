# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import copy
import json
import pathlib

from autocopy.config import AutoCopyConfig


class NoAnkiConfigView(AutoCopyConfig):
    """Load default configuration without accessing a running Anki instance."""

    def _set_underlying_dicts(self) -> None:
        """Initialize detached defaults and editable settings for each standalone instance."""
        config_path = pathlib.Path(__file__).parent.parent / "autocopy" / "config.json"
        self._default_config = json.loads(config_path.read_text(encoding="utf-8"))
        # Editing standalone settings must not change defaults or another test's configuration.
        self._config = copy.deepcopy(self._default_config)

    def write_config(self) -> None:
        """Ignore persistence requests outside Anki so tests never write user settings."""

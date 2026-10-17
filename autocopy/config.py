# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools

from .ajt_common.addon_config import AddonConfigManager


class AutoCopyConfig(AddonConfigManager):
    @property
    def activated(self) -> bool:
        return self["activated"]

    @activated.setter
    def activated(self, value: bool) -> None:
        self["activated"] = bool(value)

    @property
    def fields(self) -> list[str]:
        return self["fields"]

    @fields.setter
    def fields(self, value: list[str]) -> None:
        self["fields"] = value

    @property
    def clipboard_monitor(self) -> bool:
        return self["clipboard_monitor"]


@functools.cache
def get_global_config() -> AutoCopyConfig:
    """Return the shared configuration, initializing it on first use in Anki."""
    # Delay access to Anki's add-on manager until a caller actually needs configuration.
    return AutoCopyConfig()

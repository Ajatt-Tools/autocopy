# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from .ajt_common.addon_config import AddonConfigManager


class AutoCopyConfig(AddonConfigManager):
    @property
    def activated(self) -> bool:
        return self['activated']

    @activated.setter
    def activated(self, value: bool):
        self['activated'] = bool(value)

    @property
    def fields(self) -> list[str]:
        return self['fields']

    @fields.setter
    def fields(self, value: list[str]):
        self['fields'] = value

    @property
    def clipboard_monitor(self) -> bool:
        return self['clipboard_monitor']


config = AutoCopyConfig()

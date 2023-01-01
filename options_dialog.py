# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *
from aqt.utils import saveGeom, restoreGeom

from .ajt_common.about_menu import tweak_window
from .config import AutoCopyConfig


def as_label(config_key: str) -> str:
    return config_key.replace('_', ' ').capitalize()


ADDON_NAME = "Autocopy"


class AutocopySettingsDialog(QDialog):
    name = "ajt__autocopy_settings_dialog"

    def __init__(self, config: AutoCopyConfig, parent: QWidget = None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.setWindowTitle(f"{ADDON_NAME} Settings")
        self._config = config
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._checkboxes = {key: QCheckBox(as_label(key)) for key in self._config.bool_keys()}
        self._fields_edit = QLineEdit()
        self.setLayout(self.make_layout())
        self.setup_logic()
        self.set_initial_values()
        tweak_window(self)
        restoreGeom(self, self.name)

    def make_layout(self) -> QLayout:
        layout = QVBoxLayout()
        layout.addLayout(form := QFormLayout())
        form.addRow("Fields", self._fields_edit)
        for checkbox in self._checkboxes.values():
            layout.addWidget(checkbox)
        layout.addStretch(1)
        layout.addWidget(self._button_box)
        return layout

    def set_initial_values(self):
        for key, checkbox in self._checkboxes.items():
            checkbox.setChecked(self._config[key])
        self._fields_edit.setText(','.join(self._config.fields))

    def setup_logic(self):
        qconnect(self._button_box.accepted, self.accept)
        qconnect(self._button_box.rejected, self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setFocus()

    def done(self, *args, **kwargs) -> None:
        saveGeom(self, self.name)
        return super().done(*args, **kwargs)

    def accept(self) -> None:
        for key, checkbox in self._checkboxes.items():
            self._config[key] = checkbox.isChecked()
        self._config['fields'] = self._fields_edit.text().split(',')
        self._config.write_config()
        return super().accept()

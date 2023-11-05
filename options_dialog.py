# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *
from aqt.utils import saveGeom, restoreGeom

from .ajt_common.about_menu import tweak_window
from .ajt_common.anki_field_selector import AnkiFieldSelector
from .config import AutoCopyConfig

ADDON_NAME = "Autocopy"
TRANSLATE = {
    "activated": f"activate {ADDON_NAME}",
    "on_show_question": "copy when question is shown",
    "on_show_answer": "copy when answer is shown",
    "on_editor_load_note": "copy when Editor loads a note",
    "on_select_note": "copy when a note is selected",
}


def as_label(config_key: str) -> str:
    return TRANSLATE.get(config_key, config_key).replace('_', ' ').capitalize()


class FieldList(QWidget):
    """Widget that holds a list of Anki fields and lets the user add, remove and reposition them."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._field_selector = AnkiFieldSelector()
        self._field_list = QListWidget()
        self._add_button = QPushButton("Add")
        self._remove_button = QPushButton("Remove")
        self.setLayout(self._create_layout())
        self._connect_buttons()
        self._adjust_widgets()
        self._add_tooltips()

    def _create_layout(self):
        layout = QVBoxLayout()

        layout.addLayout(upper := QHBoxLayout())
        upper.addWidget(QLabel("New field"))
        upper.addWidget(self._field_selector)
        upper.addWidget(self._add_button)

        layout.addLayout(lower := QHBoxLayout())
        lower.addWidget(self._field_list)

        lower.addLayout(buttons := QVBoxLayout())
        buttons.addWidget(self._remove_button)
        buttons.addStretch(1)

        return layout

    def _adjust_widgets(self):
        self._field_selector.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding,
            QSizePolicy.Policy.Expanding)  # horizontal, vertical
        self._field_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

    def _connect_buttons(self):
        qconnect(self._add_button.clicked, self._append_field)
        qconnect(self._remove_button.clicked, self._remove_current)

    def _append_field(self):
        self._field_list.addItem(self._field_selector.currentText())

    def _remove_current(self):
        if (current := self._field_list.currentItem()) and current.isSelected():
            self._field_list.takeItem(self._field_list.currentRow())

    def set_fields(self, fields: list[str]):
        self._field_list.clear()
        self._field_list.addItems(fields)

    def current_fields(self) -> list[str]:
        return [
            self._field_list.item(idx).text()
            for idx in range(self._field_list.count())
        ]

    def _add_tooltips(self):
        self._add_button.setToolTip("Add a new field to the list.")
        self._remove_button.setToolTip("Remove selected field.")


class AutocopySettingsDialog(QDialog):
    name = "ajt__autocopy_settings_dialog"

    def __init__(self, config: AutoCopyConfig, parent: QWidget = None):
        super().__init__(parent)
        self.setMinimumSize(320, 320)
        self.setWindowTitle(f"{ADDON_NAME} Settings")
        self._config = config
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._checkboxes = {key: QCheckBox(as_label(key)) for key in self._config.bool_keys()}
        self._fields_edit = FieldList()
        self.setLayout(self._make_layout())
        self._setup_logic()
        self._set_initial_values()
        tweak_window(self)
        restoreGeom(self, self.name)
        self._add_tooltips()

    def _make_layout(self) -> QLayout:
        layout = QVBoxLayout()
        layout.addWidget(self._fields_edit)
        for checkbox in self._checkboxes.values():
            layout.addWidget(checkbox)
        layout.addStretch(1)
        layout.addWidget(self._button_box)
        return layout

    def _set_initial_values(self):
        for key, checkbox in self._checkboxes.items():
            checkbox.setChecked(self._config[key])
        self._fields_edit.set_fields(self._config.fields)

    def _setup_logic(self):
        qconnect(self._button_box.accepted, self.accept)
        qconnect(self._button_box.rejected, self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setFocus()

    def _add_tooltips(self):
        self._checkboxes["clipboard_monitor"].setToolTip(
            "Open the Anki Browser with the text in the clipboard\n"
            "when the clipboard's content changes."
        )

    def done(self, *args, **kwargs) -> None:
        saveGeom(self, self.name)
        return super().done(*args, **kwargs)

    def accept(self) -> None:
        for key, checkbox in self._checkboxes.items():
            self._config[key] = checkbox.isChecked()
        self._config.fields = self._fields_edit.current_fields()
        self._config.write_config()
        return super().accept()

"""
Widgets for node items from beams.tree_config.action
"""

from qtpy import QtWidgets

from beams.tree_config.action import SetPVActionItem
from beams.widgets.base import EmbeddedNodeWidget


class SetPVActionWidget(EmbeddedNodeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.form_layout = QtWidgets.QFormLayout()
        self.setLayout(self.form_layout)

        self.pv_edit = QtWidgets.QLineEdit()
        self.form_layout.addRow("EPICS PV:", self.pv_edit)
        self.value_edit = QtWidgets.QLineEdit()
        self.form_layout.addRow("Value:", self.value_edit)

        self.loop_period_edit = QtWidgets.QDoubleSpinBox()
        self.form_layout.addRow("Loop Period:", self.loop_period_edit)

    def update_item(self, item: SetPVActionItem):
        item.pv = self.pv_edit.text()
        item.value = self.value_edit.text()  # TODO: deal with types
        item.loop_period_sec = self.loop_period_edit.value()

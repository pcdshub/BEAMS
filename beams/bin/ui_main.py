import qtpynodeeditor as nodeeditor
from qtpy.QtWidgets import QApplication
from qtpynodeeditor.node_geometry import LayoutDirection

from beams.widgets.models import RootNodeModel, add_items_to_registry


def main(*args, **kwargs):
    app = QApplication([])
    registry = nodeeditor.DataModelRegistry()

    my_style = nodeeditor.StyleCollection()
    my_style.node.layout_direction = LayoutDirection.VERTICAL

    add_items_to_registry(registry, style=my_style)
    registry.register_model(RootNodeModel, style=my_style, category="Root")
    scene = nodeeditor.FlowScene(style=my_style, registry=registry)

    view = nodeeditor.FlowView(scene)
    view.setWindowTitle("Beams Behavior Tree Builder")
    view.resize(800, 600)
    view.show()

    app.exec_()

import json
from pathlib import Path

from pydm import Display
from pydm.widgets.line_edit import PyDMLineEdit

from beams.bin.gen_test_ioc_main import walk_dict_pvs


class App(Display):

    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        filepath = Path(__file__).parent / "mfx_tree.json"
        with open(filepath, "r") as fd:
            deser = json.load(fd)
        # Preserve order, ignore duplicates
        seen = set()
        for pvname in (pv for pv in walk_dict_pvs(deser) if not (pv in seen or seen.add(pv))):
            self.ui.scroll.widget().layout().addRow(pvname, PyDMLineEdit(init_channel=f"ca://{pvname}"))

    def ui_filename(self):
        return 'mfx_tree_ui.ui'

import json
from pathlib import Path

from ophyd.signal import EpicsSignal
from pydm import Display
from typhos.widgets import determine_widget_type

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
            cls, kwargs = determine_widget_type(EpicsSignal(pvname))
            widget = cls(**kwargs)
            self.ui.scroll.widget().layout().addRow(pvname, widget)

    def ui_filename(self):
        return 'mfx_tree_ui.ui'

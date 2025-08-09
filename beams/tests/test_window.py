from pytestqt.qtbot import QtBot

from beams.widgets.window import MainWindow


def test_main_window(qtbot: QtBot):
    window = MainWindow()
    qtbot.add_widget(window)

    # basic introspection for now.  This may change in the future
    # opens with an edit tab open
    assert window.tab_widget.count() == 1

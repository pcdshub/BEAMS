from qtpy.QtWidgets import QApplication

from beams.widgets.window import MainWindow


def main(*args, **kwargs):
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()

    app.exec_()

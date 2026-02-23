import numpy
import pytest
import sys
from icepaposc.window_main import WindowMain
from PyQt5 import QtWidgets, Qt, QtCore, uic, QtGui
from PyQt5.QtWidgets import QFileDialog, QShortcut, QApplication
from icepaposc.tests.FIcePAPController import FIcePAPController

HOST = "w-kitslab-icepap-21"
PORT = 5000
TIMEOUT = 3


@pytest.fixture
def app(qtbot):
    # Instantiate WindowMain with a signal set file so it loads predefined curves.
    icepap_controller = FIcePAPController(HOST, PORT, TIMEOUT, auto_axes=True)
    win = WindowMain(
        HOST,
        PORT,
        TIMEOUT,
        [],
        2,
        "./icepaposc/tests/SignalSet.lst",
        "",
        # "",
        icepap_controller=icepap_controller,
    )
    qtbot.addWidget(win)
    return win


def test_signal_set(app):
    # Signal set file should create the expected number of curves.
    assert len(app.curve_items) == 5

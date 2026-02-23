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
    # Provide a small signal list to exercise subscription wiring.
    signal_list = [
        "1:PosAxis:1",
        "2:EncTgtenc:2",
        "3:DifAxTgtenc:3",
    ]
    # Use a fake controller so we can instantiate the UI without hardware.
    icepap_controller = FIcePAPController(HOST, PORT, TIMEOUT, auto_axes=True)
    win = WindowMain(
        HOST,
        PORT,
        TIMEOUT,
        signal_list,
        2,
        # "",
        "",
        "",
        icepap_controller=icepap_controller,
    )
    qtbot.addWidget(win)
    return win


def test_signal_list(app):
    # Each signal should create a curve, a subscription, and a UI list entry.
    assert len(app.curve_items) == 3
    assert len(app.collector.channels_subscribed.keys()) == 3
    assert app.ui.lvActiveSig.count() == 3

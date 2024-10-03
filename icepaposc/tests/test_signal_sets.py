
import numpy
import pytest
import sys
from icepaposc.window_main import WindowMain
from PyQt5 import QtWidgets, Qt, QtCore, uic, QtGui
from PyQt5.QtWidgets import QFileDialog, QShortcut, QApplication

@pytest.fixture
def app(qtbot):
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, [],
                     2, "./tests/SignalSet.lst", "", "")
    qtbot.addWidget(win)
    return win

def test_signal_set(app):
    assert len(app.curve_items) == 6

'''

def test_main():
    # args = get_parser().parse_args()
    # print(args)

    app = QApplication(sys.argv)
    # win = WindowMain(args.host, args.port, args.timeout, args.sig,
    #                 args.axis, args.sigset, args.corr, args.yrange)
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, [],
    ----                 1, "", "", "")
    sig_set = [
        '1:PosAxis:1',
        '1:PosAbsenc:1',
        '1:PosInpos:1',
        '1:PosEncin:1',
    ]
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_set,
                     1, "", "", "")
    axis_aux = 2
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_set,
                     axis_aux, "", "", "")
    sigset_file = "sigset.lst"
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_set,
                     1, sigset_file, "", "")
    sigset_file = "sigset.lst"
    corr_factors_test = [2, 1000, 3 10000]
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_set,
                     1, sigset_file, corr_factors_test, "")
    #---
    win.show()
    sys.exit(app.exec_())
'''


if __name__ == "__main__":
    print("python -i -m icepaosc.test_window_main")
    # get icepap_client (python 3.11) add pytest and pytest-qt with conda or pip
    # pytest ./test_window_main.py --log-level=DEBUG --verbosity=10
    test_main()



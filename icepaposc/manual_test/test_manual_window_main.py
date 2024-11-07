import numpy
import pytest
import sys
from icepaposc.window_main import WindowMain
from PyQt5 import QtWidgets, Qt, QtCore, uic, QtGui
from PyQt5.QtWidgets import QFileDialog, QShortcut, QApplication


def test_main():
    # args = get_parser().parse_args()
    # print(args)

    app = QApplication(sys.argv)
    # win = WindowMain(args.host, args.port, args.timeout, args.sig,
    #                 args.axis, args.sigset, args.corr, args.yrange)
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, [],
                         1, "", "", "")
    win.show()
    # sys.exit(app.exec_())
    app.exec_()

    sig_list = [
        '1:PosAxis:1',
        '1:PosAbsenc:2',
        '1:PosInpos:3',
        '1:PosEncin:4',
    ]
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_list,
                     1, "", "", "")
    win.show()
    app.exec_()

    axis_aux = 2
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_list,
                     axis_aux, "", "", "")
    win.show()
    app.exec_()

    sigset_file = "./test/SignalSet.lst"
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, "",
                     2, sigset_file, "", "")
    win.show()
    app.exec_()

    sigset_file = "./test/SignalSet.lst"
    corr_factors_test = [2, 1000, 3, 10000]
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, sig_list,
                     1, sigset_file, corr_factors_test, "")
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    print("python -i -m icepaosc.test_manual_window_main")
    test_main()



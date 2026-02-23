import numpy
import pytest
import sys
from icepaposc.window_main import WindowMain
from icepaposc.csvloader import load_csv_items
from PyQt5 import QtWidgets, Qt, QtCore, uic, QtGui
from PyQt5.QtWidgets import QFileDialog, QShortcut, QApplication
from icepaposc.tests.FIcePAPController import FIcePAPController

from PyQt5.QtWidgets import QApplication, QMessageBox
import sys


def manual_test_prompt(wtitle, wmessage):
    """
    Display a message box before running tests that require manual interaction.
    """
    app = QApplication.instance() or QApplication(sys.argv)

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle(wtitle)
    msg.setText(wmessage)
    msg.setStandardButtons(
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
    )

    result = msg.exec()

    if result == QMessageBox.StandardButton.Cancel:
        pytest.skip("Manual tests skipped by user.")


def test_main():
    # args = get_parser().parse_args()
    # print(args)
    wtitle = "Basic signal group and estimation tests"
    wmessage = "\
        In this order: \n\
        - Press the closed loop signals button \n\
        - Ctrl+t and Ctrl+y to set tSCALE and ySCALE modes \n\
        - Press the estimate button \n\n\
        Finally check the random estimation updates \
        "
    print(wmessage)
    manual_test_prompt(wtitle, wmessage)
    app = QApplication(sys.argv)
    icepap_controller = FIcePAPController(
        "w-kitslab-icepap-21", 5000, 3, auto_axes=True
    )
    # win = WindowMain(args.host, args.port, args.timeout, args.sig,
    #                 args.axis, args.sigset, args.corr, args.yrange)
    win = WindowMain(
        "w-kitslab-icepap-21",
        5000,
        3,
        [],
        1,
        # "",
        "",
        "",
        icepap_controller=icepap_controller,
    )
    win.show()
    # sys.exit(app.exec_())
    app.exec_()

    sig_list = [
        "1:PosAxis:1",
        "1:PosAbsenc:2",
        "1:PosInpos:3",
        "1:PosEncin:4",
    ]
    wtitle = "Command line signals tests"
    wmessage = "\
        In this order: \n\
        - Verify there are 4 signals \n\
        - In the Settings menu, enable autosave and select USER/.icepaposc folder\n\
        - Ctrl+t and Ctrl+y to set tSCALE and ySCALE modes \n\
        - Press the Pause button and change Ctrl+Y and Ctrl+T \n\n\
        Check after pressing Run again y and t axis state is coherent, and data is saved \
        "
    print(wmessage)
    manual_test_prompt(wtitle, wmessage)
    win = WindowMain(
        "w-kitslab-icepap-21",
        5000,
        3,
        sig_list,
        1,
        # "",
        "",
        "",
        icepap_controller=icepap_controller,
    )
    win.show()
    app.exec_()

    axis_aux = 2
    wtitle = "Command line signals tests 2"
    wmessage = "\
        In this order: \n\
        - Verify there are 4 signals but that driver 2 gets selected\n\
        - Ctrl+t and Ctrl+y to set tSCALE and ySCALE modes \n\
        - Check that offset and scale buttons work on Yn and X \n\n\
        Check after pressing Ctrl-t and Ctrl-y again state is coherent \
        "
    print(wmessage)
    manual_test_prompt(wtitle, wmessage)
    win = WindowMain(
        "w-kitslab-icepap-21",
        5000,
        3,
        sig_list,
        axis_aux,
        # "",
        "",
        "",
        icepap_controller=icepap_controller,
    )
    win.show()
    app.exec_()

    sigset_file = "./icepaposc/tests/SignalSet.lst"
    wtitle = "File loaded signals tests"
    wmessage = "\
        In this order: \n\
        - Verify there are 6 signals and black background \n\
        - Ctrl+t and Ctrl+y to set tSCALE and ySCALE modes \n\
        - Click in the data and move the curves around \n\
        - Use Signals menu to export and reimport signal sets \n\n\
        Check that after Ctrl+t and Ctrl-y again state is coherent\
        "
    print(wmessage)
    manual_test_prompt(wtitle, wmessage)
    win = WindowMain(
        "w-kitslab-icepap-21",
        5000,
        3,
        [],
        1,
        sigset_file,
        "",
        # "",
        icepap_controller=icepap_controller,
    )
    win.show()
    app.exec_()

    sigset_file = "./icepaposc/tests/SignalSet.lst"
    corr_factors_test = "2, 1000, 3, 10000"
    wtitle = "Corrector factors"
    wmessage = "\
        In this order: \n\
        - Verify there are 5 signals and black background \n\
        - Ctrl+t and Ctrl+y to set tSCALE and ySCALE modes \n\
        - Toggle Ctrl+u and check that POS* and ENC* signals change value \n\n\
        Check that after Ctrl+t and Ctrl-y again state is coherent \
        "
    print(wmessage)
    manual_test_prompt(wtitle, wmessage)
    win = WindowMain(
        "w-kitslab-icepap-21",
        5000,
        3,
        sig_list[1:],  # Dont repeat posaxis
        1,
        sigset_file,
        corr_factors_test,
        # "",
        icepap_controller=icepap_controller,
    )
    win.show()
    app.exec_()

    sigset_file = "./icepaposc/tests/SignalSet.lst"
    corr_factors_test = "2, 1000, 3, 10000"
    wtitle = "Sample rate, dump rate and save to file"
    wmessage = "\
        In this order: \n\
        - Verify there are 5 signals and black background \n\
        - Verify data is updated now every second \n\
        - Ctrl+t and Ctrl+y to set tSCALE and ySCALE modes \n\
        - Use Ctrl+i and Ctrl+o to set a filename and save to USER/.icepaposc folder \n\n\
        Check that the date in the file in the USER/.icepaposc folder is coherent \
        "
    print(wmessage)
    manual_test_prompt(wtitle, wmessage)
    win = WindowMain(
        "w-kitslab-icepap-21",
        5000,
        3,
        sig_list[1:],  # Dont repeat posaxis
        1,
        sigset_file,
        corr_factors_test,
        # "",
        icepap_controller=icepap_controller,
        sample_rate=100,
        dump_rate=10,
    )
    win.show()
    app.exec_()

    sigset_file = "./icepaposc/tests/SignalSet.lst"
    corr_factors_test = "2, 1000, 3, 10000"
    wtitle = "Sample rate, dump rate and save to file"
    wmessage = "\
        In this order: \n\
        - Verify there are 5 signals and black background \n\
        - Verify data is updated now every second \n\
        - Ctrl+t and Ctrl+y to set tSCALE and ySCALE modes \n\
        - Use Ctrl+i and Ctrl+o to set a filename and save to USER/.icepaposc folder \n\n\
        Check that the date in the file in the USER/.icepaposc folder is coherent \
        "
    print(wmessage)
    manual_test_prompt(wtitle, wmessage)
    win = WindowMain(
        "w-kitslab-icepap-21",
        5000,
        3,
        sig_list[1:],  # Dont repeat posaxis
        1,
        sigset_file,
        corr_factors_test,
        # "",
        icepap_controller=icepap_controller,
        sample_rate=100,
        dump_rate=10,
        # yrange="1",
    )
    win.show()
    sys.exit(app.exec_())

    # CSV mode manual test
    csv_fft = "./icepaposc/tests/data/csv_fft_sines.csv"
    wtitle = "CSV mode: FFT and Derivative"
    wmessage = "\
        In this order: \n\
        - Verify signals are listed in Active Signals list with colors \n\
        - Ctrl+Y toggles Y tiling \n\
        - Ctrl+F opens FFT tool; select all signals and save (Ctrl+O) \n\
        - Ctrl+D opens derivative tool; select all signals and save (Ctrl+O) \n\n\
        Check that saved CSV files exist and contain expected headers \
        "
    print(wmessage)
    manual_test_prompt(wtitle, wmessage)
    win = WindowMain(
        "csv",
        0,
        0,
        [],
        1,
        "",
        "",
        csv_mode=True,
        csv_items=load_csv_items(csv_fft),
        csv_axes=["Y1", "Y2", "Y3"],
    )
    win.show()
    app.exec_()

    csv_der = "./icepaposc/tests/data/csv_derivative_shapes.csv"
    wtitle = "CSV mode: Derivative (shapes)"
    wmessage = "\
        In this order: \n\
        - Verify 4 signals listed (zero, const, line, parab) \n\
        - Ctrl+D opens derivative tool; select all signals and save (Ctrl+O) \n\n\
        Check derivative CSV contains zero for zero/const signals \
        "
    print(wmessage)
    manual_test_prompt(wtitle, wmessage)
    win = WindowMain(
        "csv",
        0,
        0,
        [],
        1,
        "",
        "",
        csv_mode=True,
        csv_items=load_csv_items(csv_der),
        csv_axes=["Y1", "Y2", "Y3", "Y4"],
    )
    win.show()
    app.exec_()


if __name__ == "__main__":
    print("python -i -m icepaosc.test_manual_window_main")
    test_main()

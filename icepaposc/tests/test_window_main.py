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

NUM_CURVES_CLOSED_LOOP = 9
DATA_LEN_30 = 30
DATA_LEN_40 = 40
DATA_LEN_50 = 50
DATA_LEN_60 = 60
DATA_LEN_90 = 90


@pytest.fixture
def window(qtbot):
    # Factory fixture so each test can customize the window inputs.
    def create_window(
        siglist=[], selected_driver=1, sigset="", corr=""
    ):  # , yrange=""):
        # Use a fake controller to avoid connecting to real hardware.
        icepap_controller = FIcePAPController(HOST, PORT, TIMEOUT, auto_axes=True)
        win = WindowMain(
            HOST,
            PORT,
            TIMEOUT,
            siglist,
            selected_driver,
            sigset,
            corr,
            # yrange,
            icepap_controller=icepap_controller,
        )
        qtbot.addWidget(win)
        return win

    return create_window


@pytest.fixture
def app(window):
    # Default window instance for most tests.
    return window()


def test_initial_state(app):
    # Verify initial state before any UI actions.
    assert app.host == HOST
    assert len(app.curve_items) == 0
    assert not app._paused


def test_closed_loop_signals(app, qtbot):
    # Trigger closed-loop signals and ensure curves appear.
    app.ui.btnCLoop.click()
    assert len(app.curve_items) == NUM_CURVES_CLOSED_LOOP
    assert not app._paused
    # Wait for data acquisition to populate arrays.
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == DATA_LEN_30)
    # Validate y-scale mode and x-axis view range.
    yscale_mode_after_cloopbtn_tests(qtbot, app)
    assert app.last_now <= app.view_boxes[0].viewRange()[0][1]
    assert app.last_now >= app.view_boxes[0].viewRange()[0][0]


@pytest.mark.skip(reason="Temporarily disabled due to known y-tiling regression")
def test_ytiled_mode(app, qtbot):
    # Exercise y-tiling toggle and refresh logic (currently skipped).
    app.ui.btnCLoop.click()
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == DATA_LEN_60)
    assert app.view_boxes[0].state["autoRange"][1] == True
    last_yranges = []
    for i in range(0, 5):
        last_yranges.append(app.view_boxes[i].viewRange()[1])
    app.ui.btnResetY.click()
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == DATA_LEN_90)
    ytiled_mode_tests(qtbot, app, last_yranges)


def test_tiled(app, qtbot):
    # Full workflow: closed-loop signals -> update factors -> tile/un-tile.
    assert app.host == HOST
    app.ui.btnCLoop.click()
    assert not app._paused
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == DATA_LEN_30)
    # Update corrector factors through the UI widgets.
    ui_corr_factors = [1, 0, 1, 0]
    update_corrector_factors_ui(app, ui_corr_factors)
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == DATA_LEN_40)
    # Capture existing y-ranges before toggling tiling.
    last_yranges = []
    for i in range(0, 5):
        last_yranges.append(app.view_boxes[i].viewRange()[1])
    yscale_mode_after_cloopbtn_tests(qtbot, app)
    # Toggle to tiled mode and validate layout.
    app._toggle_y_autorange()
    qtbot.waitUntil(lambda: not app.ytiled_viewbox_next)
    ytiled_mode_tests(qtbot, app, last_yranges)
    # Toggle auto mode refresh and validate timer state.
    app._toggle_y_autorange()
    qtbot.waitUntil(lambda: app._y_tile_refresh_active)
    ytiled_mode_refresh_tests(qtbot, app)
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == DATA_LEN_50)


def yscale_mode_after_cloopbtn_tests(qtbot, app):
    # After CLoop, we expect auto-range Y and manual X (scope mode).
    assert app.ytiled_viewbox_next
    # check all yaxes except last one have autorange on
    for i in range(5):
        assert app.view_boxes[i].state["autoRange"][1] == True

    # check xaxis is panning (scope mode)
    assert app.view_boxes[0].state["autoRange"][0] == False
    assert app.ui.btnResetX.text() == "tSCALE"
    assert app.ui.btnResetY.text() == "ySCALE"


def ytiled_mode_tests(qtbot, app, last_yranges):
    # Validate state after switching to ytiled (stacked) mode.
    assert not app._paused
    assert not app.ytiled_viewbox_next
    assert app.ui.btnResetY.text() == "ySCALEa"

    # check all yaxes except last one have autorange off
    for i in range(5):
        assert app.view_boxes[i].state["autoRange"][1] == False

    # check xaxis is panning (scope mode)
    assert app.view_boxes[0].state["autoRange"][0] == False
    assert app.ui.btnResetX.text() == "tSCALE"
    assert app.last_now <= app.view_boxes[0].viewRange()[0][1]
    assert app.last_now >= app.view_boxes[0].viewRange()[0][0]

    # check in ytiled mode
    assert app.ytiled_viewbox_next == False
    for i in range(5):
        assert app.last_tiled_y_ranges[i] != [0, 0]
        assert app.last_tiled_y_ranges[i] == app.view_boxes[i].viewRange()[1]

    # Compute expected expanded Y ranges for tiled layout (currently not asserted).
    vertical_slots = 6
    assert vertical_slots == app.vertical_slots
    fill_factor = 2
    for i in range(0, 5):
        [amin, amax] = last_yranges[i]
        old_center = amin + (amax - amin) / 2
        old_range = amax - amin
        slots_above = 1 + 2 * i
        slots_below = 2 * vertical_slots - i * 2 - 1
        new_amax = old_center + slots_above * old_range / fill_factor
        new_amin = old_center - slots_below * old_range / fill_factor
        # assert app.view_boxes[i].viewRange()[1] == [new_amin, new_amax]


def ytiled_mode_refresh_tests(qtbot, app):
    # Validate refresh timer and button text while in auto Y mode.
    assert app._y_tile_refresh_active
    assert app._y_tile_refresh_timer.isActive()
    assert not app.ytiled_viewbox_next
    assert app.ui.btnResetY.text() == "yAUTO"


def update_corrector_factors_ui(app, cf):
    # Drive the correction factor text boxes in the UI.
    app.ui.txt_poscorr_a.setText(str(cf[0]))
    app.ui.txt_poscorr_b.setText(str(cf[1]))
    app.ui.txt_enccorr_a.setText(str(cf[2]))
    app.ui.txt_enccorr_b.setText(str(cf[3]))


if __name__ == "__main__":
    # print("python -i -m icepaosc.test_window_main")
    test_header()

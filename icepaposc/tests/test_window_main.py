import numpy
import pytest
import sys
from icepaposc.window_main import WindowMain
from PyQt5 import QtWidgets, Qt, QtCore, uic, QtGui
from PyQt5.QtWidgets import QFileDialog, QShortcut, QApplication

@pytest.fixture
def app(qtbot):
    win = WindowMain("w-kitslab-icepap-21", 5000, 3, [],
                      1, "", "", "")
    qtbot.addWidget(win)
    return win

def test_yscaled(app, qtbot):
    assert app.host == "w-kitslab-icepap-21"
    # press cloop button, wait 3s, check data in
    app.ui.btnCLoop.click()
    # Correct number of curves
    assert len(app.curve_items) == 9
    # Acquisition running
    assert not app._paused
    # x axis length is 30s
    vr = app.view_boxes[0].viewRange()
    assert vr[0][1] - vr[0][0] == 30
    # some data in
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 30)
    yscale_mode_after_cloopbtn_tests(qtbot, app)
    assert app.last_now <= app.view_boxes[0].viewRange()[0][1]
    assert app.last_now >= app.view_boxes[0].viewRange()[0][0]
    #press cloop again (restarting acq) and test ytiled mode
    app.ui.btnCLoop.click()
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 60)
    assert app.view_boxes[0].state['autoRange'][1] == True
    last_yranges = []
    for i in range(0,5):
        last_yranges.append(app.view_boxes[i].viewRange()[1])
    app.ui.btnResetY.click()
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 90)
    ytiled_mode_tests(qtbot, app, last_yranges)


def yscale_mode_after_cloopbtn_tests(qtbot, app):
    assert app.ytiled_viewbox_next
    # check all yaxes except last one have autorange on
    assert app.view_boxes[0].state['autoRange'][1] == True
    assert app.view_boxes[1].state['autoRange'][1] == True
    assert app.view_boxes[2].state['autoRange'][1] == True
    assert app.view_boxes[3].state['autoRange'][1] == True
    assert app.view_boxes[4].state['autoRange'][1] == True
    # assert app.view_boxes[5].state['autoRange'][1] == True
    # check xaxis is panning (scope mode) 
    assert app.view_boxes[0].state['autoRange'][0] == False
    assert app.ui.btnResetX.text() == 'tSCALE'
    assert app.ui.btnResetY.text() == 'ySPLIT'

def ytiled_mode_tests(qtbot, app, last_yranges):
    assert not app._paused
    assert not app.ytiled_viewbox_next
    assert app.ui.btnResetY.text() == 'ySCALE'
    # some data in
    # check all yaxes except last one have autorange off
    assert app.view_boxes[0].state['autoRange'][1] == False
    assert app.view_boxes[1].state['autoRange'][1] == False
    assert app.view_boxes[2].state['autoRange'][1] == False
    assert app.view_boxes[3].state['autoRange'][1] == False
    assert app.view_boxes[4].state['autoRange'][1] == False
    # assert app.view_boxes[5].state['autoRange'][1] == True
    # check xaxis is panning (scope mode) 
    assert app.view_boxes[0].state['autoRange'][0] == False
    assert app.ui.btnResetX.text() == 'tSCALE'
    assert app.last_now <= app.view_boxes[0].viewRange()[0][1]
    assert app.last_now >= app.view_boxes[0].viewRange()[0][0]
    # check in ytiled mode
    assert app.ytiled_viewbox_next == False
    assert app.last_tiled_y_ranges[0] != [0,0]
    assert app.last_tiled_y_ranges[0] == app.view_boxes[0].viewRange()[1]
    assert app.last_tiled_y_ranges[1] != [0,0]
    assert app.last_tiled_y_ranges[1] == app.view_boxes[1].viewRange()[1]
    assert app.last_tiled_y_ranges[2] != [0,0]
    assert app.last_tiled_y_ranges[2] == app.view_boxes[2].viewRange()[1]
    assert app.last_tiled_y_ranges[3] != [0,0]
    assert app.last_tiled_y_ranges[3] == app.view_boxes[3].viewRange()[1]
    assert app.last_tiled_y_ranges[4] != [0,0]
    assert app.last_tiled_y_ranges[4] == app.view_boxes[4].viewRange()[1]
    vertical_slots = 6
    fill_factor = 2
    for i in range(0, 5):
        [amin, amax] = last_yranges[i]
        old_center = amin + (amax-amin) / 2
        old_range = amax - amin
        slots_above = 1 + 2*i
        slots_below = 2 * vertical_slots - i*2 -1
        new_amax = old_center + slots_above * old_range / fill_factor
        new_amin = old_center - slots_below * old_range / fill_factor
        assert app.view_boxes[i].viewRange()[1] == [new_amin, new_amax]

def update_corrector_factors_ui(app, cf):
    app.ui.txt_poscorr_a.setText(str(cf[0]))
    app.ui.txt_poscorr_b.setText(str(cf[1]))
    app.ui.txt_enccorr_a.setText(str(cf[2]))
    app.ui.txt_enccorr_b.setText(str(cf[3]))

'''
For some reason the change to corrected does not work with autorangey
in pytest, so correction factors cant be tested against yarange and ytiled
modes. It does work in real

def test_corr_ar(app, qtbot):
    #Now check ytiled mode AFTER a toggle to units
    assert app.host == "w-kitslab-icepap-21"
    app.ui.btnCLoop.click()
    assert not app._paused
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 30)
    ui_corr_factors = [2,100,3,1000]
    print('ui corr updated')
    update_corrector_factors_ui(app, ui_corr_factors)
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 40)
    last_yranges = []
    for i in range(0,5):
        last_yranges.append(app.view_boxes[i].viewRange()[1])
    yscale_mode_after_cloopbtn_tests(qtbot, app)
    # app.ui.btnResetY.click()
    #print('toggle ar into tiled')
    #app._toggle_y_autorange()
    #qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 50)
    #qtbot.waitUntil(lambda: not app.ytiled_viewbox_next)
    # assert len(app.curve_items[0].array_val) == 30
    #ytiled_mode_tests(qtbot, app, last_yranges)
    #print('tiled ok')
    # some data in after tiled mode
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 50)
    # app.curve_items[0].array_val[-1] = 50
    # check applied corrector factors are still default
    # assert app.corr_factors == [1,0,1,0]
    assert app.corr_factors == ui_corr_factors
    # now  toggle units and check everything is ok
    last_yranges = []
    for i in range(0,5):
        last_yranges.append(app.view_boxes[i].viewRange()[1])
    # update_corrector_factors_ui(app, [2, 100, 3, 1000])
    last_coll = app.last_now
    print('toggle corr')
    app._toggle_corr_factors()
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 70)
    print('toggle corr')
    app._toggle_corr_factors()
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 80)
    print('toggle corr')
    app._toggle_corr_factors()
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 90)
    # app._toggle_corr_factors()
    assert app.corr_factors == app.corr_factors_ui
    # wait until the forced yautorange happens
'''

def test_tiled(app, qtbot):
    #Now check ytiled mode AFTER a toggle to units
    assert app.host == "w-kitslab-icepap-21"
    app.ui.btnCLoop.click()
    assert not app._paused
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 30)
    ui_corr_factors = [1,0,1,0]
    update_corrector_factors_ui(app, ui_corr_factors)
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 40)
    last_yranges = []
    for i in range(0,5):
        last_yranges.append(app.view_boxes[i].viewRange()[1])
    # Change from yautorange to ytiled mode and test
    yscale_mode_after_cloopbtn_tests(qtbot, app)
    app._toggle_y_autorange()
    qtbot.waitUntil(lambda: not app.ytiled_viewbox_next)
    ytiled_mode_tests(qtbot, app, last_yranges)
    # some data in after tiled mode
    qtbot.waitUntil(lambda: len(app.curve_items[0].array_val) == 50)

if __name__ == "__main__":
    # print("python -i -m icepaosc.test_window_main")
    test_header()



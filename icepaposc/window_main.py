#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# This file is part of IcepapOCS link:
#        https://github.com/ALBA-Synchrotron/IcepapOCS
#
# Copyright 2017:
#       MAX IV Laboratory, Lund, Sweden
#       CELLS / ALBA Synchrotron, Bellaterra, Spain
#
# Distributed under the terms of the GNU General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
#
# You should have received a copy of the GNU General Public License
# along with IcepapOCS. If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
import os.path

import pyqtgraph as pg
import numpy as np
import time
import datetime
from PyQt5 import QtWidgets, Qt, QtCore, uic, QtGui
from PyQt5.QtWidgets import QFileDialog, QShortcut, QApplication
from PyQt5.QtGui import QKeySequence
from PyQt5.Qt import QClipboard
from icepap import IcePAPController
from .collector import Collector
from .correction_profiles import IPAP_PROFILE, DTAX_PROFILE
from .dialog_settings import DialogSettings
from .settings import Settings
from .axis_time import AxisTime
from .curve_item import CurveItem
from .hotkeyhelptool import HotkeyHelpTool
from .debugtool import DebugTool
from .ffttool import FFTTool
from .derivatetool import DerivativeTool
from .utils import (
    parse_signal_definition,
    load_signal_set_file,
    write_curves_to_csv,
    _format_csv_value
)
import collections
from importlib.resources import path

# Palette Colours
RED = QtGui.QColor(255, 0, 0)
GREEN = QtGui.QColor(0, 255, 0)
BLUE = QtGui.QColor(0, 127, 255)
CYAN = QtGui.QColor(0, 255, 255)
PINK = QtGui.QColor(255, 192, 203)
YELLOW = QtGui.QColor(255, 255, 0)
DARK_GREEN = QtGui.QColor(0, 128, 0)
DARK_CYAN = QtGui.QColor(0, 127, 127)
OLIVE = QtGui.QColor(127, 127, 0)
DARK_RED = QtGui.QColor(128, 0, 0)
DARK_BLUE = QtGui.QColor(0, 0, 255)
PURPLE = QtGui.QColor(127, 0, 127)

DEFAULT_PALETTE = [
    RED,
    GREEN,
    BLUE,
    CYAN,
    PINK,
    YELLOW,
    DARK_GREEN,
    DARK_CYAN,
    OLIVE,
    DARK_RED,
    DARK_BLUE,
    PURPLE,
]

Y_TILE_REFRESH_INTERVAL_MS = 5000
SIGNAL_SETS = {
    "Closed_loop_plot": {
        "signals": [
            ("PosAxis", 1, RED, QtCore.Qt.SolidLine, ""),
            ("DifAxTgtenc", 2, GREEN, QtCore.Qt.SolidLine, ""),
            ("DifAxMotor", 4, BLUE, QtCore.Qt.SolidLine, ""),
            ("VelCurrent", 5, CYAN, QtCore.Qt.SolidLine, ""),
            ("VelMotor", 5, PINK, QtCore.Qt.SolidLine, ""),
            ("EncTgtenc", 3, DARK_GREEN, QtCore.Qt.SolidLine, ""),
            ("StatMoving", 6, RED, QtCore.Qt.SolidLine, ""),
            ("StatSettling", 6, YELLOW, QtCore.Qt.SolidLine, ""),
            ("StatStopcode", 6, GREEN, QtCore.Qt.DotLine, ""),
        ],
        "y_range_config": {5: (-1, 20)},
        "run": True,
    },
    "Currents_plot": {
        "signals": [
            ("PosAxis", 1, RED, QtCore.Qt.SolidLine, ""),
            ("EncTgtenc", 5, DARK_GREEN, QtCore.Qt.SolidLine, ""),
            ("DifAxTgtenc", 4, GREEN, QtCore.Qt.SolidLine, ""),
            ("MeasI", 6, DARK_CYAN, QtCore.Qt.SolidLine, ""),
            ("VelCurrent", 2, CYAN, QtCore.Qt.SolidLine, ""),
            ("VelMotor", 2, PINK, QtCore.Qt.SolidLine, ""),
        ],
        "run": True,
    },
    "Closed_loopd_plot": {
        "signals": [
            ("PosAxis", 1, RED, QtCore.Qt.SolidLine, ""),
            ("DifAxTgtenc", 2, GREEN, QtCore.Qt.SolidLine, ""),
            ("DifAxMotor", 5, BLUE, QtCore.Qt.SolidLine, ""),
            ("VelCurrent", 4, CYAN, QtCore.Qt.SolidLine, ""),
            ("VelMotor", 4, PINK, QtCore.Qt.SolidLine, ""),
            ("MeasI", 6, YELLOW, QtCore.Qt.SolidLine, ""),
            ("EncTgtenc", 3, DARK_GREEN, QtCore.Qt.SolidLine, ""),
            ("StatMoving", 6, RED, QtCore.Qt.SolidLine, ""),
            ("StatSettling", 6, YELLOW, QtCore.Qt.DashLine, ""),
            ("StatStopcode", 6, GREEN, QtCore.Qt.DotLine, ""),
        ],
        "y_range_config": {5: (-1, 17.5)},
    },
    "Closed_loops_plot": {
        "signals": [
            ("PosAxis", 1, RED, QtCore.Qt.SolidLine, ""),
            ("DifAxTgtenc", 2, GREEN, QtCore.Qt.SolidLine, ""),
            ("DifAxMotor", 4, BLUE, QtCore.Qt.SolidLine, ""),
            ("EncTgtenc", 3, CYAN, QtCore.Qt.SolidLine, ""),
            ("StatReady", 6, PINK, QtCore.Qt.DotLine, ""),
            ("StatMoving", 6, RED, QtCore.Qt.DotLine, ""),
            ("StatSettling", 6, YELLOW, QtCore.Qt.DotLine, ""),
            ("StatOutofwin", 6, DARK_CYAN, QtCore.Qt.DotLine, ""),
            ("StatWarning", 6, OLIVE, QtCore.Qt.DotLine, ""),
            ("StatStopcode", 6, GREEN, QtCore.Qt.DotLine, ""),
            ("MeasI", 6, DARK_BLUE, QtCore.Qt.SolidLine, ""),
        ],
        "y_range_config": {5: (-1, 17.5)},
    },
    "Open_loop_plot": {
        "signals": [
            ("PosAxis", 1, RED, QtCore.Qt.SolidLine, ""),
            ("DifAxTgtenc", 2, GREEN, QtCore.Qt.SolidLine, ""),
            ("EncTgtenc", 4, BLUE, QtCore.Qt.SolidLine, ""),
            ("StatWarning", 6, DARK_GREEN, QtCore.Qt.DotLine, ""),
            ("MeasI", 6, YELLOW, QtCore.Qt.DotLine, ""),
            ("VelMotor", 5, PINK, QtCore.Qt.SolidLine, ""),
        ],
        "y_range_config": {5: (-1, 17.5)},
    },
    "Velocities_plot": {
        "signals": [
            ("PosAxis", 1, RED, QtCore.Qt.SolidLine, ""),
            ("DifAxMotor", 2, BLUE, QtCore.Qt.SolidLine, ""),
            ("DifAxTgtenc", 2, GREEN, QtCore.Qt.SolidLine, ""),
            ("VelCurrent", 4, CYAN, QtCore.Qt.SolidLine, ""),
            ("VelMotor", 4, PINK, QtCore.Qt.SolidLine, ""),
        ],
    },
    "Target_plot": {
        "signals": [
            ("PosAxis", 1, RED, QtCore.Qt.SolidLine, ""),
            ("DifAxTgtenc", 2, GREEN, QtCore.Qt.SolidLine, ""),
            ("EncTgtenc", 4, YELLOW, QtCore.Qt.SolidLine, ""),
            ("StatWarning", 6, OLIVE, QtCore.Qt.DotLine, ""),
        ],
        "y_range_config": {5: (-1, 17.5)},
    },
}


class WindowMain(QtWidgets.QMainWindow):
    """A dialog for plotting IcePAP signals."""

    def __init__(
        self,
        host,
        port,
        timeout,
        siglist,
        selected_driver=None,
        sigset=None,
        corr=None,
        # yrange=None,
        dump_rate=1,
        sample_rate=50,
        icepap_controller=None,
        csv_mode=False,
        csv_items=None,
        csv_axes=None,
    ):
        """
        Initializes an instance of class WindowMain.

        host            - IcePAP system address.
        port            - IcePAP system port number.
        timeout         - Socket timeout.
        sigset          - .lst file with signal set to import
        siglist         - List of predefined signals.
                            Element Syntax: <driver>:<signal name>:<Y-axis>
                            Example: ["1:PosAxis:1", "1:MeasI:2", "1:MeasVm:3"]
        selected_driver - The driver to display in combobox at startup.
        icepap_controller - Different than None if used by automated tests
        """
        # This feature is removed for the time being
        yrange = None

        # Init
        super(WindowMain, self).__init__(None)

        # Initialize UI
        self._init_ui(host)

        # Initialize settings
        self.settings = Settings()
        if dump_rate != 1:
            self.settings.dump_rate = dump_rate
        if sample_rate != 50:
            self.settings.sample_rate = sample_rate

        self.csv_mode = bool(csv_mode)
        self.static_items = []
        self._static_entries = []

        # Initialize corrector factors
        self._init_corrector_factors(corr)

        # Initialize data collector
        if not self.csv_mode:
            self._init_collector(host, port, timeout, icepap_controller)
            self._configure_correction_profile_from_descriptor()
        else:
            self.collector = None

        self.subscriptions = {}
        self.curve_items = []
        self._paused = False

        # Initialize plot
        self._init_plot(yrange)

        # Initialize signals
        self._init_signals(selected_driver, sigset, siglist)
        if self.csv_mode and csv_items:
            self.add_static_items(csv_items, csv_axes)
            self._apply_csv_mode_ui()

        # Initialize time
        self._init_timers()

        # Cleanup the layout
        self._remove_empty_y_axis(6)  # This is causing an issue
        self._remove_empty_y_axis(5)
        self._remove_empty_y_axis(4)
        self._remove_empty_y_axis(3)
        self._init_status_strip()

    def _init_ui(self, host):
        """Initializes the UI."""
        self.uvr = 0
        self.host = host
        self.ui = self
        with path("icepaposc.ui", "window_main.ui") as f:
            uic.loadUi(f, baseinstance=self.ui, package="icepaposc.custom_widgets")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setWindowTitle("Oscilloscope | {}".format(host))

    def _init_corrector_factors(self, corr):
        """Initializes the corrector factors."""
        # Correction profiles (Ctrl+U cycles through profile states)
        self._corr_profile = IPAP_PROFILE
        self._state_list = list(self._corr_profile.states)
        self._corr_state = -1
        self._corr_entries = {}
        self._manual_factors = [1.0, 0.0, 1.0, 0.0]
        self._corr_build_info = None
        self._corr_state_changed = False
        corr_values = None
        if isinstance(corr, (list, tuple)) and len(corr) == 4:
            corr_values = corr
        elif isinstance(corr, str) and corr and corr.count(",") == 3:
            corr_values = [float(value) for value in corr.split(",")]
        if corr_values:
            self.ui.txt_poscorr_a.setText(str(float(corr_values[0])))
            self.ui.txt_poscorr_b.setText(str(float(corr_values[1])))
            self.ui.txt_enccorr_a.setText(str(float(corr_values[2])))
            self.ui.txt_enccorr_b.setText(str(float(corr_values[3])))
            self._txt_poscorr_a_focus_lost()
            self._txt_poscorr_b_focus_lost()
            self._txt_enccorr_a_focus_lost()
            self._txt_enccorr_b_focus_lost()
        self._manual_factors = self._read_manual_factors()

    def set_correction_build_info(self, build_info):
        """Sets extra build info for correction profiles and rebuilds entries."""
        self._corr_build_info = build_info
        if hasattr(self, "curve_items"):
            self._update_correction_entries()

    def _init_collector(self, host, port, timeout, icepap_controller):
        """Initializes the data collector."""
        try:
            if icepap_controller is None:
                icepap_controller = IcePAPController(
                    host.split(';')[0], port, timeout, auto_axes=True
                )
            self.collector = Collector(
                self.settings,
                self.callback_collect,
                icepap_controller=icepap_controller,
                hostname=host
            )
        except Exception as e:
            msg = "Failed to create main window.\n{}".format(e)
            print(msg)
            QtWidgets.QMessageBox.critical(self, "Create Main Window", msg)
            return

    def _configure_correction_profile_from_descriptor(self):
        if not self.collector:
            return
        build_info = None
        try:
            build_info = self.collector.icepap_system.get_correction_build_info()
        except Exception:
            build_info = None
        profile = IPAP_PROFILE
        if isinstance(build_info, dict) and build_info.get("profile") == "dtax":
            profile = DTAX_PROFILE
        self._corr_profile = profile
        self._state_list = list(self._corr_profile.states)
        self.set_correction_build_info(build_info)

    def _init_plot(self, yrange):
        """Initializes the plot."""
        # Switch to using black background and white foreground
        pg.setConfigOption("background", "k")
        pg.setConfigOption("foreground", "w")
        self.fgcolor = QtGui.QColor(255, 255, 255)
        self.color_axes = self.fgcolor

        # Set up the plot area.
        self.plot_widget = pg.PlotWidget()
        self._plot_item = self.plot_widget.getPlotItem()
        self.hotkeyHelp = HotkeyHelpTool(self.plot_widget)
        self.debugTool = DebugTool(self, self.plot_widget)
        self.fftTool = FFTTool(self)
        self.derivativeTool = DerivativeTool(self)
        self.fftTool.attachToPlotItem(self._plot_item)
        self.derivativeTool.attachToPlotItem(self._plot_item)
        self.view_boxes = [
            self.plot_widget.getViewBox(),
            pg.ViewBox(),
            pg.ViewBox(),
            pg.ViewBox(),
            pg.ViewBox(),
            pg.ViewBox(),
        ]
        self.ui.vloCurves.setDirection(QtWidgets.QBoxLayout.BottomToTop)
        self.ui.vloCurves.addWidget(self.plot_widget)

        # Set up the X-axis.
        # Hide the original X-axis without removing it (avoid Qt delete during paint).
        self._plot_item.getAxis("bottom").hide()
        self._axisTime = AxisTime(orientation="bottom")  # Create new X-axis.
        self._axisTime.linkToView(self.view_boxes[0])
        self._plot_item.layout.addItem(self._axisTime, 4, 1)
        self.now = -1  # self.collector.get_current_time()
        self.view_boxes[0].enableAutoRange(axis=self.view_boxes[0].XAxis)
        self.view_boxes[1].enableAutoRange(axis=self.view_boxes[1].XAxis)
        self.view_boxes[2].enableAutoRange(axis=self.view_boxes[2].XAxis)
        self.view_boxes[3].enableAutoRange(axis=self.view_boxes[3].XAxis)
        self.view_boxes[4].enableAutoRange(axis=self.view_boxes[4].XAxis)
        self.view_boxes[5].enableAutoRange(axis=self.view_boxes[5].XAxis)
        self.ui.btnResetX.setText("tSCALE")  # temporary fix
        self._initialize_x_time()

        # Set up the Y-axes.
        self.ytiled_viewbox_next = False
        self._y_tile_refresh_active = False
        self._y_tile_refresh_timer = None
        self.skip_autorange = []
        self._y_manual_axes = set()
        if yrange is not None and yrange != "":
            yrange_s = yrange.split(",")
            for a in yrange_s:
                self.skip_autorange.append(int(a))
        self._plot_item.showAxis("right")
        self._plot_item.scene().addItem(self.view_boxes[1])
        self._plot_item.scene().addItem(self.view_boxes[2])
        self._plot_item.scene().addItem(self.view_boxes[3])
        self._plot_item.scene().addItem(self.view_boxes[4])
        self._plot_item.scene().addItem(self.view_boxes[5])
        ax3 = pg.AxisItem(orientation="right", linkView=self.view_boxes[2])
        ax4 = pg.AxisItem(orientation="right", linkView=self.view_boxes[3])
        ax5 = pg.AxisItem(orientation="right", linkView=self.view_boxes[4])
        ax6 = pg.AxisItem(orientation="right", linkView=self.view_boxes[5])
        self.axes = [
            self._plot_item.getAxis("left"),
            self._plot_item.getAxis("right"),
            ax3,
            ax4,
            ax5,
            ax6,
        ]
        self.axes[1].linkToView(self.view_boxes[1])
        self.view_boxes[1].setXLink(self.view_boxes[0])
        self.view_boxes[2].setXLink(self.view_boxes[0])
        self.view_boxes[3].setXLink(self.view_boxes[0])
        self.view_boxes[4].setXLink(self.view_boxes[0])
        self.view_boxes[5].setXLink(self.view_boxes[0])
        self._plot_item.layout.addItem(self.axes[2], 2, 3)
        self._plot_item.layout.addItem(self.axes[3], 2, 4)
        self._plot_item.layout.addItem(self.axes[4], 2, 5)
        self._plot_item.layout.addItem(self.axes[5], 2, 6)
        self._plot_item.hideButtons()
        self.last_tiled_y_ranges = []
        for i in range(0, len(self.view_boxes)):
            self.last_tiled_y_ranges.append([0, 0])
        self._force_tiled_viewbox_y_ranges_after_corr_factors_change = False
        self._enable_all_y_autoranging_state()
        self._do_black_background()

        # Set up the crosshair vertical line.
        self.cross_hair2_time = None
        self.local_t1 = None
        self.local_t2 = None
        self.last_time_value = 0
        self.vertical_line = pg.InfiniteLine(angle=90, movable=False)
        self.view_boxes[0].addItem(self.vertical_line, ignoreBounds=True)
        # Set up the fixed crosshair vertical for time measurements.
        self.vertical_line2 = pg.InfiniteLine(angle=90, movable=False)

    def _init_signals(self, selected_driver, sigset, siglist):
        """Initializes the signals."""
        # Initialize comboboxes and buttons.
        if not self.csv_mode:
            self._fill_combo_box_driver_ids(selected_driver)
            self._fill_combo_box_signals()
        self._update_button_status()
        self.ui.red_radio.setChecked(True)
        self.ui.solidline_radio.setChecked(True)
        self.ui.nomarker_radio.setChecked(True)

        # Set up signalling connections.
        self._connect_signals()
        self.proxy = pg.SignalProxy(
            self.plot_widget.scene().sigMouseMoved, rateLimit=60, slot=self._mouse_moved
        )
        self.proxy1 = pg.SignalProxy(
            self.plot_widget.scene().sigMouseClicked,
            rateLimit=60,
            slot=self._mouse_clicked,
        )

        # Add any predefined signals. 7, 9, 11 low contrast on black bgd
        self.palette_colours = DEFAULT_PALETTE

        # Import command line signal set (file) first
        self._file_path = None
        if not self.csv_mode and sigset != "" and sigset is not None:
            self._import_signal_set(sigset)

        # Add signals from cmd line to cmbbox
        button_id = 0
        for sig in ([] if self.csv_mode else siglist):
            if button_id > 11:
                button_id = 0
            try:
                driver, signal_name, axis = parse_signal_definition(sig)
            except ValueError as exc:
                msg = str(exc)
                print(msg)
                QtWidgets.QMessageBox.critical(self, "Bad Signal Syntax", msg)
                return
            self._add_signal(
                driver,
                signal_name,
                axis,
                self.palette_colours[button_id],
                QtCore.Qt.SolidLine,
                self.ui.marker_radio_group.checkedButton().text(),
            )
            button_id += 1

        # encoder count to motor step conversion factor measurement
        self.ecpmt_just_enabled = False
        self.step_ini = 0
        self.enc_ini = 0

    def _init_timers(self):
        """Initializes the timers."""
        # Set up auto save of collected signal data.
        self._save_ticker = QtCore.QTimer()
        self._save_ticker.timeout.connect(self._auto_save)
        self._save_time = None
        self._idx = 0
        self._settings_updated = False
        self._old_use_append = self.settings.use_append
        self._prepare_next_auto_save()

        self._y_tile_refresh_timer = QtCore.QTimer()
        self._y_tile_refresh_timer.setInterval(Y_TILE_REFRESH_INTERVAL_MS)
        self._y_tile_refresh_timer.timeout.connect(self._tile_viewbox_yranges)

        # A hotkey allows to save the data in the viewbox (ONLY) directly to a predefined filename
        self.hotkey_filename = "default"

    def _apply_csv_mode_ui(self):
        self.ui.cbDrivers.setEnabled(False)
        self.ui.cbSignals.setEnabled(False)
        self.ui.sbAxis.setEnabled(False)
        self.ui.btnAdd.setEnabled(False)
        self.ui.btnShift.setEnabled(False)
        self.ui.btnRemoveSel.setEnabled(False)
        self.ui.btnRemoveAll.setEnabled(False)
        self.ui.btnPause.setEnabled(False)
        self.ui.btnNow.setEnabled(False)
        self.ui.actionClosed_Loop.setEnabled(False)
        self.ui.actionVelocities.setEnabled(False)
        self.ui.actionCurrents.setEnabled(False)
        self.ui.actionTarget.setEnabled(False)
        self.ui.actionImport_Set.setEnabled(False)
        self.ui.actionExport_Set.setEnabled(False)
        self.ui.chkEctsTurn.setEnabled(False)

    def _axis_index_from_name(self, axis_name):
        axis_name = (axis_name or "").upper()
        if axis_name.startswith("Y"):
            try:
                idx = int(axis_name[1:])
            except Exception:
                idx = 1
        else:
            idx = 1
        idx = max(1, min(idx, len(self.view_boxes)))
        return idx

    def add_static_items(self, items, axes=None):
        axes = axes or []
        for idx, item in enumerate(items):
            axis_name = axes[idx] if idx < len(axes) else None
            axis_idx = self._axis_index_from_name(axis_name)
            self.view_boxes[axis_idx - 1].addItem(item)
            entry = self._build_static_entry(item, axis_idx)
            self._static_entries.append(entry)
            self.static_items.append(item)
            self._add_active_static_entry(entry)
        self._update_plot_axes_labels()
        self._view_all_data()

    def get_static_items(self):
        return list(self.static_items)

    def _add_active_static_entry(self, entry):
        signal_name = entry["name"]
        driver = 1
        if "-" in signal_name:
            head, tail = signal_name.split("-", 1)
            if head.isdigit():
                driver = int(head)
                signal_name = tail or signal_name
        signature = "{}:{}:{}".format(driver, signal_name, entry["axis"])
        self.ui.lvActiveSig.addItem(signature)
        index = self.ui.lvActiveSig.count() - 1
        self.ui.lvActiveSig.setCurrentRow(index)
        self.ui.lvActiveSig.item(index).setForeground(entry["color"])
        self.ui.lvActiveSig.item(index).setBackground(Qt.QColor(0, 0, 0))

    def _build_static_entry(self, item, axis_idx):
        name = item.name() or "signal"
        x_data, y_data = item.getData()
        try:
            x = np.array(x_data, dtype=float)
            y = np.array(y_data, dtype=float)
        except Exception:
            x = np.array([], dtype=float)
            y = np.array([], dtype=float)
        color = None
        try:
            pen = item.opts.get("pen", None)
            color = pg.mkPen(pen).color()
        except Exception:
            color = QtGui.QColor(255, 255, 255)
        entry = {
            "item": item,
            "axis": axis_idx,
            "name": name,
            "color": color,
            "x": x,
            "y": y,
            "y_min": float(np.min(y)) if y.size else 0.0,
            "y_max": float(np.max(y)) if y.size else 0.0,
            "val_cross": None,
        }
        return entry

    def _static_get_y(self, entry, time_value):
        x = entry["x"]
        y = entry["y"]
        if x.size == 0:
            return 0.0
        idx = int(np.searchsorted(x, time_value))
        if idx <= 0:
            closest = 0
        elif idx >= len(x):
            closest = len(x) - 1
        else:
            left = idx - 1
            right = idx
            closest = left if abs(x[left] - time_value) <= abs(x[right] - time_value) else right
        return float(y[closest])

    def _fill_combo_box_driver_ids(self, selected_driver):
        """Fills the driver IDs combo box with available drivers."""
        driver_ids = self.collector.get_available_drivers()
        for driver_id in driver_ids:
            self.ui.cbDrivers.addItem(str(driver_id))
        if selected_driver is not None:
            start_index = self.ui.cbDrivers.findText(str(selected_driver))
        # maybe the selected_driver is not available;
        # then just take the first one
        if start_index == -1:
            start_index = 0
        self.ui.cbDrivers.setCurrentIndex(start_index)

    def _fill_combo_box_signals(self):
        """Fills the signals combo box with available signals."""
        signals = self.collector.get_available_signals()
        for sig in signals:
            self.ui.cbSignals.addItem(sig)

        self.ui.cbSignals.setCurrentIndex(0)

    def _connect_signals(self):
        """Connects UI signals to their respective slots."""
        self.ui.sbAxis.valueChanged.connect(self._select_axis)
        self.ui.btnAdd.clicked.connect(self._add_button_clicked)
        self.ui.btnShift.clicked.connect(self._shift_button_clicked)
        self.ui.btnRemoveSel.clicked.connect(self._remove_selected_signal)
        self.ui.btnRemoveAll.clicked.connect(self._remove_all_signals)
        self.ui.btnCLoop.setDefaultAction(self.ui.actionClosed_Loop)
        self.ui.btnVelocities.setDefaultAction(self.ui.actionVelocities)
        self.ui.btnCurrents.setDefaultAction(self.ui.actionCurrents)
        self.ui.btnTarget.setDefaultAction(self.ui.actionTarget)
        self.ui.btnClear.clicked.connect(self._clear_all)
        self.ui.btnSeeAll.clicked.connect(self._view_all_data)
        self.ui.btnResetX.clicked.connect(self._toggle_x_autorange)
        self.ui.btnResetY.clicked.connect(self._toggle_y_autorange)
        self.ui.btnPause.clicked.connect(self._pause_x_axis)
        self.ui.btnNow.clicked.connect(self._goto_now)
        self.ui.actionSave_to_File.triggered.connect(self._save_to_file)
        self.ui.actionSettings.triggered.connect(self._display_settings_dlg)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionClosed_Loop.triggered.connect(self._signals_closed_loop)
        self.ui.actionExport_Set.triggered.connect(self._export_signal_set)
        self.ui.actionImport_Set.triggered.connect(self._import_signal_set)
        self.ui.actionVelocities.triggered.connect(self._signals_velocities)
        self.ui.actionCurrents.triggered.connect(self._signals_currents)
        self.ui.actionTarget.triggered.connect(self._signals_target)
        self.view_boxes[0].sigResized.connect(self._update_views)
        self.ui.chkEctsTurn.stateChanged.connect(self.enable_ects_per_turn_calculation)
        self.ui.btnAxisScaleAuto.clicked.connect(self._set_axis_autoscale)
        self.ui.btnAxisOffsIncrease.clicked.connect(self._axis_offs_pp)
        self.ui.btnAxisOffsDecrease.clicked.connect(self._axis_offs_mm)
        self.ui.btnAxisScaleIncrease.clicked.connect(self._axis_scale_pp)
        self.ui.btnAxisScaleDecrease.clicked.connect(self._axis_scale_mm)
        self.ui.btnWhitebg.clicked.connect(self._do_white_background)
        self.ui.btnGreybg.clicked.connect(self._do_grey_background)
        self.ui.btnBlackbg.clicked.connect(self._do_black_background)

        self.shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut.activated.connect(self._save_window_content_to_file)
        self.shortcut = QShortcut(QKeySequence("Ctrl+Shift+O"), self)
        self.shortcut.activated.connect(self._save_raw_states_window_content_to_file)
        self.shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut.activated.connect(self._signals_closed_loop_dynamic)
        # self.shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        # self.shortcut.activated.connect(self._signals_closed_loop_static)
        # self.shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        # self.shortcut.activated.connect(self._signals_open_loop)
        self.shortcut = QShortcut(QKeySequence("Ctrl+U"), self)
        self.shortcut.activated.connect(self._toggle_corr_factors)
        self.shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        self.shortcut.activated.connect(self._get_filename_string)
        self.shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.shortcut.activated.connect(self._toggle_y_autorange)
        self.shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.shortcut.activated.connect(self._zoom_in_x)
        self.shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.shortcut.activated.connect(self._zoom_out_x)
        self.shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut.activated.connect(self._toggle_x_autorange)
        self.shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        self.shortcut.activated.connect(self.hotkeyHelp.toggle)
        self.shortcut = QShortcut(QKeySequence("Ctrl+Shift+H"), self)
        self.shortcut.activated.connect(self.debugTool.toggle)

        self.ui.txt_poscorr_a.editingFinished.connect(self._txt_poscorr_a_focus_lost)
        self.ui.txt_poscorr_b.editingFinished.connect(self._txt_poscorr_b_focus_lost)
        self.ui.txt_enccorr_a.editingFinished.connect(self._txt_enccorr_a_focus_lost)
        self.ui.txt_enccorr_b.editingFinished.connect(self._txt_enccorr_b_focus_lost)

    def _txt_poscorr_a_focus_lost(self):
        self.ui.txt_poscorr_a.setCursorPosition(0)

    def _txt_poscorr_b_focus_lost(self):
        self.ui.txt_poscorr_b.setCursorPosition(0)

    def _txt_enccorr_a_focus_lost(self):
        self.ui.txt_enccorr_a.setCursorPosition(0)

    def _txt_enccorr_b_focus_lost(self):
        self.ui.txt_enccorr_b.setCursorPosition(0)

    def _read_manual_factors(self):
        manual = list(self._manual_factors)
        try:
            manual[0] = float(self.ui.txt_poscorr_a.text())
        except Exception:
            pass
        try:
            manual[1] = float(self.ui.txt_poscorr_b.text())
        except Exception:
            pass
        try:
            manual[2] = float(self.ui.txt_enccorr_a.text())
        except Exception:
            pass
        try:
            manual[3] = float(self.ui.txt_enccorr_b.text())
        except Exception:
            pass
        return manual

    def _corr_key(self, driver_addr, signal_name):
        return "{}:{}".format(driver_addr, signal_name).lower()

    def _build_profile_entry(
        self, driver_addr, signal_name, manual=None, build_info=None
    ):
        # Build a per-signal correction profile entry using the current profile.
        entry = {
            "source": "units",
            "factors": {"units": (1.0, 0.0)},
            "states": list(self._state_list),
            "profile": self._corr_profile.name,
            "manual": manual,
        }
        try:
            manual_pairs = None
            if manual is not None:
                manual_pairs = [
                    (manual[0], manual[1]),
                    (manual[2], manual[3]),
                ]
            icepap_system = getattr(self.collector.icepap_system, "icepap_system", None)
            if icepap_system is None:
                icepap_system = self.collector.icepap_system
            source, factors = self._corr_profile.build_factors(
                icepap_system, driver_addr, signal_name, manual_pairs, build_info
            )
            entry.update(
                {
                    "source": source,
                    "factors": factors,
                    "states": list(self._state_list),
                    "profile": self._corr_profile.name,
                    "manual": manual_pairs,
                }
            )
        except Exception:
            pass
        # Ensure every global state exists in this entry with default identity factors.
        self._ensure_entry_states(entry)
        return entry

    def _ensure_entry_states(self, entry):
        # Keep entry factors aligned with the global state list, defaulting to no-op.
        factors = entry.get("factors") or {}
        if not isinstance(factors, dict):
            factors = {}
            entry["factors"] = factors
        for state in self._state_list:
            if state not in factors:
                factors[state] = (1.0, 0.0)
        entry["states"] = list(self._state_list)

    def _register_correction_entry(self, curve_item):
        # Register a new correction entry; extend the global state list if needed.
        entry = self._build_profile_entry(
            curve_item.driver_addr,
            curve_item.signal_name,
            manual=self._manual_factors,
            build_info=self._corr_build_info,
        )
        if entry.get("factors"):
            new_states = [k for k in entry["factors"].keys() if k not in self._state_list]
            if new_states:
                # Append new states in discovery order.
                self._state_list.extend(new_states)
        # Ensure the new entry includes all states (including newly added ones).
        self._ensure_entry_states(entry)
        self._corr_entries[self._corr_key(curve_item.driver_addr, curve_item.signal_name)] = entry
        curve_item.set_correction_profile(entry)
        curve_item.apply_correction_state(self._corr_state)

    def _drop_correction_entry(self, curve_item):
        key = self._corr_key(curve_item.driver_addr, curve_item.signal_name)
        self._corr_entries.pop(key, None)

    def _update_correction_entries(self):
        for ci in self.curve_items:
            entry = self._build_profile_entry(
                ci.driver_addr,
                ci.signal_name,
                manual=self._manual_factors,
                build_info=self._corr_build_info,
            )
            self._corr_entries[self._corr_key(ci.driver_addr, ci.signal_name)] = entry
            ci.set_correction_profile(entry)
            ci.apply_correction_state(self._corr_state)


    def _init_status_strip(self):
        self._status_label = QtWidgets.QLabel()
        self.statusbar.addPermanentWidget(self._status_label, 1)
        self._status_values = {
            "ya": "yAUTO",
            "ta": "TSCALE",
            "cf": "OFF",
            "cap": "",
        }
        self._status_label.setToolTip(
            "yAUTO: Y autorange\n"
            "ySCALE: Y tiled once\n"
            "ySCALEa: Y tiled refresh\n"
            "TSCALE: Time scale\n"
            "TPAN: Time pan\n"
            "OFF/UNITS/STEPS/ECTS/MT: Correction state"
        )
        self._update_y_status()
        self._update_time_status()
        self._update_cf_status()
        self._update_capacity_status()

    def _refresh_status_label(self):
        if not hasattr(self, "_status_values"):
            return
        if self.csv_mode:
            try:
                self._status_label.setText("CSV MODE")
            except Exception:
                pass
            return
        text = "  ".join(
            [
                self._status_values.get("ta", "---"),
                self._status_values.get("ya", "---"),
                self._status_values.get("cf", "---"),
                self._status_values.get("cap", ""),
            ]
        ).strip()
        try:
            self._status_label.setText(text)
        except Exception:
            pass

    def _set_status_text(self, *, ya=None, ta=None, cf=None):
        if not hasattr(self, "_status_values"):
            return
        if ya is not None:
            self._status_values["ya"] = ya
        if ta is not None:
            self._status_values["ta"] = ta
        if cf is not None:
            self._status_values["cf"] = cf
        self._refresh_status_label()

    def _update_y_status(self):
        if not hasattr(self, "_status_values"):
            return
        # Always derive the current state from the active flags.
        if self._y_tile_refresh_active:
            value = "ySCALEa"
        elif self.ytiled_viewbox_next:
            value = "yAUTO"
        else:
            value = "ySCALE"
        self._set_status_text(ya=value)

    def _update_time_status(self):
        if not hasattr(self, "_status_values"):
            return
        value = "TSCALE" if self.x_autorange_enabled() else "TPAN"
        self._set_status_text(ta=value)

    def _update_cf_status(self):
        if not hasattr(self, "_status_values"):
            return
        if self._corr_state == -1 or not self._state_list:
            value = "OFF"
        else:
            value = str(self._state_list[self._corr_state]).upper()
        self._set_status_text(cf=value)

    def _update_capacity_status(self):
        if not hasattr(self, "_status_values"):
            return
        period_ms = self.settings.sample_rate
        autosave_txt = "AUTOSAVE ON" if self.settings.use_auto_save else "AUTOSAVE OFF"
        rate_txt = "---"
        try:
            if period_ms:
                hz = 1000.0 / float(period_ms)
                rate_val = "{:.1f}".format(hz).rstrip("0").rstrip(".")
                rate_txt = "{}Hz".format(rate_val)
        except Exception:
            rate_txt = "---"
        cap_text = "{} {}".format(rate_txt, autosave_txt)
        self._status_values["cap"] = cap_text
        self._refresh_status_label()

    def closeEvent(self, event):
        """Overloads (QMainWindow) QWidget.closeEvent()."""
        self._remove_all_signals()
        event.accept()

    def _update_views(self):
        """Updates the geometry of the view boxes."""
        self.view_boxes[1].setGeometry(self.view_boxes[0].sceneBoundingRect())
        self.view_boxes[2].setGeometry(self.view_boxes[0].sceneBoundingRect())
        self.view_boxes[3].setGeometry(self.view_boxes[0].sceneBoundingRect())
        self.view_boxes[4].setGeometry(self.view_boxes[0].sceneBoundingRect())
        self.view_boxes[5].setGeometry(self.view_boxes[0].sceneBoundingRect())
        self.view_boxes[1].linkedViewChanged(
            self.view_boxes[0], self.view_boxes[1].XAxis
        )
        self.view_boxes[2].linkedViewChanged(
            self.view_boxes[0], self.view_boxes[2].XAxis
        )
        self.view_boxes[3].linkedViewChanged(
            self.view_boxes[0], self.view_boxes[3].XAxis
        )
        self.view_boxes[4].linkedViewChanged(
            self.view_boxes[0], self.view_boxes[4].XAxis
        )
        self.view_boxes[5].linkedViewChanged(
            self.view_boxes[0], self.view_boxes[5].XAxis
        )

    def _update_button_status(self):
        val = self.ui.lvActiveSig.count() == 0
        self.ui.btnShift.setDisabled(val)
        self.ui.btnRemoveSel.setDisabled(val)
        self.ui.btnRemoveAll.setDisabled(val)

    def _get_filename_string(self):
        name, done1 = QtWidgets.QInputDialog.getText(
            self,
            "Filename string",
            "Input a file name string for the .csv files "
            "(20220131_1500_filename_string_*.csv:",
            text=self.hotkey_filename,
        )
        print(name)
        self.hotkey_filename = name

    def _update_plot_axes_labels(self):
        # txt = ['', '', '']
        txt = ["", "", "", "", "", ""]
        if self.csv_mode:
            for entry in self._static_entries:
                color = entry["color"]
                name = entry["name"]
                t = "<span style='font-size: 8pt; color: {};'>{}</span>".format(
                    color.name(), name
                )
                txt[entry["axis"] - 1] += t
        else:
            for ci in self.curve_items:
                t = "<span style='font-size: 8pt; " "color: {};'>{}</span>".format(
                    ci.color.name(), ci.signature
                )
                txt[ci.y_axis - 1] += t
        for i in range(0, len(self.axes)):
            self.axes[i].setLabel(txt[i])

    def _select_axis(self):
        pass

    def _add_button_clicked(self):
        addr = int(self.ui.cbDrivers.currentText())
        my_signal_name = str(self.ui.cbSignals.currentText())
        my_axis = self.ui.sbAxis.value()
        my_linecolor = self._get_line_color()
        my_linestyle = self._get_line_style()
        my_linemarker = self._get_line_marker()
        self._add_signal(
            addr, my_signal_name, my_axis, my_linecolor, my_linestyle, my_linemarker
        )
        self._goto_now()

    def _get_line_color(self):
        the_btn = self.ui.color_radio_group.checkedButton()
        if the_btn:
            return the_btn.palette().color(QtGui.QPalette.WindowText)
        else:
            return QtGui.QColor(0, 0, 0)

    def _get_line_marker(self):
        the_btn = self.ui.marker_radio_group.checkedButton()
        if the_btn:
            return str(the_btn.text())
        else:
            return ""

    def _get_line_style(self):
        if self.ui.solidline_radio.isChecked():
            return QtCore.Qt.SolidLine
        elif self.ui.dottedline_radio.isChecked():
            return QtCore.Qt.DotLine
        else:
            return QtCore.Qt.SolidLine

    def _add_signal(
        self,
        driver_addr,
        signal_name,
        y_axis,
        linecolor,
        linestyle,
        linemarker,
        auto_save=False,
    ):
        """
        Adds a new curve to the plot area.

        driver_addr - IcePAP driver address.
        signal_name - Signal name.
        y_axis      - Y axis to plot against.
        """
        try:
            subscription_id = self.collector.subscribe(driver_addr, signal_name)
        except Exception as e:
            msg = "Failed to subscribe to signal {} " "from driver {}.\n{}".format(
                signal_name, driver_addr, e
            )
            print(msg)
            QtWidgets.QMessageBox.critical(self, "Add Curve", msg)
            return
        ci = CurveItem(
            subscription_id,
            driver_addr,
            signal_name,
            y_axis,
            linecolor,
            linestyle,
            linemarker,
        )
        self._register_correction_entry(ci)
        self._add_y_axis(y_axis)
        self._add_curve(ci)
        self.curve_items.append(ci)
        self.collector.start(subscription_id)
        self.ui.lvActiveSig.addItem(ci.signature)
        index = len(self.curve_items) - 1
        self.ui.lvActiveSig.setCurrentRow(index)
        self.ui.lvActiveSig.item(index).setForeground(ci.color)
        self.ui.lvActiveSig.item(index).setBackground(Qt.QColor(0, 0, 0))
        self._update_plot_axes_labels()
        self._update_button_status()
        if self._y_tile_refresh_active:
            self._tile_viewbox_yranges()
        elif self.ytiled_viewbox_next:
            self._enable_all_y_autoranging_state()
        else:
            self._tile_viewbox_yranges()
        if auto_save:
            self._auto_save(True)

    def _remove_selected_signal(self):
        self._auto_save(True)
        index = self.ui.lvActiveSig.currentRow()
        ci = self.curve_items[index]
        self._drop_correction_entry(ci)
        y_axis = ci.y_axis
        self.collector.unsubscribe(ci.subscription_id)
        self._remove_curve_plot(ci)
        self.ui.lvActiveSig.takeItem(index)
        self.curve_items.remove(ci)
        self._remove_empty_y_axis(y_axis)
        self._update_plot_axes_labels()
        self._update_button_status()

    def _remove_all_signals(self):
        """Removes all signals."""
        self._auto_save(True)
        for index in range(self.ui.lvActiveSig.count() - 1, -1, -1):
            self.ui.lvActiveSig.takeItem(index)
            if index >= len(self.curve_items):
                continue
            ci = self.curve_items[index]
            self._drop_correction_entry(ci)
            self.collector.unsubscribe(ci.subscription_id)
            self._remove_curve_plot(ci)
            y_axis = ci.y_axis
            self.curve_items.remove(ci)
            self._remove_empty_y_axis(y_axis)
        self.curve_items = []
        self._update_plot_axes_labels()
        self._update_button_status()
        self.hotkey_filename = "default"
        if self._y_tile_refresh_active:
            self._stop_y_tile_refresh()
        self._enable_all_y_autoranging_state()

    def _add_y_axis(self, y_axis):
        i = y_axis - 1
        if y_axis > 2:
            axis = self.axes[i]
            if axis is not None and axis.scene() is self._plot_item.scene():
                axis.setVisible(True)
                view_box = self.view_boxes[i]
                if view_box is not None:
                    view_box.setVisible(True)
                return
            self.view_boxes[i] = pg.ViewBox()
            self.view_boxes[i].disableAutoRange(axis=self.view_boxes[i].XAxis)
            self.view_boxes[i].enableAutoRange(axis=self.view_boxes[i].YAxis)
            # self.view_boxes[i].autoRange()
            self._plot_item.scene().addItem(self.view_boxes[i])
            self.axes[i] = pg.AxisItem(orientation="right", linkView=self.view_boxes[i])
            self.view_boxes[i].setXLink(self.view_boxes[0])
            self._plot_item.layout.addItem(self.axes[i], 2, y_axis)
            self.axes[i].setPen(self.color_axes)
            self.axes[i].setTextPen(self.color_axes)

    def _remove_empty_y_axis(self, y_axis):
        if self.csv_mode:
            # Avoid removing/hiding axes in CSV mode during pytest runs; Qt can
            # try to paint deleted AxisItem objects and crash (segfault).
            return
        i = y_axis - 1
        if i in self.skip_autorange:
            self.skip_autorange.remove(i)
        if i is not None and i > 1:
            if self.y_axis_empty(y_axis):
                try:
                    axis = self.axes[i]
                    if axis is not None and axis.scene() is self._plot_item.scene():
                        axis.setVisible(False)
                    view_box = self.view_boxes[i]
                    if view_box is not None and view_box.scene() is self._plot_item.scene():
                        view_box.setVisible(False)
                except BaseException:
                    return

    def y_axis_empty(self, y_axis):
        if self.csv_mode:
            for entry in self._static_entries:
                if entry["axis"] == y_axis:
                    return False
        else:
            for ci in self.curve_items:
                if ci.y_axis == y_axis:
                    return False
        return True

    def _shift_button_clicked(self):
        """Assign a curve to a different y axis."""
        index = self.ui.lvActiveSig.currentRow()
        ci = self.curve_items[index]
        self._remove_curve_plot(ci)
        y_axis = ci.y_axis
        self._add_y_axis((ci.y_axis % len(self.axes)) + 1)
        ci.y_axis = (ci.y_axis % len(self.axes)) + 1
        self._remove_empty_y_axis(y_axis)
        ci.update_signature()
        self._add_curve(ci)
        self.ui.lvActiveSig.takeItem(index)
        self.ui.lvActiveSig.insertItem(index, ci.signature)
        self.ui.lvActiveSig.item(index).setForeground(ci.color)
        self.ui.lvActiveSig.item(index).setBackground(Qt.QColor(0, 0, 0))
        self.ui.lvActiveSig.setCurrentRow(index)
        self._update_plot_axes_labels()

    def _add_curve(self, ci):
        """
        Create a new curve and add it to a viewbox.

        ci - Curve item that will be the owner.
        """
        my_curve = ci.create_curve()
        self.view_boxes[ci.y_axis - 1].addItem(my_curve)

    def _mouse_moved(self, evt):
        """
        Acts om mouse move.

        evt - Event containing the position of the mouse pointer.
        """
        # print(evt)
        pos = evt[0]  # The signal proxy turns original arguments into a tuple.
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.view_boxes[0].mapSceneToView(pos)
            time_value = mouse_point.x()
            self.last_time_value = time_value
            self._update_signals_text(time_value)

    def _format_legend_value(self, value):
        decimals = max(0, getattr(self.settings, "legend_decimals", 3))
        fmt = "{:." + str(decimals) + "f}"
        try:
            formatted = fmt.format(value)
            if "." in formatted:
                formatted = formatted.rstrip("0").rstrip(".")
            if formatted == "":
                formatted = "0"
            return formatted
        except (TypeError, ValueError):
            return ""

    def _update_signals_text(self, time_value):
        try:
            date = datetime.datetime.fromtimestamp(time_value)
            pretty_time = date.strftime("%H:%M:%S.%f")[:-3]
        except ValueError:  # Time out of range.
            return
        txtmax = ""
        txtnow = ""
        txtmin = ""
        txtdiff = ""
        txtlocalmin = ""
        txtlocalmax = ""
        text_size = 8
        span_html = "{}{}</span>"
        if self.csv_mode:
            for entry in self._static_entries:
                color = entry["color"]
                tmp = "<span style='font-size: {}pt; overflow: hidden; color: {};'>|"
                tmp = tmp.format(text_size, color.name())
                x = entry["x"]
                y = entry["y"]
                if x.size and x[0] <= time_value <= x[-1]:
                    txtmax += span_html.format(
                        tmp, self._format_legend_value(entry["y_max"])
                    )
                    y_now = self._static_get_y(entry, time_value)
                    txtnow += span_html.format(
                        tmp, self._format_legend_value(y_now)
                    )
                    txtmin += span_html.format(
                        tmp, self._format_legend_value(entry["y_min"])
                    )
                    if self.cross_hair2_time is not None and entry["val_cross"] is not None:
                        txtdiff += span_html.format(
                            tmp,
                            self._format_legend_value(y_now - entry["val_cross"]),
                        )
                if (
                    self.local_t1 is not None
                    and self.local_t2 is not None
                    and x.size
                    and x[0] <= self.local_t1 <= x[-1]
                    and x[0] <= self.local_t2 <= x[-1]
                ):
                    t1 = min(self.local_t1, self.local_t2)
                    t2 = max(self.local_t1, self.local_t2)
                    mask = (x >= t1) & (x <= t2)
                    if np.any(mask):
                        yslice = y[mask]
                        txtlocalmin += span_html.format(
                            tmp, self._format_legend_value(float(np.min(yslice)))
                        )
                        txtlocalmax += span_html.format(
                            tmp, self._format_legend_value(float(np.max(yslice)))
                        )
        else:
            for ci in self.curve_items:
                tmp = "<span style='font-size: {}pt; overflow: hidden; color: {};'>|"
                tmp = tmp.format(text_size, ci.color.name())
                if ci.in_range(time_value):
                    txtmax += span_html.format(tmp, self._format_legend_value(ci.val_max))
                    txtnow += span_html.format(
                        tmp, self._format_legend_value(ci.get_y(time_value))
                    )
                    txtmin += span_html.format(tmp, self._format_legend_value(ci.val_min))
                    if self.cross_hair2_time is not None:
                        txtdiff += span_html.format(
                            tmp,
                            self._format_legend_value(ci.get_y(time_value) - ci.val_cross),
                        )
                # You can enter here because of a click after a double click or
                # after a ctrlo
                if (
                    self.local_t1 is not None
                    and self.local_t2 is not None
                    and ci.in_range(self.local_t1)
                    and ci.in_range(self.local_t2)
                ):
                    txtlocalmin += span_html.format(
                        tmp,
                        self._format_legend_value(
                            ci.calculate_local_min(self.local_t1, self.local_t2)
                        ),
                    )
                    txtlocalmax += span_html.format(
                        tmp,
                        self._format_legend_value(
                            ci.calculate_local_max(self.local_t1, self.local_t2)
                        ),
                    )
        if self.cross_hair2_time is not None:
            tmp = "|<span style='font-size: {}pt; overflow: hidden; color: {};'>{} {}</span>"
            txtnow += tmp.format(
                text_size,
                str(self.fgcolor.name()),
                pretty_time,
                datetime.datetime.fromtimestamp(
                    abs(time_value - self.cross_hair2_time)
                ).strftime("%S.%f")[:-3],
            )
            tmp = "|<span style='font-size: {}pt; overflow: hidden; color: {};'>{} {}</span>"
        else:
            tmp = (
                "|<span style='font-size: {}pt; overflow: hidden; color: {};'>{}</span>"
            )
            txtnow += tmp.format(text_size, str(self.fgcolor.name()), pretty_time)

        if self.cross_hair2_time is not None:
            title = "<br>{}<br>{}<br>{}<br> {}".format(txtmax, txtnow, txtmin, txtdiff)
        else:
            # you can't have crosshair on and display locals
            if self.local_t2 is not None and self.local_t1 is not None:
                title = "<br>{}<br>{}<br> {}".format(txtlocalmax, txtnow, txtlocalmin)
            else:
                title = "<br>{}<br>{}<br> {}".format(txtmax, txtnow, txtmin)
        title2 = "<div style='overflow: hidden'>" + title + "</div>"
        self.plot_widget.setTitle(title2)
        self.vertical_line.setPos(time_value)

    def _mouse_clicked(self, evt):
        pos = evt[0]  # The signal proxy turns original arguments into a tuple.
        if (
            pos.button() == QtCore.Qt.LeftButton
            and pos.modifiers() & QtCore.Qt.ControlModifier
        ):
            self._adjust_view_xmin(pos)
            return
        mouse_point = self.view_boxes[0].mapSceneToView(evt[0].scenePos())
        time_value = mouse_point.x()
        if evt[0].double():
            try:
                date = datetime.datetime.fromtimestamp(time_value)
                pretty_time = date.strftime("%H:%M:%S.%f")[:-3]
            except ValueError:  # Time out of range.
                return
            self.cross_hair2_time = time_value
            self.view_boxes[0].addItem(self.vertical_line2, ignoreBounds=True)
            self.vertical_line2.setPos(mouse_point.x())
            if self.csv_mode:
                for entry in self._static_entries:
                    x = entry["x"]
                    if x.size and x[0] <= time_value <= x[-1]:
                        entry["val_cross"] = self._static_get_y(entry, time_value)
            else:
                for ci in self.curve_items:
                    if ci.in_range(time_value):
                        ci.val_cross = ci.get_y(time_value)
            self.local_t1 = time_value
            self.local_t2 = None
        else:
            if self.cross_hair2_time is not None:
                self.cross_hair2_time = None
                self.view_boxes[0].removeItem(self.vertical_line2)
            if self.local_t2 is None:
                self.local_t2 = time_value
            else:
                self.local_t1 = None
                self.local_t2 = None

    def _adjust_view_xmin(self, mouse_event):
        """Snap the X-range left edge to the clicked position."""
        view_box = self.view_boxes[0]
        if view_box is None:
            return
        x_min, x_max = view_box.viewRange()[0]
        click_pos = view_box.mapSceneToView(mouse_event.scenePos()).x()
        if not np.isfinite(click_pos):
            return
        if click_pos >= x_max:
            click_pos = x_max - 1e-6
        if click_pos == x_min:
            return
        self._x_pan_span = x_max - click_pos
        self._x_pan_next_oscmode_after_ctrlclick = True
        view_box.enableAutoRange(axis=view_box.XAxis, enable=False)
        self.ui.btnResetX.setText("tSCALE")
        view_box.setXRange(click_pos, x_max, padding=0)
        mouse_event.accept()

    def _remove_curve_plot(self, ci):
        """
        Remove a curve from the plot area.

        ci - Curve item to remove.
        """
        self.view_boxes[ci.y_axis - 1].removeItem(ci.curve)

    def _do_white_background(self):
        color_axes = QtGui.QColor(0, 0, 0)
        color_plot = QtGui.QColor(255, 255, 255)
        self._set_plot_colors(color_axes, color_plot)

    def _do_grey_background(self):
        color_axes = QtGui.QColor(0, 0, 0)
        color_plot = QtGui.QColor(230, 230, 230)
        self._set_plot_colors(color_axes, color_plot)

    def _do_black_background(self):
        color_axes = QtGui.QColor(255, 255, 255)
        color_plot = QtGui.QColor(0, 0, 0)
        self._set_plot_colors(color_axes, color_plot)

    def _set_plot_colors(self, color_axes, color_plot):
        self.plot_widget.setBackground(color_plot)
        self.color_axes = color_axes
        for i in range(len(self.axes)):
            self.axes[i].setPen(color_axes)
            self.axes[i].setTextPen(color_axes)
        self._axisTime.setPen(color_axes)
        self._axisTime.setTextPen(color_axes)
        self.fgcolor = color_axes

    def _apply_signal_set(
        self,
        signal_set,
        hotkey_filename,
        y_range_config=None,
        black_background=True,
        run=False,
    ):
        self._remove_all_signals()
        drv_addr = int(self.ui.cbDrivers.currentText())
        for signal_def in signal_set:
            self._add_signal(drv_addr, *signal_def)

        self._enable_all_y_autoranging_state()

        if y_range_config:
            for axis, y_range in y_range_config.items():
                self.view_boxes[axis].disableAutoRange(axis=self.view_boxes[axis].YAxis)
                self.view_boxes[axis].setYRange(y_range[0], y_range[1], padding=0)
                self.skip_autorange.append(axis)

        if black_background:
            self._do_black_background()

        self.hotkey_filename = hotkey_filename

        if run:
            self._run()

        self._goto_now()

    def _signals_closed_loop(self):
        """Display a specific set of curves."""
        config = SIGNAL_SETS["Closed_loop_plot"]
        self._apply_signal_set(
            config["signals"],
            "Closed_loop_plot",
            y_range_config=config.get("y_range_config"),
            run=config.get("run", False),
        )

    def _signals_currents(self):
        """Display a specific set of curves."""
        config = SIGNAL_SETS["Currents_plot"]
        self._apply_signal_set(
            config["signals"],
            "Currents_plot",
            y_range_config=config.get("y_range_config"),
            run=config.get("run", False),
        )

    def _signals_closed_loop_dynamic(self):
        """Display a specific set of curves."""
        config = SIGNAL_SETS["Closed_loopd_plot"]
        self._apply_signal_set(
            config["signals"],
            "Closed_loopd_plot",
            y_range_config=config.get("y_range_config"),
            run=config.get("run", False),
        )

    def _signals_closed_loop_static(self):
        """Display a specific set of curves."""
        config = SIGNAL_SETS["Closed_loops_plot"]
        self._apply_signal_set(
            config["signals"],
            "Closed_loops_plot",
            y_range_config=config.get("y_range_config"),
            run=config.get("run", False),
        )

    def _signals_open_loop(self):
        """Display a specific set of curves."""
        config = SIGNAL_SETS["Open_loop_plot"]
        self._apply_signal_set(
            config["signals"],
            "Open_loop_plot",
            y_range_config=config.get("y_range_config"),
            run=config.get("run", False),
        )

    def _signals_velocities(self):
        """Display a specific set of curves."""
        config = SIGNAL_SETS["Velocities_plot"]
        self._apply_signal_set(
            config["signals"],
            "Velocities_plot",
            y_range_config=config.get("y_range_config"),
            run=config.get("run", False),
        )

    def _signals_target(self):
        """Display a specific set of curves."""
        config = SIGNAL_SETS["Target_plot"]
        self._apply_signal_set(
            config["signals"],
            "Target_plot",
            y_range_config=config.get("y_range_config"),
            run=config.get("run", False),
        )

    def _clear_all(self):
        """Clear all the displayed curves."""
        self._auto_save()
        for ci in self.curve_items:
            ci.clear()

    def _view_all_data(self):
        """Adjust X axis to view all collected data."""
        if self.csv_mode and self._static_entries:
            xs = [entry["x"] for entry in self._static_entries if entry["x"].size]
            if not xs:
                return
            time_start = min(np.min(x) for x in xs)
            time_end = max(np.max(x) for x in xs)
            self.view_boxes[0].setXRange(time_start, time_end, padding=0)
            return
        if self.collector is None:
            return
        time_start = self.collector.get_current_time()
        for ci in self.curve_items:
            t = ci.start_time()
            if 0 < t < time_start:
                time_start = t
        time_end = self.collector.get_current_time()
        self.view_boxes[0].setXRange(time_start, time_end, padding=0)

    def _import_signal_set(self, filename=None):
        if filename is None or filename is False:
            fname = QFileDialog.getOpenFileName(
                self,
                "Import Signal Set",
                filter="Signal Set Files Files (*.lst);;All Files (*)",
                directory=self.settings.signals_set_folder,
            )
        else:
            fname = [filename]
        if not fname or not fname[0]:
            return
        file_path = fname[0]
        signal_defs, force_black_background = load_signal_set_file(file_path)
        self._remove_all_signals()
        drv_addr = int(self.ui.cbDrivers.currentText())
        for signal_def in signal_defs:
            style = (
                QtCore.Qt.SolidLine
                if signal_def["line_style"] == 0
                else QtCore.Qt.DashLine
            )
            marker_value = signal_def["line_marker"]
            if marker_value == 0:
                marker = None
            elif marker_value == 1:
                marker = "o"
            elif marker_value == 2:
                marker = "s"
            else:
                marker = "+"
            self._add_signal(
                drv_addr,
                signal_def["signal_name"],
                signal_def["axis"],
                QtGui.QColor(signal_def["color"]),
                style,
                marker,
            )
        if force_black_background:
            self._do_black_background()

    def _export_signal_set(self):
        file_name = os.path.join(self.settings.signals_set_folder, "SignalSet.lst")
        fname = QFileDialog.getSaveFileName(
            self,
            "Export Signal Set",
            file_name,
            filter="Signal Set Files Files (*.lst);;All Files (*)",
        )
        if not fname or not fname[0]:
            return
        file_path = fname[0]
        with open(file_path, "w") as f:
            for ci in self.curve_items:
                line = "{} {} {} {} {}\n".format(
                    ci.signal_name,
                    ci.y_axis,
                    ci.color.name(),
                    ci.pen["style"],
                    ci.symbol,
                )
                f.write(line)

    def x_autorange_enabled(self):
        ar = self.view_boxes[0].state["autoRange"][0]
        # This sometimes returns a boolean sometimes an int!
        if ar == 1.0 or ar == True:
            ar = True
        return ar

    def _enable_x_autorange(self):
        if not self._paused:
            self.view_boxes[0].enableAutoRange(axis=self.view_boxes[0].XAxis)
            self.ui.btnResetX.setText("tPAN")
        self._x_pan_next_oscmode_after_ctrlclick = False
        self._update_time_status()

    def _enable_x_oscmode(self):
        if self.collector is None:
            return
        now = self.collector.get_current_time()
        span = getattr(self, "_x_pan_span", None)
        if span is not None and span > 0:
            start = now - span
            self.view_boxes[0].setXRange(start, now, padding=0)
            self.ui.btnResetX.setText("tSCALE")
            self._update_time_status()
            return
        start = now - self.settings.default_x_axis_len
        x_min = self.view_boxes[0].viewRange()[0][0]
        x_max = self.view_boxes[0].viewRange()[0][1]
        if x_max - x_min < self.settings.default_x_axis_len:
            self.view_boxes[0].setXRange(start, now, padding=0)
        else:
            self.view_boxes[0].setXRange(x_min, now, padding=0)
        self.ui.btnResetX.setText("tSCALE")
        self._update_time_status()

    def _initialize_x_time(self):
        if self.collector is None:
            return
        now = self.collector.get_current_time()
        start = now - self.settings.default_x_axis_len
        self.view_boxes[0].setXRange(start, now, padding=0)

    def _toggle_x_autorange(self):
        """
        Reset the length of the X axis to
        the initial number of seconds (setting).
        Toggles between autorangex, autopanx
        _update_view wont autopanx if now (current time) is outside of the displayed data
        """
        if not self.x_autorange_enabled() and getattr(
            self, "_x_pan_next_oscmode_after_ctrlclick", False
        ):
            self._x_pan_next_oscmode_after_ctrlclick = False
            self._enable_x_oscmode()
            return
        if not self.x_autorange_enabled():
            self._enable_x_autorange()
        else:
            self._enable_x_oscmode()

    def _force_all_y_autorange(self):
        for i in range(0, len(self.view_boxes)):
            if i not in self.skip_autorange:
                vb = self.view_boxes[i]
                vb.autoRange()

    def _enable_all_ys_autoranging(self):
        for i in range(0, len(self.view_boxes)):
            if i not in self.skip_autorange:
                vb = self.view_boxes[i]
                vb.enableAutoRange(axis=vb.YAxis)

    def _enable_all_y_autoranging_state(self):
        self._stop_y_tile_refresh()
        self._enable_all_ys_autoranging()
        self._y_manual_axes.clear()
        self.ytiled_viewbox_next = True
        self.ui.btnResetY.setText("ySCALE")
        self._update_y_status()
        # self._force_all_y_autorange()

    def _enable_all_y_tiled_once_state(self):
        self._stop_y_tile_refresh()
        self._y_manual_axes.clear()
        self.ytiled_viewbox_next = False
        self.ui.btnResetY.setText("ySCALEa")
        self._tile_viewbox_yranges()
        self._update_y_status()

    def _enable_all_y_tiled_refresh_state(self):
        if not self._y_tile_refresh_timer:
            return
        if not self._y_tile_refresh_active:
            self._y_tile_refresh_active = True
            self._y_tile_refresh_timer.start()
            self._y_manual_axes.clear()
        self._update_y_status()
        self.ytiled_viewbox_next = False
        self._tile_viewbox_yranges()
        self.ui.btnResetY.setText("yAUTO")

    def _enable_y_autoranging(self, i):
        vb = self.view_boxes[i - 1]
        vb.enableAutoRange(axis=vb.YAxis)
        # vb.autoRange()

    def _get_y_axes_ranging_mode(self):
        if self._y_tile_refresh_active:
            return "ySCALEa"
        if self.ytiled_viewbox_next:
            return "yAUTO"
        return "ySCALE"

    def _restore_y_axes_ranging_mode(self, mode):
        if mode == "ySCALEa":
            self._enable_all_y_tiled_refresh_state()
        elif mode == "yAUTO":
            self._enable_all_y_autoranging_state()
        elif mode == "ySCALE":
            self._enable_all_y_tiled_once_state()

    def _toggle_y_autorange(self):
        # Toggle between vertical tile autorange or normal ys autorange
        # For the vertical tiled mode to work autorange must be called once before
        # If correction factors are toggled in tiled mode, autorange is forced one before
        # the tile calculation is done
        if self.ytiled_viewbox_next:
            self._enable_all_y_tiled_once_state()
            self.ui.btnResetY.setText("ySCALEa")
        elif self._y_tile_refresh_active:
            self._enable_all_y_autoranging_state()
        else:
            self._enable_all_y_tiled_refresh_state()

    def _start_y_tile_refresh(self):
        if not self._y_tile_refresh_active:
            self._enable_all_y_tiled_refresh_state()

    def _stop_y_tile_refresh(self):
        if self._y_tile_refresh_timer:
            self._y_tile_refresh_timer.stop()
        self._y_tile_refresh_active = False
        if self.ytiled_viewbox_next:
            self.ui.btnResetY.setText("ySCALE")

    def _pause_x_axis(self):
        """Freeze the X axis."""
        if self._paused:
            self._paused = False
            self.ui.btnPause.setText("Pause")
        else:
            self._paused = True
            self.ui.btnPause.setText("Run")
            self._enable_x_oscmode()
        self.ui.btnClear.setDisabled(self._paused)

    def _run(self):
        self._paused = False
        self.ui.btnPause.setText("Pause")

    def _zoom_in_x(self):
        """Zoom in on now or viewbox center"""
        x_min = self.view_boxes[0].viewRange()[0][0]
        x_max = self.view_boxes[0].viewRange()[0][1]
        # now = self.collector.get_current_time()
        if x_max < self.now:
            x_center = (x_min + x_max) / 2
            x_min_new = x_center - (x_max - x_min) / 4
            x_max_new = x_center + (x_max - x_min) / 4
        else:
            x_min_new = x_max - (x_max - x_min) / 2
            x_max_new = x_max
        self.view_boxes[0].setXRange(x_min_new, x_max_new, padding=0)

    def _zoom_out_x(self):
        """Zoom out on now or viewbox center"""
        x_min = self.view_boxes[0].viewRange()[0][0]
        x_max = self.view_boxes[0].viewRange()[0][1]
        # now = self.collector.get_current_time()
        if x_max < self.now:
            x_center = (x_min + x_max) / 2
            x_min_new = x_center - (x_max - x_min)
            x_max_new = x_center + (x_max - x_min)
        else:
            x_min_new = x_max - (x_max - x_min) * 2
            x_max_new = x_max
        self.view_boxes[0].setXRange(x_min_new, x_max_new, padding=0)

    def _goto_now(self):
        """Pan X axis to display newest values."""
        if self.collector is None:
            return
        now = self.collector.get_current_time()
        x_min = self.view_boxes[0].viewRange()[0][0]
        x_max = self.view_boxes[0].viewRange()[0][1]
        self.view_boxes[0].setXRange(now - (x_max - x_min), now, padding=0)

    def enable_action(self, enable=True):
        """Enables or disables menu item File|Settings."""
        self.ui.actionSettings.setEnabled(enable)

    def _save_window_content_to_file(self):
        if self._corr_state == -1 or not self._state_list:
            unitstr = "st"
        else:
            unitstr = str(self._state_list[self._corr_state]).lower()
        driver = 0
        try:
            driver = int(self.ui.cbDrivers.currentText())
        except Exception:
            driver = 0
        filename1 = "{}_{:03d}_{}_{}.csv".format(
            time.strftime("%y%m%d_%H%M%S", time.localtime()),
            driver,
            self.hotkey_filename,
            unitstr,
        )
        QApplication.clipboard().setText(filename1)
        # print(filename1)
        user_path = os.path.expanduser("~")
        base_folder = os.path.join(user_path, ".icepaposc")
        filename2 = os.path.join(base_folder, (filename1))
        print(filename2)
        self._save_to_file(filename2)

    def _save_raw_states_window_content_to_file(self):
        if self._corr_state != -1 and self._state_list:
            msg = (
                "Ctrl+Shift+O only works in correction state OFF.\n"
                "Press Ctrl+U to set the state to OFF."
            )
            QtWidgets.QMessageBox.information(
                self, "Raw Export", msg
            )
            return
        driver = 0
        try:
            driver = int(self.ui.cbDrivers.currentText())
        except Exception:
            driver = 0
        filename1 = "{}_{:03d}_{}_rawstates.csv".format(
            time.strftime("%y%m%d_%H%M%S", time.localtime()),
            driver,
            self.hotkey_filename,
        )
        QApplication.clipboard().setText(filename1)
        user_path = os.path.expanduser("~")
        base_folder = os.path.join(user_path, ".icepaposc")
        filename2 = os.path.join(base_folder, (filename1))
        print(filename2)
        self._save_raw_states_to_file(filename2)

    def _save_to_file(self, filename=None):
        if self.csv_mode:
            self._save_static_to_file(filename)
            return
        if not self.curve_items:
            return
        if filename is None or filename == False:
            capt = "Save to csv file"
            fa = QtWidgets.QFileDialog.getSaveFileName(caption=capt, filter="*.csv")
            fn = str(fa[0])
        else:
            x_min = self.view_boxes[0].viewRange()[0][0]
            x_max = self.view_boxes[0].viewRange()[0][1]
            fn = filename
            # If set visible window as local window and update legend
            self.local_t1 = x_min
            self.local_t2 = x_max
            self._update_signals_text(self.last_time_value)
        if not fn:
            return
        if fn[-4:] != ".csv":
            fn = fn + ".csv"
        try:
            if filename is None or filename == False:
                write_curves_to_csv(self.curve_items, fn)
            else:
                write_curves_to_csv(self.curve_items, fn, [x_min, x_max])
            self._report_csv_write(fn)
        except Exception as e:
            msg = "Failed to write csv file: {}\n{}".format(fn, e)
            print(msg)
            QtWidgets.QMessageBox.critical(self, "File Open Failed", msg)

    def _save_raw_states_to_file(self, filename=None):
        if self.csv_mode:
            return
        if not self.curve_items:
            return
        if filename is None or filename == False:
            capt = "Save to csv file"
            fa = QtWidgets.QFileDialog.getSaveFileName(caption=capt, filter="*.csv")
            fn = str(fa[0])
        else:
            x_min = self.view_boxes[0].viewRange()[0][0]
            x_max = self.view_boxes[0].viewRange()[0][1]
            fn = filename
            self.local_t1 = x_min
            self.local_t2 = x_max
            self._update_signals_text(self.last_time_value)
        if not fn:
            return
        if fn[-4:] != ".csv":
            fn = fn + ".csv"
        try:
            if filename is None or filename == False:
                self._write_raw_states_csv(fn)
            else:
                self._write_raw_states_csv(fn, time_range=(x_min, x_max))
            self._report_csv_write(fn)
        except Exception as e:
            msg = "Failed to write csv file: {}\n{}".format(fn, e)
            print(msg)
            QtWidgets.QMessageBox.critical(self, "File Open Failed", msg)

    def _report_csv_write(self, filename):
        if not filename or not os.path.isfile(filename):
            print("CSV verification failed: file not found")
            return
        header = ""
        line_count = 0
        first_value = None
        last_value = None
        try:
            with open(filename, "r") as csv_file:
                header = csv_file.readline().rstrip("\n")
                for _ in csv_file:
                    line_count += 1
                    if first_value is None:
                        first_value = _
                    last_value = _
        except Exception as e:
            print("CSV verification failed: {}".format(e))
            return
        print("CSV lines: {}".format(line_count))
        print("CSV header: {}".format(header))
        if first_value is not None and last_value is not None:
            try:
                first_parts = first_value.split(",", 2)
                last_parts = last_value.split(",", 2)
                if len(first_parts) < 2 or len(last_parts) < 2:
                    raise ValueError("Missing timestamp column")
                first_token = first_parts[1]
                last_token = last_parts[1]
                acq_time = float(last_token) - float(first_token)
                print("Acq time:{}".format(acq_time))
            except Exception as e:
                print("Acq time: unavailable ({})".format(e))

    def _write_raw_states_csv(self, filename, time_range=None):
        entries = []
        for ci in self.curve_items:
            with ci.lock:
                time_vals = list(ci.array_time)
                raw_vals = list(ci.array_val)
                corr_source = ci.corr_source
                corr_factors = dict(ci.corr_factors) if ci.corr_factors else {}
            if not time_vals:
                entries.append(
                    {
                        "driver": ci.driver_addr,
                        "signal": ci.signal_name,
                        "time": [],
                        "raw": [],
                        "source": corr_source,
                        "factors": corr_factors,
                    }
                )
                continue
            if time_range is not None:
                t_min, t_max = time_range
                idx_min = ci.get_time_index(t_min)
                idx_max = ci.get_time_index(t_max)
                time_vals = time_vals[idx_min:idx_max]
                raw_vals = raw_vals[idx_min:idx_max]
            entries.append(
                {
                    "driver": ci.driver_addr,
                    "signal": ci.signal_name,
                    "time": time_vals,
                    "raw": raw_vals,
                    "source": corr_source,
                    "factors": corr_factors,
                }
            )

        if not entries:
            return
        # Build a column-oriented matrix with raw + converted values per state.
        csv_matrix = collections.OrderedDict()
        for entry in entries:
            driver = entry["driver"]
            signal = entry["signal"]
            time_vals = entry["time"]
            raw_vals = entry["raw"]
            source = (entry["source"] or "").lower()
            factors = entry["factors"] or {}

            header_time = "time-{}-{}".format(driver, signal)
            header_val = "val-{}-{}".format(driver, signal)
            csv_matrix[header_time] = time_vals
            csv_matrix[header_val] = raw_vals

            # For each correction state, add a converted column.
            for state in self._state_list:
                if state is None:
                    continue
                state_name = str(state)
                if state_name.lower() == source:
                    continue
                suffix = "_" + state_name.lower()
                key_time = "time-{}-{}{}".format(driver, signal, suffix)
                key_val = "val-{}-{}{}".format(driver, signal, suffix)
                corr = factors.get(state_name)
                if corr is None:
                    corr = factors.get(state_name.lower())
                if corr:
                    scale = float(corr[0])
                    offset = float(corr[1])
                    conv_vals = [scale * v + offset for v in raw_vals]
                else:
                    conv_vals = list(raw_vals)
                csv_matrix[key_time] = time_vals
                csv_matrix[key_val] = conv_vals

        # Ensure every column is padded to the longest length.
        non_empty_keys = [key for key, values in csv_matrix.items() if values]
        if not non_empty_keys:
            return
        max_len = max(len(csv_matrix[key]) for key in non_empty_keys)
        for key in csv_matrix:
            delta = max_len - len(csv_matrix[key])
            if delta > 0:
                csv_matrix[key] = delta * [np.nan] + csv_matrix[key]

        # Write CSV header and rows.
        with open(filename, "w+") as csv_file:
            for key in csv_matrix:
                csv_file.write(",{}".format(key))
            csv_file.write("\n")
            for idx in range(0, max_len):
                line = str(idx)
                for key in csv_matrix:
                    line += ",{}".format(_format_csv_value(csv_matrix[key][idx]))
                csv_file.write(line + "\n")

    def _save_static_to_file(self, filename=None):
        if not self._static_entries:
            return
        if filename is None or filename == False:
            capt = "Save to csv file"
            fa = QtWidgets.QFileDialog.getSaveFileName(caption=capt, filter="*.csv")
            fn = str(fa[0])
        else:
            x_min = self.view_boxes[0].viewRange()[0][0]
            x_max = self.view_boxes[0].viewRange()[0][1]
            fn = filename
        if not fn:
            return
        if fn[-4:] != ".csv":
            fn = fn + ".csv"
        try:
            self._write_static_csv(fn, time_range=(x_min, x_max) if filename else None)
            self._report_csv_write(fn)
        except Exception as e:
            msg = "Failed to write csv file: {}\n{}".format(fn, e)
            print(msg)
            QtWidgets.QMessageBox.critical(self, "File Open Failed", msg)

    def _write_static_csv(self, filename, time_range=None):
        csv_matrix = collections.OrderedDict()
        for entry in self._static_entries:
            name = entry["name"].replace("-", "_").replace(":", "_").replace(" ", "_")
            header_time = "time-{}".format(name)
            header_val = "val-{}".format(name)
            csv_matrix[header_time] = entry["x"]
            csv_matrix[header_val] = entry["y"]

        non_empty = [key for key, values in csv_matrix.items() if len(values) > 0]
        if not non_empty:
            return

        if time_range is not None:
            t_min, t_max = time_range
            for key in list(csv_matrix.keys()):
                data = csv_matrix[key]
                if data.size == 0:
                    csv_matrix[key] = data
                    continue
                if key.startswith("time-"):
                    mask = (data >= t_min) & (data <= t_max)
                    csv_matrix[key] = data[mask]
                else:
                    time_key = "time-" + key[4:]
                    xvals = csv_matrix.get(time_key, None)
                    if xvals is None or xvals.size == 0:
                        csv_matrix[key] = data
                    else:
                        mask = (xvals >= t_min) & (xvals <= t_max)
                        csv_matrix[key] = data[mask]

        max_len = max(len(values) for values in csv_matrix.values())
        for key, values in list(csv_matrix.items()):
            if len(values) < max_len:
                pad = [np.nan] * (max_len - len(values))
                csv_matrix[key] = list(values) + pad
            else:
                csv_matrix[key] = list(values)

        with open(filename, "w+") as csv_file:
            for key in csv_matrix:
                csv_file.write(",{}".format(key))
            csv_file.write("\n")
            for idx in range(max_len):
                line = str(idx)
                for key in csv_matrix:
                    line += ",{}".format(_format_csv_value(csv_matrix[key][idx]))
                csv_file.write(line + "\n")

    def _auto_save(self, use_new_file=False):
        if not self.curve_items or not self._file_path:
            return
        if not self._settings_updated and not self.settings.use_auto_save:
            return
        self._save_ticker.stop()

        # Create matrix.
        my_dict = collections.OrderedDict()
        for ci in self.curve_items:
            start_idx = ci.get_time_index(self._save_time)
            header = "time-{}-{}".format(ci.driver_addr, ci.signal_name)
            my_dict[header] = ci.array_time[start_idx:]
            header = "val-{}-{}".format(ci.driver_addr, ci.signal_name)
            my_dict[header] = ci.array_val_corr[start_idx:]
        key_longest = None
        for key in my_dict:  # Find a non empty list.
            if my_dict[key]:
                key_longest = key
                break
        if not key_longest:
            self._prepare_next_auto_save(True)
            return
        for key in my_dict:  # Find the longest list.
            if my_dict[key] and my_dict[key][0] < my_dict[key_longest][0]:
                key_longest = key
        for key in my_dict:  # Fill up the shorter lists with nan.
            delta = len(my_dict[key_longest]) - len(my_dict[key])
            my_dict[key] = delta * [np.nan] + my_dict[key]

        # Write matrix to file.
        try:
            f = open(self._file_path, self._get_write_mode())
        except Exception as e:
            msg = "Failed to open file: {}\n{}".format(self._file_path, e)
            print(msg)
            QtWidgets.QMessageBox.critical(self, "File Open Failed", msg)
            return
        if self._idx == 0:
            for key in my_dict:
                f.write(",{}".format(key))
            f.write("\n")
        for i in range(0, len(my_dict[key_longest])):
            line = str(self._idx)
            self._idx += 1
            for key in my_dict:
                line += ",{}".format(_format_csv_value(my_dict[key][i]))
            f.write(line + "\n")
        f.close()

        self._prepare_next_auto_save(use_new_file)

    def _prepare_next_auto_save(self, use_new_file=False):
        if self.settings.use_auto_save:
            if (
                use_new_file
                or not self.settings.use_append
                or not self._file_path
                or self._settings_updated
            ):
                self._set_new_file_path()
            self._save_time = time.time()
            self._save_ticker.start(60000 * self.settings.saving_interval)
        else:
            self._save_time = None
            self._file_path = None

    def _set_new_file_path(self):
        self._idx = 0
        time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        file_name = "IcepapOSC_{}.csv".format(time_str)
        self._file_path = self.settings.saving_folder + "/" + file_name

    def _get_write_mode(self):
        do_append = self.settings.use_append
        if self._settings_updated:
            do_append = self._old_use_append
        return "a+" if do_append else "w+"

    def _display_settings_dlg(self):
        self.enable_action(False)
        dlg = DialogSettings(self, self.settings)
        dlg.show()

    def settings_updated(self):
        """Settings have been changed."""
        self._settings_updated = True
        if self._file_path:
            self._auto_save(True)
        else:
            self._prepare_next_auto_save()
        self._old_use_append = self.settings.use_append
        self._settings_updated = False
        self._enable_x_autorange()
        self._update_capacity_status()

    def callback_collect(self, subscription_id, value_list):
        """
        Callback function that stores the data collected from IcePAP.

        subscription_id - Subscription id.
        value_list - List of tuples (time, value).
        """
        if not self._paused:
            for ci in self.curve_items:
                if ci.subscription_id == subscription_id:
                    ci.collect(value_list)
            self._update_view()
        else:
            x_min = self.view_boxes[0].viewRange()[0][0]
            x_max = self.view_boxes[0].viewRange()[0][1]
            self._update_curves_values(x_min, x_max)

    def _update_view(self):
        self.uvr = self.uvr + 1
        x_min = self.view_boxes[0].viewRange()[0][0]
        x_max = self.view_boxes[0].viewRange()[0][1]
        last_now_in_range = self.now <= x_max
        last_now_in_window = self.now <= x_max and self.now >= x_min
        # print(self.now, self.x_autorange_enabled(), last_now_in_range, last_now_in_window)
        # print(x_min, x_max, x_max-x_min)
        # If signals have been added during acquisition, autorange can go lost
        if not self.x_autorange_enabled():
            self.ui.btnResetX.setText("tSCALE")
        # Update the X-axis. Autorange, autopan, none if not now
        self.last_now = self.now
        self.now = self.collector.get_current_time()
        if not self.x_autorange_enabled():
            # print('No autorange')
            if last_now_in_range or self.last_now == -1:
                self.view_boxes[0].setXRange(
                    self.now - (x_max - x_min), self.now, padding=0
                )
        elif not last_now_in_window:
            # print('Autorange not in window')
            # autorange x can be true while the box is elsewhere?
            self._goto_now()
            self._view_all_data()
            self._enable_x_autorange()
        # Detect out of range and update the now button
        self.ui.btnNow.setDisabled(last_now_in_range)

        # Update the displayed curves based on corrections
        self._update_curves_values(x_min, x_max)
        if self.ytiled_viewbox_next:
            for i, vb in enumerate(self.view_boxes):
                if i not in self.skip_autorange:
                    ar_state = vb.state["autoRange"][1]
                    # if ar_state:
                    #     vb.autoRange(axis=vb.YAxis)

        # Update the legend
        self._update_signals_text(self.last_time_value)

        # Update encoder count to motor step conversion factor measurement
        if self.ui.chkEctsTurn.isChecked():
            addr = self.collector.channels[
                self.collector.current_channel
            ].icepap_address
            step_now = self.collector.icepap_system.icepap_system[addr].get_pos("AXIS")
            cfgANSTEP = int(
                self.collector.icepap_system.icepap_system[addr].get_cfg("ANSTEP")[
                    "ANSTEP"
                ]
            )
            cfgANTURN = int(
                self.collector.icepap_system.icepap_system[addr].get_cfg("ANTURN")[
                    "ANTURN"
                ]
            )
            enc_sel = str(self.ui.cb_enc_sel.currentText())
            try:
                enc_now = self.collector.icepap_system.icepap_system[addr].get_enc(
                    enc_sel
                )
            except Exception as e:
                msg = "Error querying encoder.\n{}".format(e)
                print(msg)
                return
            if self.ecpmt_just_enabled:
                self.step_ini = step_now
                self.enc_ini = enc_now
                self.ecpmt_just_enabled = False
                print(self.step_ini, self.enc_ini)
            if (step_now - self.step_ini) != 0:
                enc_cts_per_motor_turn = (
                    (enc_now - self.enc_ini)
                    * 1.0
                    * cfgANSTEP
                    / ((step_now - self.step_ini) * cfgANTURN)
                )
            else:
                enc_cts_per_motor_turn = 0
            self.ui.txtEctsTurn.setText(str(enc_cts_per_motor_turn))
            self.ui.txtEctsTurn.setCursorPosition(0)

    def _update_curves_values(self, x_min, x_max):
        if self.csv_mode:
            return
        previous_y_mode = self._get_y_axes_ranging_mode()
        corr_factors_need_update = False
        manual = self._read_manual_factors()
        if manual != self._manual_factors:
            self._manual_factors = manual
            self._update_correction_entries()
            corr_factors_need_update = True
        if self._corr_state_changed:
            corr_factors_need_update = True
            self._corr_state_changed = False
        # If the corrector factors were toggled while in ytile,
        # we force yautorange once and then we ytile again
        if self._force_tiled_viewbox_y_ranges_after_corr_factors_change:
            if self._tiled_viewbox_y_ranges_changed():
                self._tile_viewbox_yranges()
                self._force_tiled_viewbox_y_ranges_after_corr_factors_change = False

        # Update the curves.
        for ci in self.curve_items:
            if corr_factors_need_update:
                try:
                    ci.update_curve(x_min, x_max, corr_state=self._corr_state)
                except ValueError:
                    # Min on empty signal
                    pass
                self._update_signals_text(self.last_time_value)
            else:
                ci.update_curve(x_min, x_max)
        if corr_factors_need_update:
            self._restore_y_axes_ranging_mode(previous_y_mode)

    def _toggle_corr_factors(self):
        if not self._state_list:
            self._corr_state = -1
        elif self._corr_state == -1:
            self._corr_state = 0
        else:
            self._corr_state += 1
            if self._corr_state >= len(self._state_list):
                self._corr_state = -1
        self._corr_state_changed = True
        self._update_cf_status()

    def enable_ects_per_turn_calculation(self):
        if self.ui.chkEctsTurn.isChecked():
            self.ecpmt_just_enabled = True

    def _set_axis_autoscale(self):
        axis = self.ui.cbAxisCtrlSelect.currentText()
        if axis.startswith("Y"):
            # Yn axis
            self._enable_y_autoranging(int(axis[1]))
        else:
            # X axis
            self._enable_x_autorange()

    def _axis_offs_pp(self):
        self._chg_axis_offs(+0.1)

    def _axis_offs_mm(self):
        self._chg_axis_offs(-0.1)

    def _axis_scale_pp(self):
        self._chg_axis_scale(1 / 1.25)

    def _axis_scale_mm(self):
        self._chg_axis_scale(1.25)

    def _chg_axis_offs(self, offsfact):
        axis, amin, amax = self._get_axis_range()
        c = (amin + amax) / 2
        d = (amax - amin) / 2
        c += d * 2 * offsfact
        if axis < len(self.axes):
            # Yn axis
            self.view_boxes[axis].setYRange(c - d, c + d, padding=0)
        else:
            # X axis
            self.view_boxes[0].setXRange(c - d, c + d, padding=0)

    def _tile_viewbox_yranges(self):
        used_yaxes = []
        for i in range(0, len(self.view_boxes)):
            if not self.y_axis_empty(i + 1):
                used_yaxes.append(i)
        vertical_slots = len(used_yaxes)
        self.vertical_slots = len(used_yaxes)
        fill_factor = 2
        yslot = 0
        # This code assumes there has been a normal yautorange before in all yaxes
        # for the calculations.
        axis_data_ranges = {}
        x_min, x_max = self.view_boxes[0].viewRange()[0]
        if self.csv_mode:
            for entry in self._static_entries:
                x = entry["x"]
                y = entry["y"]
                if x.size == 0 or y.size == 0:
                    continue
                yaxis_idx = entry["axis"] - 1
                if yaxis_idx in self.skip_autorange:
                    continue
                mask = (x >= x_min) & (x <= x_max)
                if not np.any(mask):
                    continue
                y_visible = y[mask]
                if y_visible.size == 0:
                    continue
                data_min = float(np.min(y_visible))
                data_max = float(np.max(y_visible))
                if yaxis_idx not in axis_data_ranges:
                    axis_data_ranges[yaxis_idx] = [data_min, data_max]
                else:
                    axis_data_ranges[yaxis_idx][0] = min(
                        axis_data_ranges[yaxis_idx][0], data_min
                    )
                    axis_data_ranges[yaxis_idx][1] = max(
                        axis_data_ranges[yaxis_idx][1], data_max
                    )
        else:
            for ci in self.curve_items:
                if not ci.array_val_corr:
                    continue
                yaxis_idx = ci.y_axis - 1
                if yaxis_idx in self.skip_autorange:
                    continue
                start_idx = ci.get_time_index(x_min)
                end_idx = ci.get_time_index(x_max)
                start_idx = max(0, start_idx)
                end_idx = min(len(ci.array_val_corr), end_idx)
                if start_idx >= end_idx:
                    continue
                visible_values = ci.array_val_corr[start_idx:end_idx]
                if not visible_values:
                    continue
                data_min = min(visible_values)
                data_max = max(visible_values)
                if yaxis_idx not in axis_data_ranges:
                    axis_data_ranges[yaxis_idx] = [data_min, data_max]
                else:
                    axis_data_ranges[yaxis_idx][0] = min(
                        axis_data_ranges[yaxis_idx][0], data_min
                    )
                    axis_data_ranges[yaxis_idx][1] = max(
                        axis_data_ranges[yaxis_idx][1], data_max
                    )

        manual_active = self._y_tile_refresh_active
        for yaxis in range(0, len(self.view_boxes)):
            if yaxis in used_yaxes and yaxis not in self.skip_autorange:
                if manual_active:
                    current_range = self.view_boxes[yaxis].viewRange()[1]
                    last_range = self.last_tiled_y_ranges[yaxis]
                    if (
                        last_range != [0, 0]
                        and yaxis not in self._y_manual_axes
                        and (
                            abs(current_range[0] - last_range[0]) > 1e-9
                            or abs(current_range[1] - last_range[1]) > 1e-9
                        )
                    ):
                        # User changed this axis range manually; stop auto-updating it
                        # until the Y scaling mode changes.
                        self._y_manual_axes.add(yaxis)
                        self.last_tiled_y_ranges[yaxis] = list(current_range)
                    if yaxis in self._y_manual_axes:
                        # Keep the slot reserved but skip auto-ranging this axis.
                        self.last_tiled_y_ranges[yaxis] = list(current_range)
                        yslot = yslot + 1
                        continue
                if yaxis in axis_data_ranges:
                    [amin, amax] = axis_data_ranges[yaxis]
                else:
                    [amin, amax] = self.view_boxes[yaxis].viewRange()[1]
                if amin == amax:
                    amax = amin + 1
                old_center = amin + (amax - amin) / 2
                old_range = amax - amin
                range_slots = (amax - amin) * vertical_slots
                slots_above = 1 + 2 * yslot
                slots_below = 2 * vertical_slots - yslot * 2 - 1
                new_amax = old_center + slots_above * old_range / fill_factor
                new_amin = old_center - slots_below * old_range / fill_factor
                # print(yaxis, fill_factor, slots_above, slots_below, new_amin, new_amax, amin, amax, amax-amin, range_slots, range_slots*fill_factor, old_center )
                yslot = yslot + 1
                self.last_tiled_y_ranges[yaxis] = [new_amin, new_amax]
                self.view_boxes[yaxis].setYRange(new_amin, new_amax, padding=0)
            else:
                self.last_tiled_y_ranges[yaxis] = [0, 0]
        self.ytiled_viewbox_next = False
        if self._y_tile_refresh_active:
            self.ui.btnResetY.setText("yAUTO")
        self._update_y_status()

    def _tiled_viewbox_y_ranges_changed(self):
        ranges_changed = False
        for i in range(0, len(self.view_boxes)):
            current_range = self.view_boxes[i].viewRange()[1]
            if self.last_tiled_y_ranges[i] == [0, 0]:
                continue
            elif self.last_tiled_y_ranges[i] != current_range:
                ranges_changed = True
        first_pass = True
        for i in range(0, len(self.view_boxes)):
            if self.last_tiled_y_ranges[i] != [0, 0]:
                first_pass = False
        return ranges_changed or first_pass

    def _chg_axis_scale(self, scalefact):
        axis, amin, amax = self._get_axis_range()
        c = (amin + amax) / 2
        d = (amax - amin) / 2 * scalefact
        if axis < len(self.axes):
            # Yn axis
            self.view_boxes[axis].setYRange(c - d, c + d, padding=0)
        else:
            # X axis
            self.view_boxes[0].setXRange(c - d, c + d, padding=0)

    def _get_axis_range(self):
        axis = self.ui.cbAxisCtrlSelect.currentIndex()
        if axis < len(self.axes):
            # Yn axis
            [amin, amax] = self.view_boxes[axis].viewRange()[1]
        else:
            # X axis
            [amin, amax] = self.view_boxes[0].viewRange()[0]
        return axis, amin, amax

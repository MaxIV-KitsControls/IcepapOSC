#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""FFT helper tool for IcePAP OSC."""

from __future__ import absolute_import

import numpy as np
import pyqtgraph as pg

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QAction,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFileDialog,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QWidget,
    QMenuBar,
    QInputDialog,
    QApplication,
)
import os
import time
from PyQt5.QtGui import QKeySequence
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QEvent
from .utils import _format_csv_value

__all__ = ["FFTTool"]


def compute_fft(xs, ys):
    dxs = np.diff(xs)
    if dxs.size == 0:
        raise ValueError("Not enough samples for FFT")
    dx = float(np.mean(dxs))
    if dx == 0:
        raise ValueError("Zero spacing in X data")
    freq = np.fft.rfftfreq(len(ys), d=dx)
    spec = np.fft.rfft(ys)
    return freq, np.abs(spec)


def apply_bandpass(freq, spec, bandpass):
    try:
        spec = np.array(spec, copy=True)
        freq = np.array(freq, copy=False)
    except Exception:
        return spec
    if spec.size == 0:
        return spec
    low, high = bandpass
    if low is not None:
        spec[freq <= low] = 0
    if high is not None and np.isfinite(high):
        spec[freq >= high] = 0
    return spec


def _visible_slice(xs, ys, x_min, x_max):
    if xs.size == 0 or ys.size == 0:
        return None, None
    mask = (xs >= x_min) & (xs <= x_max)
    if not np.any(mask):
        return None, None
    return xs[mask], ys[mask]


class FFTTool(QtCore.QObject):
    """Adds an FFT picker and window."""

    def __init__(self, trend):
        super().__init__(trend)
        self.trend = trend
        self._plot_item = None
        self._dlg = None
        self._list = None
        self._fft_win = None
        self._fft_plot = None
        self._fft_legend = None
        self._fft_table = None
        self._fft_x_label = None
        self._fft_vline = None
        self._fft_proxy = None
        self._fft_series = []
        self._last_fft = []
        self._last_selection = []
        self._save_action = None
        self._bandpass = (0.0, None)
        self._bandpass_action = None
        self._log_y = False
        self._log_action = None
        self._fft_log_action = None

    def attachToPlotItem(self, plot_item):
        self._plot_item = plot_item
        menu = plot_item.getViewBox().menu

        self._fft_action = QAction("FFT...", self.trend)
        self._fft_action.setShortcut(QKeySequence("Ctrl+F"))
        self._fft_action.triggered.connect(lambda: self._open_dialog(plot_item))
        menu.addAction(self._fft_action)
        self.trend.addAction(self._fft_action)

        self._refresh_action = QAction("Refresh FFT", self.trend)
        self._refresh_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self._refresh_action.triggered.connect(self._refresh_fft)
        self._refresh_action.setEnabled(False)
        menu.addAction(self._refresh_action)
        self.trend.addAction(self._refresh_action)

    def _open_dialog(self, plot_item):
        curves = self._source_items()
        if self._dlg is None:
            self._dlg = QDialog(self.trend)
            self._dlg.setWindowTitle("Select curves for FFT")
            self._list = QListWidget(self._dlg)
            self._list.setSelectionMode(QListWidget.MultiSelection)
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self._dlg
            )
            buttons.accepted.connect(lambda: self._run_fft(plot_item))
            buttons.accepted.connect(self._dlg.accept)
            buttons.rejected.connect(self._dlg.reject)
            layout = QVBoxLayout(self._dlg)
            layout.addWidget(self._list)
            layout.addWidget(buttons)
        else:
            self._list.clear()

        for ci in curves:
            name = self._item_name(ci)
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, ci)
            item.setCheckState(Qt.Unchecked)
            self._list.addItem(item)

        self._dlg.show()
        self._dlg.raise_()
        self._dlg.activateWindow()

    def _run_fft(self, plot_item):
        self._last_fft = []
        self._last_selection = []
        x_min, x_max = plot_item.getViewBox().viewRange()[0]

        skipped = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.checkState() != Qt.Checked:
                continue
            ci = item.data(Qt.UserRole)
            xs, ys = self._item_data(ci)
            xs, ys = _visible_slice(xs, ys, x_min, x_max)
            if xs is None or len(xs) < 2:
                skipped.append(item.text())
                continue
            try:
                freq, spec = compute_fft(xs, ys)
                spec = apply_bandpass(freq, spec, self._bandpass)
            except Exception:
                skipped.append(item.text())
                continue
            pen = self._item_pen(ci)
            self._last_fft.append((item.text(), freq, spec, pen, ci))
            self._last_selection.append(ci)

        if not self._last_fft:
            QMessageBox.warning(
                self.trend, "FFT", "No valid curves selected for FFT."
            )
            return
        if skipped:
            QMessageBox.information(
                self.trend,
                "FFT",
                "Skipped curves: {}".format(", ".join(skipped)),
            )

        self._show_fft_window()
        self._refresh_action.setEnabled(True)

    def _show_fft_window(self):
        if self._fft_win is None:
            self._fft_win = QDialog(self.trend)
            self._fft_win.setWindowTitle("FFT")
            self._fft_win.setWindowFlags(
                self._fft_win.windowFlags() | Qt.WindowMinMaxButtonsHint
            )
            layout = QVBoxLayout(self._fft_win)
            menu_bar = QMenuBar(self._fft_win)
            fft_menu = menu_bar.addMenu("FFT")
            self._bandpass_action = QAction("Set FFT bandpass...", self._fft_win)
            self._bandpass_action.triggered.connect(self._set_bandpass)
            fft_menu.addAction(self._bandpass_action)
            self._log_action = QAction("FFT log Y", self._fft_win, checkable=True)
            self._log_action.setChecked(self._log_y)
            self._log_action.toggled.connect(self._toggle_log_y)
            fft_menu.addAction(self._log_action)
            fft_menu.addSeparator()
            self._save_action = QAction("Save FFT to CSV", self._fft_win)
            self._save_action.setShortcut(QKeySequence("Ctrl+O"))
            self._save_action.triggered.connect(self._save_fft)
            fft_menu.addAction(self._save_action)
            self._refresh_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
            fft_menu.addAction(self._refresh_action)
            layout.addWidget(menu_bar)
            self._fft_plot = pg.PlotWidget()
            self._fft_plot.setBackground("k")
            try:
                self._fft_plot.getPlotItem().getAxis("bottom").setPen("w")
                self._fft_plot.getPlotItem().getAxis("left").setPen("w")
            except Exception:
                pass
            layout.addWidget(self._fft_plot, 1)
            self._init_inspector_panel()
            self._fft_win.addAction(self._save_action)
            self._fft_win.addAction(self._refresh_action)
            try:
                menu = self._fft_plot.getPlotItem().getViewBox().menu
                self._fft_log_action = QAction("FFT log Y", self._fft_win, checkable=True)
                self._fft_log_action.setChecked(self._log_y)
                self._fft_log_action.toggled.connect(self._toggle_log_y)
                menu.addAction(self._fft_log_action)
            except Exception:
                self._fft_log_action = None
        else:
            self._fft_plot.clear()
            self._fft_legend = None
            self._fft_vline = None

        self._fft_series = []
        if self._fft_legend is None:
            try:
                self._fft_legend = self._fft_plot.addLegend()
            except Exception:
                self._fft_legend = None
        for name, freq, spec, pen, _ci in self._last_fft:
            self._fft_plot.plot(freq, spec, pen=pen, name=name)
            self._fft_series.append((name, freq, spec, pen))
        self._colorize_legend()
        self._sync_inspector_rows()
        self._ensure_fft_vline()
        self._apply_log_mode()

        self._fft_win.show()
        self._fft_win.raise_()
        self._fft_win.activateWindow()
        self._position_overlay()

    def _ensure_fft_vline(self):
        if self._fft_plot is None:
            return
        if self._fft_vline is None:
            self._fft_vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("w"))
            self._fft_vline.setZValue(10)
            self._fft_plot.addItem(self._fft_vline, ignoreBounds=True)

    def _refresh_fft(self):
        if not self._last_selection or self._plot_item is None:
            return
        if self._dlg is None:
            self._dlg = QDialog(self.trend)
        self._last_fft = []
        x_min, x_max = self._plot_item.getViewBox().viewRange()[0]
        skipped = []
        for ci in self._last_selection:
            xs, ys = self._item_data(ci)
            xs, ys = _visible_slice(xs, ys, x_min, x_max)
            if xs is None or len(xs) < 2:
                skipped.append(self._item_name(ci))
                continue
            try:
                freq, spec = compute_fft(xs, ys)
                spec = apply_bandpass(freq, spec, self._bandpass)
            except Exception:
                skipped.append(self._item_name(ci))
                continue
            pen = self._item_pen(ci)
            self._last_fft.append((self._item_name(ci), freq, spec, pen, ci))
        if skipped:
            QMessageBox.information(
                self.trend,
                "FFT",
                "Skipped curves: {}".format(", ".join(skipped)),
            )
        self._show_fft_window()

    def _toggle_log_y(self, enabled):
        self._log_y = bool(enabled)
        self._apply_log_mode()
        if self._log_action is not None:
            self._log_action.setChecked(self._log_y)
        if self._fft_log_action is not None:
            self._fft_log_action.setChecked(self._log_y)

    def _apply_log_mode(self):
        if self._fft_plot is None:
            return
        try:
            self._fft_plot.setLogMode(False, self._log_y)
        except Exception:
            try:
                self._fft_plot.getPlotItem().setLogMode(False, self._log_y)
            except Exception:
                pass

    def _save_fft(self):
        if not self._last_fft:
            return
        filename = self._build_quicksave_path("_fft")
        print(filename)
        content = {}
        for _name, freq, spec, _pen, ci in self._last_fft:
            key_base = self._header_base(ci)
            content["time-{}_fft".format(key_base)] = list(freq)
            content["val-{}_fft".format(key_base)] = list(spec)
        max_len = max(len(v) for v in content.values())
        for key, data in list(content.items()):
            content[key] = data + [np.nan] * (max_len - len(data))
        with open(filename, "w+") as f:
            f.write("," + ",".join(content.keys()) + "\n")
            for i in range(max_len):
                line = str(i)
                for key in content:
                    line += ",{}".format(_format_csv_value(content[key][i]))
                f.write(line + "\n")

    def _header_base(self, ci):
        if hasattr(ci, "driver_addr") and hasattr(ci, "signal_name"):
            signal = str(ci.signal_name).replace("-", "_").replace(":", "_").replace(" ", "_")
            return "{}-{}".format(ci.driver_addr, signal)
        name = self._item_name(ci)
        return name.replace("-", "_").replace(":", "_").replace(" ", "_")

    def _source_items(self):
        if getattr(self.trend, "csv_mode", False):
            getter = getattr(self.trend, "get_static_items", None)
            return getter() if getter else []
        return list(self.trend.curve_items)

    def _item_name(self, ci):
        if hasattr(ci, "signature"):
            return ci.signature
        if hasattr(ci, "name"):
            try:
                name = ci.name()
                if name:
                    return name
            except Exception:
                pass
        return "signal"

    def _item_data(self, ci):
        if hasattr(ci, "array_time") and hasattr(ci, "array_val_corr"):
            return np.array(ci.array_time, dtype=float), np.array(ci.array_val_corr, dtype=float)
        try:
            x, y = ci.getData()
        except Exception:
            return np.array([], dtype=float), np.array([], dtype=float)
        if x is None or y is None:
            return np.array([], dtype=float), np.array([], dtype=float)
        return np.array(x, dtype=float), np.array(y, dtype=float)

    def _item_pen(self, ci):
        pen = None
        if hasattr(ci, "curve"):
            pen = getattr(ci.curve, "opts", {}).get("pen", None)
        elif hasattr(ci, "opts"):
            pen = ci.opts.get("pen", None)
        try:
            return pg.mkPen(pen)
        except Exception:
            return pg.mkPen("w")

    def _build_quicksave_path(self, suffix):
        unitstr = "st"
        state_list = getattr(self.trend, "_state_list", [])
        state = getattr(self.trend, "_corr_state", -1)
        if state_list and state != -1:
            unitstr = str(state_list[state]).lower()
        driver = 0
        try:
            driver = int(self.trend.ui.cbDrivers.currentText())
        except Exception:
            pass
        hotkey = getattr(self.trend, "hotkey_filename", "default")
        base = "{}_{:03d}_{}_{}".format(
            time.strftime("%y%m%d_%H%M%S", time.localtime()),
            driver,
            hotkey,
            unitstr,
        )
        filename = "{}{}.csv".format(base, suffix)
        QApplication.clipboard().setText(filename)
        user_path = os.path.expanduser("~")
        base_folder = os.path.join(user_path, ".icepaposc")
        return os.path.join(base_folder, filename)

    def _colorize_legend(self):
        if not self._fft_legend:
            return
        for sample, label in getattr(self._fft_legend, "items", []):
            try:
                pen = sample.opts.get("pen", None)
                color = pg.mkPen(pen).color()
                label.setText(label.text, color=color)
            except Exception:
                continue

    def _set_bandpass(self):
        current = self._bandpass
        low = "" if current[0] is None else str(current[0])
        high = "" if current[1] is None else str(current[1])
        text, ok = QInputDialog.getText(
            self._fft_win or self.trend,
            "FFT bandpass",
            "Enter low,high (Hz). Empty means no limit:",
            text="{},{}".format(low, high),
        )
        if not ok:
            return
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 2:
            QMessageBox.warning(self._fft_win or self.trend, "FFT", "Use: low,high")
            return
        try:
            low_val = float(parts[0]) if parts[0] else None
            high_val = float(parts[1]) if parts[1] else None
        except ValueError:
            QMessageBox.warning(self._fft_win or self.trend, "FFT", "Invalid number")
            return
        self._bandpass = (low_val, high_val)
        if self._plot_item is not None:
            self._refresh_fft(self._plot_item)

    def _init_inspector_panel(self):
        self._fft_overlay = QWidget(self._fft_plot)
        self._fft_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._fft_overlay.setStyleSheet("background: transparent; color: white;")
        side_layout = QVBoxLayout(self._fft_overlay)
        side_layout.setContentsMargins(4, 2, 4, 2)
        side_layout.setSpacing(2)
        self._fft_x_label = QLabel("x = --", self._fft_overlay)
        self._fft_x_label.setStyleSheet("color: white;")
        self._fft_table = QTableWidget(self._fft_overlay)
        self._fft_table.setColumnCount(1)
        self._fft_table.setHorizontalHeaderLabels(["Value"])
        self._fft_table.horizontalHeader().setVisible(False)
        self._fft_table.verticalHeader().setVisible(False)
        self._fft_table.setShowGrid(False)
        self._fft_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._fft_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._fft_table.setFocusPolicy(Qt.NoFocus)
        self._fft_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._fft_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._fft_table.setStyleSheet(
            "QTableWidget { background: transparent; color: white; }"
            "QTableWidget::item { padding: 0px 8px 4px 8px; }"
        )
        header = self._fft_table.horizontalHeader()
        header.setStretchLastSection(True)
        side_layout.addWidget(self._fft_table, 0)
        side_layout.addWidget(self._fft_x_label)
        self._position_overlay()
        self._fft_plot.installEventFilter(self)
        self._fft_vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("w"))
        self._fft_vline.setZValue(10)
        self._fft_plot.addItem(self._fft_vline, ignoreBounds=True)
        self._fft_proxy = pg.SignalProxy(
            self._fft_plot.scene().sigMouseMoved, rateLimit=30, slot=self._mouse_moved
        )

    def _position_overlay(self):
        if not getattr(self, "_fft_overlay", None):
            return
        margin = 8
        geo = self._fft_plot.rect()
        width = max(180, int(geo.width() * 0.25))
        height = max(120, int(geo.height() * 0.35))
        x = geo.width() - width - margin
        y = geo.height() - height - margin
        legend = None
        try:
            legend = self._fft_plot.getPlotItem().legend
        except Exception:
            legend = self._fft_legend
        if legend is not None:
            try:
                legend_rect = legend.mapToScene(legend.boundingRect()).boundingRect()
                top_left = self._fft_plot.mapFromScene(legend_rect.topLeft())
                bottom_right = self._fft_plot.mapFromScene(legend_rect.bottomRight())
                leg_left = top_left.x()
                leg_top = top_left.y()
                leg_right = bottom_right.x()
                x = leg_right + margin
                y = leg_top
                if x + width > geo.width() - margin:
                    x = max(margin, leg_left - width - margin)
                if y + height > geo.height() - margin:
                    y = max(margin, geo.height() - height - margin)
            except Exception:
                pass
        height = self._overlay_height(height, geo.height() - 2 * margin)
        self._fft_overlay.setGeometry(x, y, width, height)

    def eventFilter(self, obj, event):
        if obj is self._fft_plot and event.type() == QEvent.Resize:
            self._position_overlay()
        return super().eventFilter(obj, event)

    def _sync_inspector_rows(self):
        if not self._fft_table:
            return
        series = self._ordered_series()
        self._fft_table.setRowCount(len(series))
        row_height = self._legend_row_height(len(series))
        for row, (_name, _xs, _ys, pen) in enumerate(series):
            value_item = QTableWidgetItem("")
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            try:
                color = pg.mkPen(pen).color()
                value_item.setForeground(color)
            except Exception:
                pass
            self._fft_table.setItem(row, 0, value_item)
            if row_height:
                self._fft_table.setRowHeight(row, row_height)
        self._sync_inspector_font()
        self._position_overlay()

    def _mouse_moved(self, evt):
        if self._fft_plot is None:
            return
        pos = evt[0]
        try:
            vb = self._fft_plot.plotItem.vb
            if not vb.sceneBoundingRect().contains(pos):
                return
            mouse_point = vb.mapSceneToView(pos)
        except Exception:
            mouse_point = self._fft_plot.plotItem.vb.mapSceneToView(pos)
        x_val = float(mouse_point.x())
        self._fft_x_label.setText("x = {:.6g}".format(x_val))
        if self._fft_vline is not None:
            self._fft_vline.setPos(x_val)
        if not self._fft_series:
            return
        for row, (_name, xs, ys, _pen) in enumerate(self._ordered_series()):
            item = self._fft_table.item(row, 0)
            if item is None:
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self._fft_table.setItem(row, 0, item)
            if xs is None or len(xs) == 0:
                item.setText("")
                continue
            idx = np.searchsorted(xs, x_val)
            if idx <= 0:
                closest = 0
            elif idx >= len(xs):
                closest = len(xs) - 1
            else:
                left = idx - 1
                right = idx
                closest = left if abs(xs[left] - x_val) <= abs(xs[right] - x_val) else right
            item.setText("{:.6g}".format(ys[closest]))

    def _ordered_series(self):
        if not self._fft_series:
            return []
        legend = None
        try:
            legend = self._fft_plot.getPlotItem().legend
        except Exception:
            legend = self._fft_legend
        if not legend or not getattr(legend, "items", None):
            return list(self._fft_series)
        order = []
        for _sample, label in legend.items:
            name = getattr(label, "text", None)
            if name:
                order.append(name)
        lookup = {name: (name, xs, ys, pen) for name, xs, ys, pen in self._fft_series}
        ordered = [lookup[name] for name in order if name in lookup]
        for name, xs, ys, pen in self._fft_series:
            if name not in order:
                ordered.append((name, xs, ys, pen))
        return ordered

    def _legend_row_height(self, rows):
        legend = None
        try:
            legend = self._fft_plot.getPlotItem().legend
        except Exception:
            legend = self._fft_legend
        if legend is None or rows <= 0:
            return None
        try:
            rect = legend.boundingRect()
            return max(14, int(rect.height() / rows))
        except Exception:
            return None

    def _sync_inspector_font(self):
        font = None
        legend = None
        try:
            legend = self._fft_plot.getPlotItem().legend
        except Exception:
            legend = self._fft_legend
        if legend and getattr(legend, "items", None):
            try:
                _sample, label = legend.items[0]
                if hasattr(label, "item") and hasattr(label.item, "font"):
                    font = label.item.font()
                elif hasattr(label, "font"):
                    font = label.font()
            except Exception:
                font = None
        if font is not None:
            self._fft_table.setFont(font)
            self._fft_x_label.setFont(font)

    def _overlay_height(self, fallback, max_height):
        if not self._fft_table or not self._fft_x_label:
            return min(fallback, max_height)
        layout = self._fft_overlay.layout()
        if layout is None:
            return min(fallback, max_height)
        margins = layout.contentsMargins()
        spacing = layout.spacing()
        rows = self._fft_table.rowCount()
        if rows <= 0:
            table_h = 0
        else:
            table_h = sum(self._fft_table.rowHeight(i) for i in range(rows))
        label_h = self._fft_x_label.sizeHint().height()
        height = (
            margins.top()
            + margins.bottom()
            + table_h
            + label_h
            + (spacing if rows > 0 else 0)
        )
        return min(max(height, 40), max_height)

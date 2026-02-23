#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Derivative helper tool for IcePAP OSC."""

from __future__ import absolute_import

import numpy as np
import pyqtgraph as pg

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
    QApplication,
    QMenuBar,
)
from PyQt5.QtGui import QKeySequence
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QEvent
from .utils import _format_csv_value
from .axis_time import AxisTime
import os
import time
import datetime

__all__ = ["DerivativeTool"]


def compute_derivative(xs, ys):
    dx = np.diff(xs)
    dy = np.diff(ys)
    if dx.size == 0:
        raise ValueError("Not enough samples for derivative")
    if np.any(dx == 0):
        raise ValueError("Zero spacing in X data")
    deriv = dy / dx
    xmid = xs[:-1] + dx * 0.5
    return xmid, deriv


def _visible_slice(xs, ys, x_min, x_max):
    if xs.size == 0 or ys.size == 0:
        return None, None
    mask = (xs >= x_min) & (xs <= x_max)
    if not np.any(mask):
        return None, None
    return xs[mask], ys[mask]


class DerivativeTool(QtCore.QObject):
    """Adds a derivative picker and window."""

    def __init__(self, trend):
        super().__init__(trend)
        self.trend = trend
        self._plot_item = None
        self._dlg = None
        self._list = None
        self._deriv_win = None
        self._deriv_plot = None
        self._deriv_legend = None
        self._deriv_table = None
        self._deriv_x_label = None
        self._deriv_vline = None
        self._deriv_proxy = None
        self._deriv_series = []
        self._last_deriv = []
        self._last_selection = []
        self._save_action = None

    def attachToPlotItem(self, plot_item):
        self._plot_item = plot_item
        menu = plot_item.getViewBox().menu

        self._deriv_action = QAction("Derivative...", self.trend)
        self._deriv_action.setShortcut(QKeySequence("Ctrl+D"))
        self._deriv_action.triggered.connect(lambda: self._open_dialog(plot_item))
        menu.addAction(self._deriv_action)
        self.trend.addAction(self._deriv_action)

        self._refresh_action = QAction("Refresh Derivative", self.trend)
        self._refresh_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self._refresh_action.triggered.connect(self._refresh_derivative)
        self._refresh_action.setEnabled(False)
        menu.addAction(self._refresh_action)
        self.trend.addAction(self._refresh_action)

    def _open_dialog(self, plot_item):
        curves = self._source_items()
        if self._dlg is None:
            self._dlg = QDialog(self.trend)
            self._dlg.setWindowTitle("Select curves for derivative")
            self._list = QListWidget(self._dlg)
            self._list.setSelectionMode(QListWidget.MultiSelection)
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self._dlg
            )
            buttons.accepted.connect(lambda: self._run_derivative(plot_item))
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

    def _run_derivative(self, plot_item):
        self._last_deriv = []
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
                dx, dy = compute_derivative(xs, ys)
            except Exception:
                skipped.append(item.text())
                continue
            pen = self._item_pen(ci)
            self._last_deriv.append((item.text(), dx, dy, pen, ci))
            self._last_selection.append(ci)

        if not self._last_deriv:
            QMessageBox.warning(
                self.trend, "Derivative", "No valid curves selected."
            )
            return
        if skipped:
            QMessageBox.information(
                self.trend,
                "Derivative",
                "Skipped curves: {}".format(", ".join(skipped)),
            )

        self._show_derivative_window()
        self._refresh_action.setEnabled(True)

    def _show_derivative_window(self):
        if self._deriv_win is None:
            self._deriv_win = QDialog(self.trend)
            self._deriv_win.setWindowTitle("Derivative")
            self._deriv_win.setWindowFlags(
                self._deriv_win.windowFlags() | Qt.WindowMinMaxButtonsHint
            )
            layout = QVBoxLayout(self._deriv_win)
            menu_bar = QMenuBar(self._deriv_win)
            deriv_menu = menu_bar.addMenu("Derivative")
            self._save_action = QAction("Save Derivative to CSV", self._deriv_win)
            self._save_action.setShortcut(QKeySequence("Ctrl+O"))
            self._save_action.triggered.connect(self._save_derivative)
            deriv_menu.addAction(self._save_action)
            self._refresh_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
            deriv_menu.addAction(self._refresh_action)
            layout.addWidget(menu_bar)
            axis_time = AxisTime(orientation="bottom")
            self._deriv_plot = pg.PlotWidget(axisItems={"bottom": axis_time})
            self._deriv_plot.setBackground("k")
            try:
                self._deriv_plot.getPlotItem().getAxis("bottom").setPen("w")
                self._deriv_plot.getPlotItem().getAxis("left").setPen("w")
            except Exception:
                pass
            layout.addWidget(self._deriv_plot, 1)
            self._init_inspector_panel()
            self._deriv_win.addAction(self._save_action)
            self._deriv_win.addAction(self._refresh_action)
        else:
            self._deriv_plot.clear()
            self._deriv_proxy = None
            self._deriv_legend = None
            self._deriv_vline = None

        self._deriv_series = []
        if self._deriv_legend is None:
            try:
                self._deriv_legend = self._deriv_plot.addLegend()
            except Exception:
                self._deriv_legend = None
        for name, xs, ys, pen, _ci in self._last_deriv:
            self._deriv_plot.plot(xs, ys, pen=pen, name=name)
            self._deriv_series.append((name, xs, ys, pen))
        self._colorize_legend()
        self._sync_inspector_rows()
        self._ensure_deriv_vline()

        self._deriv_win.show()
        self._deriv_win.raise_()
        self._deriv_win.activateWindow()
        self._position_overlay()
        self._attach_mouse_tracking()

    def _ensure_deriv_vline(self):
        if self._deriv_plot is None:
            return
        if self._deriv_vline is None:
            self._deriv_vline = pg.InfiniteLine(
                angle=90, movable=False, pen=pg.mkPen("w")
            )
            self._deriv_vline.setZValue(10)
            self._deriv_plot.addItem(self._deriv_vline, ignoreBounds=True)

    def _attach_mouse_tracking(self):
        if self._deriv_plot is None:
            return
        # Recreate proxy to ensure it's bound to the current scene
        self._deriv_proxy = pg.SignalProxy(
            self._deriv_plot.scene().sigMouseMoved,
            rateLimit=30,
            slot=self._mouse_moved,
        )

    def _refresh_derivative(self):
        if not self._last_selection or self._plot_item is None:
            return
        self._last_deriv = []
        x_min, x_max = self._plot_item.getViewBox().viewRange()[0]
        skipped = []
        for ci in self._last_selection:
            xs, ys = self._item_data(ci)
            xs, ys = _visible_slice(xs, ys, x_min, x_max)
            if xs is None or len(xs) < 2:
                skipped.append(self._item_name(ci))
                continue
            try:
                dx, dy = compute_derivative(xs, ys)
            except Exception:
                skipped.append(self._item_name(ci))
                continue
            pen = self._item_pen(ci)
            self._last_deriv.append((self._item_name(ci), dx, dy, pen, ci))
        if skipped:
            QMessageBox.information(
                self.trend,
                "Derivative",
                "Skipped curves: {}".format(", ".join(skipped)),
            )
        self._show_derivative_window()

    def _save_derivative(self):
        if not self._last_deriv:
            return
        filename = self._build_quicksave_path("_der")
        print(filename)
        content = {}
        for _name, xs, ys, _pen, ci in self._last_deriv:
            key_base = self._header_base(ci)
            content["time-{}_der".format(key_base)] = list(xs)
            content["val-{}_der".format(key_base)] = list(ys)
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
        if not self._deriv_legend:
            return
        for sample, label in getattr(self._deriv_legend, "items", []):
            try:
                pen = sample.opts.get("pen", None)
                color = pg.mkPen(pen).color()
                label.setText(label.text, color=color)
            except Exception:
                continue

    def _init_inspector_panel(self):
        self._deriv_overlay = QWidget(self._deriv_plot)
        self._deriv_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._deriv_overlay.setStyleSheet("background: transparent; color: white;")
        side_layout = QVBoxLayout(self._deriv_overlay)
        side_layout.setContentsMargins(4, 2, 4, 2)
        side_layout.setSpacing(2)
        self._deriv_x_label = QLabel("x = --", self._deriv_overlay)
        self._deriv_x_label.setStyleSheet("color: white;")
        self._deriv_table = QTableWidget(self._deriv_overlay)
        self._deriv_table.setColumnCount(1)
        self._deriv_table.setHorizontalHeaderLabels(["Value"])
        self._deriv_table.horizontalHeader().setVisible(False)
        self._deriv_table.verticalHeader().setVisible(False)
        self._deriv_table.setShowGrid(False)
        self._deriv_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._deriv_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._deriv_table.setFocusPolicy(Qt.NoFocus)
        self._deriv_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._deriv_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._deriv_table.setStyleSheet(
            "QTableWidget { background: transparent; color: white; }"
            "QTableWidget::item { padding: 0px 8px 4px 8px; }"
        )
        header = self._deriv_table.horizontalHeader()
        header.setStretchLastSection(True)
        side_layout.addWidget(self._deriv_table, 0)
        side_layout.addWidget(self._deriv_x_label)
        self._position_overlay()
        self._deriv_plot.installEventFilter(self)
        self._deriv_vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("w"))
        self._deriv_vline.setZValue(10)
        self._deriv_plot.addItem(self._deriv_vline, ignoreBounds=True)
        if self._deriv_proxy is None:
            self._deriv_proxy = pg.SignalProxy(
                self._deriv_plot.scene().sigMouseMoved,
                rateLimit=30,
                slot=self._mouse_moved,
            )

    def _position_overlay(self):
        if not getattr(self, "_deriv_overlay", None):
            return
        margin = 8
        geo = self._deriv_plot.rect()
        width = max(180, int(geo.width() * 0.25))
        height = max(120, int(geo.height() * 0.35))
        x = geo.width() - width - margin
        y = geo.height() - height - margin
        legend = None
        try:
            legend = self._deriv_plot.getPlotItem().legend
        except Exception:
            legend = self._deriv_legend
        if legend is not None:
            try:
                legend_rect = legend.mapToScene(legend.boundingRect()).boundingRect()
                top_left = self._deriv_plot.mapFromScene(legend_rect.topLeft())
                bottom_right = self._deriv_plot.mapFromScene(legend_rect.bottomRight())
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
        self._deriv_overlay.setGeometry(x, y, width, height)

    def eventFilter(self, obj, event):
        if obj is self._deriv_plot and event.type() == QEvent.Resize:
            self._position_overlay()
        return super().eventFilter(obj, event)

    def _sync_inspector_rows(self):
        if not self._deriv_table:
            return
        series = self._ordered_series()
        self._deriv_table.setRowCount(len(series))
        row_height = self._legend_row_height(len(series))
        for row, (_name, _xs, _ys, pen) in enumerate(series):
            value_item = QTableWidgetItem("")
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            try:
                color = pg.mkPen(pen).color()
                value_item.setForeground(color)
            except Exception:
                pass
            self._deriv_table.setItem(row, 0, value_item)
            if row_height:
                self._deriv_table.setRowHeight(row, row_height)
        self._sync_inspector_font()
        self._position_overlay()

    def _mouse_moved(self, evt):
        if self._deriv_plot is None:
            return
        pos = evt[0]
        try:
            vb = self._deriv_plot.plotItem.vb
            if not vb.sceneBoundingRect().contains(pos):
                return
            mouse_point = vb.mapSceneToView(pos)
        except Exception:
            mouse_point = self._deriv_plot.plotItem.vb.mapSceneToView(pos)
        x_val = float(mouse_point.x())
        self._deriv_x_label.setText("x = {}".format(self._format_x_value(x_val)))
        if self._deriv_vline is not None:
            self._deriv_vline.setPos(x_val)
        if not self._deriv_series:
            return
        for row, (_name, xs, ys, _pen) in enumerate(self._ordered_series()):
            item = self._deriv_table.item(row, 0)
            if item is None:
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self._deriv_table.setItem(row, 0, item)
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
        if not self._deriv_series:
            return []
        legend = None
        try:
            legend = self._deriv_plot.getPlotItem().legend
        except Exception:
            legend = self._deriv_legend
        if not legend or not getattr(legend, "items", None):
            return list(self._deriv_series)
        order = []
        for _sample, label in legend.items:
            name = getattr(label, "text", None)
            if name:
                order.append(name)
        lookup = {name: (name, xs, ys, pen) for name, xs, ys, pen in self._deriv_series}
        ordered = [lookup[name] for name in order if name in lookup]
        for name, xs, ys, pen in self._deriv_series:
            if name not in order:
                ordered.append((name, xs, ys, pen))
        return ordered

    def _legend_row_height(self, rows):
        legend = None
        try:
            legend = self._deriv_plot.getPlotItem().legend
        except Exception:
            legend = self._deriv_legend
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
            legend = self._deriv_plot.getPlotItem().legend
        except Exception:
            legend = self._deriv_legend
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
            self._deriv_table.setFont(font)
            self._deriv_x_label.setFont(font)

    def _overlay_height(self, fallback, max_height):
        if not self._deriv_table or not self._deriv_x_label:
            return min(fallback, max_height)
        layout = self._deriv_overlay.layout()
        if layout is None:
            return min(fallback, max_height)
        margins = layout.contentsMargins()
        spacing = layout.spacing()
        rows = self._deriv_table.rowCount()
        if rows <= 0:
            table_h = 0
        else:
            table_h = sum(self._deriv_table.rowHeight(i) for i in range(rows))
        label_h = self._deriv_x_label.sizeHint().height()
        height = (
            margins.top()
            + margins.bottom()
            + table_h
            + label_h
            + (spacing if rows > 0 else 0)
        )
        return min(max(height, 40), max_height)

    def _format_x_value(self, x_val):
        axis = None
        try:
            axis = self._deriv_plot.getPlotItem().getAxis("bottom")
        except Exception:
            axis = None
        if isinstance(axis, AxisTime):
            try:
                date = datetime.datetime.fromtimestamp(x_val)
                return date.strftime("%H:%M:%S.%f")[:-3]
            except Exception:
                pass
        try:
            x_min, x_max = self._deriv_plot.plotItem.vb.viewRange()[0]
        except Exception:
            x_min, x_max = None, None
        spacing = None
        if axis is not None and x_min is not None and x_max is not None:
            try:
                size = axis.geometry().width()
                ticks = axis.tickValues(x_min, x_max, size)
                if ticks:
                    spacing = ticks[0][0]
            except Exception:
                spacing = None
        if spacing is None and x_min is not None and x_max is not None:
            spacing = abs(x_max - x_min)
        if axis is not None and spacing is not None:
            try:
                label = axis.tickStrings([x_val], 1.0, spacing)[0]
                if label != "":
                    return label
            except Exception:
                pass
        return "{:.6g}".format(x_val)

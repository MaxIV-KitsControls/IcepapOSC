#!/usr/bin/env python

"""Correction debug overlay tool."""

from __future__ import absolute_import

import pprint

from PyQt5 import QtCore, QtWidgets

__all__ = ["DebugTool"]


class DebugTool(QtCore.QObject):
    """Shows correction debug data toggled by Ctrl+Shift+H."""

    def __init__(self, window, overlay_widget):
        super().__init__(overlay_widget)
        self._window = window
        self._overlay_widget = overlay_widget
        self._label = QtWidgets.QPlainTextEdit(overlay_widget)
        self._label.setReadOnly(True)
        self._label.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self._label.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self._label.setStyleSheet(
            "background: rgba(10,10,10,0.9); color: #d7d7d7; "
            "padding: 8px; border-radius: 6px; font-family: monospace;"
        )
        self._label.hide()
        self._visible = False
        overlay_widget.installEventFilter(self)

    def _build_text(self):
        lines = [
            "Correction Debug",
            "Ctrl+Shift+H: Toggle debug overlay",
            "",
        ]
        entries = getattr(self._window, "_corr_entries", None)
        curves = getattr(self._window, "curve_items", None)
        if not entries or curves is None:
            lines.append("No correction data.")
            return "\n".join(lines)
        found = False
        for ci in curves:
            key = self._window._corr_key(ci.driver_addr, ci.signal_name)
            entry = entries.get(key)
            if entry is None:
                continue
            found = True
            lines.append(f"Signal: {ci.driver_addr}:{ci.signal_name}")
            lines.append(f"  profile: {entry.get('profile')}")
            lines.append(f"  source: {entry.get('source')}")
            if "states" in entry:
                lines.append(f"  states: {entry.get('states')}")
            lines.append("  factors:")
            factors = entry.get("factors", {})
            for line in pprint.pformat(factors, width=120).splitlines():
                lines.append(f"    {line}")
            manual = entry.get("manual")
            if manual:
                lines.append(f"  manual: {manual}")
            lines.append("")
        if not found:
            lines.append("No correction data.")
        return "\n".join(lines)

    def _position_overlay(self):
        margin = 10
        geo = self._overlay_widget.rect()
        size = self._label.sizeHint()
        x = margin
        max_height = int(geo.height() * 0.75)
        height = max_height
        y = geo.height() - height - margin
        max_width = int(geo.width() * 1.0)
        width = min(max(size.width(), int(geo.width() * 0.9)), max_width)
        self._label.setGeometry(x, y, min(width, geo.width() - 2 * margin), height)

    def _show(self):
        if self._visible:
            return
        self._visible = True
        self._label.setPlainText(self._build_text())
        self._position_overlay()
        self._label.show()

    def _hide(self):
        if not self._visible:
            return
        self._visible = False
        self._label.hide()

    def toggle(self):
        if self._visible:
            self._hide()
        else:
            self._show()

    def eventFilter(self, obj, event):
        if obj is self._overlay_widget and event.type() == QtCore.QEvent.Resize:
            if self._visible:
                self._position_overlay()
        return super().eventFilter(obj, event)

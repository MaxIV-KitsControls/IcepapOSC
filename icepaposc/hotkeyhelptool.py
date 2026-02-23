#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Hotkey overlay tool for quick reference."""

from __future__ import absolute_import

from PyQt5 import QtCore, QtWidgets

__all__ = ["HotkeyHelpTool"]


DEFAULT_TEXT = """Hotkeys
Ctrl+O: Save visible contents to CSV
Ctrl+Shift+O: Save raw + corrected states to CSV (OFF only)
Ctrl+I: Set quicksave filename
Ctrl+U: Cycle correction state (OFF->UNITS->STP->ECTS->...->OFF)
Ctrl+Y: Toggle Y autorange modes
Ctrl+T: Toggle X autorange/autopan
Ctrl+R / Ctrl+E: Zoom in/out X
Ctrl+Left Click: Snap min time border to cursor
Ctrl+F: FFT selector
Ctrl+Shift+F: Refresh FFT
Ctrl+D: Derivative selector
Ctrl+Shift+D: Refresh derivative
Ctrl+H: Toggle this help
Ctrl+Shift+H: Correction debug overlay
"""


class HotkeyHelpTool(QtCore.QObject):
    """Shows an overlay with hotkeys toggled by Ctrl+H."""

    def __init__(self, overlay_widget, text=DEFAULT_TEXT):
        super().__init__(overlay_widget)
        self._overlay_widget = overlay_widget
        self.text = text
        self._label = QtWidgets.QLabel(overlay_widget)
        self._label.setText(self.text)
        self._label.setWordWrap(True)
        self._label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self._label.setStyleSheet(
            "background: rgba(30,30,30,0.75); color: white; "
            "padding: 8px; border-radius: 6px; font-family: monospace;"
        )
        self._label.hide()
        self._visible = False
        overlay_widget.installEventFilter(self)

    def setText(self, text):
        self.text = text
        self._label.setText(text)

    def toggle(self):
        if self._visible:
            self._hide()
        else:
            self._show()

    def _show(self):
        if self._visible:
            return
        self._visible = True
        self._position_label()
        self._label.show()

    def _hide(self):
        if not self._visible:
            return
        self._visible = False
        self._label.hide()

    def _position_label(self):
        margin = 10
        geo = self._overlay_widget.rect()
        self._label.adjustSize()
        size = self._label.sizeHint()
        width = min(size.width(), max(0, geo.width() - 2 * margin))
        height = size.height()
        x = margin
        y = max(margin, geo.height() - height - margin)
        self._label.setGeometry(x, y, width, height)

    def eventFilter(self, obj, event):
        if obj is self._overlay_widget and event.type() == QtCore.QEvent.Resize:
            if self._visible:
                self._position_label()
        return super().eventFilter(obj, event)

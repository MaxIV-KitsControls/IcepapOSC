#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""CSV loader helper for static plot items."""

from __future__ import absolute_import

import csv
import os
import numpy as np
import pyqtgraph as pg

__all__ = ["load_csv_items", "inspect_csv_columns"]


def _read_csv_header(path):
    try:
        with open(path, newline="") as f:
            reader = csv.reader(f)
            return next(reader, [])
    except Exception as exc:
        raise IOError('Could not read CSV "{}": {}'.format(path, exc)) from exc


def _column_label(idx, header, names):
    if header and idx < len(header):
        label = (header[idx] or "").strip()
        if label:
            return label
    if names and idx < len(names):
        return names[idx]
    return "col{}".format(idx + 1)


def _load_csv_columns(path):
    header = _read_csv_header(path)
    header = [h for h in header] if header else []

    try:
        with open(path, newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            rows = [row for row in reader if any(cell.strip() for cell in row)]
    except Exception as exc:
        raise IOError('Could not read CSV "{}": {}'.format(path, exc)) from exc

    if not rows:
        raise ValueError('CSV "{}" contains no data'.format(path))

    n_cols = len(header)
    if n_cols == 0:
        n_cols = len(rows[0])
        header = ["col{}".format(idx + 1) for idx in range(n_cols)]

    for idx, row in enumerate(rows, start=2):
        if len(row) != n_cols:
            raise ValueError(
                'Row {} in "{}" has {} columns but expected {}'.format(
                    idx, path, len(row), n_cols
                )
            )

    columns = [[] for _ in range(n_cols)]
    for row in rows:
        for idx, cell in enumerate(row):
            try:
                val = float(cell)
            except Exception as exc:
                raise ValueError(
                    'Non-numeric value "{}" in column {} of "{}"'.format(
                        cell, idx + 1, path
                    )
                ) from exc
            columns[idx].append(val)

    columns = [np.array(col, copy=True) for col in columns]
    names = [h.strip() for h in header]
    return header, names, columns


def _looks_like_index(label):
    test = (label or "").strip().lower()
    return test == "" or test == "index" or test.startswith("unnamed")


def _signal_name_from_labels(time_label, value_label):
    prefixes = ("time-", "time_", "val-", "val_", "value-", "value_")
    tl = (time_label or "").strip()
    vl = (value_label or "").strip()
    tl_low = tl.lower()
    vl_low = vl.lower()
    for pref in prefixes:
        val_pref = pref.replace("time", "val")
        if tl_low.startswith(pref) and vl_low.startswith(val_pref):
            base_t = tl[len(pref) :]
            base_v = vl[len(val_pref) :]
            if base_t and base_t == base_v:
                return base_t
    for pref in prefixes:
        if vl_low.startswith(pref):
            base = vl[len(pref) :]
            if base:
                return base
    return vl or tl or "signal"


def _parse_signal_pairs(header, names, columns):
    n_columns = len(columns)
    start = 1 if _looks_like_index(header[0] if header else names[0] if names else "") else 0
    remaining = n_columns - start
    if remaining < 2 or remaining % 2 != 0:
        raise ValueError(
            "CSV must contain pairs of time/value columns (optional index in column 1)"
        )

    signals = []
    for base in range(start, n_columns, 2):
        x_idx = base
        y_idx = base + 1
        t_label = _column_label(x_idx, header, names)
        v_label = _column_label(y_idx, header, names)
        sig_label = _signal_name_from_labels(t_label, v_label)
        signals.append((x_idx, y_idx, sig_label))
    return signals


def _parse_cols(csv_cols, n_available):
    if not csv_cols:
        return list(range(n_available))
    cols = []
    for part in csv_cols.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            idx = int(part)
        except ValueError:
            raise ValueError('invalid signal index "{}" (must be integer)'.format(part))
        if idx <= 0 or idx > n_available:
            raise ValueError("signal index {} out of range (1..{})".format(idx, n_available))
        cols.append(idx - 1)
    return cols


def _color_for_index(idx):
    return pg.intColor(idx, hues=12)


def load_csv_items(path, csv_cols=None):
    """Read CSV and return a list of PlotDataItems.

    The expected layout is: an index column, followed by pairs of
    (time-of-signal, value-of-signal) columns. ``csv_cols`` is a comma-separated
    list of 1-based signal indices (not column indices). Each selected signal
    adds one curve using its value column as Y and its time column as X.
    """
    if not os.path.isfile(path):
        raise IOError('File "{}" not found'.format(path))

    header, names, columns = _load_csv_columns(path)
    signals = _parse_signal_pairs(header, names, columns)
    selected = _parse_cols(csv_cols, len(signals))

    items = []
    for idx, sel in enumerate(selected):
        x_idx, y_idx, label = signals[sel]
        x = np.array(columns[x_idx], copy=True)
        y = np.array(columns[y_idx], copy=True)
        pen = pg.mkPen(_color_for_index(idx))
        item = pg.PlotDataItem(x=x, y=y, name=label, pen=pen)
        items.append(item)
    return items


def inspect_csv_columns(path):
    """Return the signal labels (one per time/value pair) for --csv-lst."""
    if not os.path.isfile(path):
        raise IOError('File "{}" not found'.format(path))

    header, names, columns = _load_csv_columns(path)
    signals = _parse_signal_pairs(header, names, columns)
    return [label for _, _, label in signals]

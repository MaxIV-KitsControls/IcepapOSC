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

import collections
import numpy as np


def parse_signal_definition(sig_definition):
    parts = sig_definition.split(":")
    if len(parts) != 3:
        raise ValueError(
            'Bad format of predefined signal "{}". It should be: '
            "<driver>:<signal name>:<Y-axis>".format(sig_definition)
        )
    driver = int(parts[0])
    signal_name = parts[1]
    axis = int(parts[2])
    return driver, signal_name, axis


def load_signal_set_file(filename):
    signals = []
    force_black_background = False
    with open(filename, "r") as f:
        for line in f:
            tokens = line.split()
            if len(tokens) < 4 or tokens[0].startswith("#"):
                continue
            line_style_value = int(tokens[3]) % 2
            line_marker_value = int(tokens[3]) >> 1
            signal = {
                "signal_name": tokens[0],
                "axis": int(tokens[1]),
                "color": tokens[2],
                "line_style": line_style_value,
                "line_marker": line_marker_value,
            }
            signals.append(signal)
            if len(tokens) == 5:
                force_token = int(tokens[4]) % 2
                if force_token:
                    force_black_background = True
    return signals, force_black_background


def _format_csv_value(value):
    try:
        return format(value, ".17g")
    except (TypeError, ValueError):
        return ""


def write_curves_to_csv(curve_items, filename, time_range=None):
    if not curve_items:
        return
    # Build a column-oriented matrix of time/value pairs per signal.
    csv_matrix = collections.OrderedDict()
    for ci in curve_items:
        header_time = "time-{}-{}".format(ci.driver_addr, ci.signal_name)
        header_val = "val-{}-{}".format(ci.driver_addr, ci.signal_name)
        csv_matrix[header_time] = ci.array_time
        csv_matrix[header_val] = ci.array_val_corr

    # Abort early if no signal has data.
    non_empty_keys = [key for key, values in csv_matrix.items() if values]
    if not non_empty_keys:
        return
    # Pad all columns to the same length (max length across signals).
    max_len = max(len(csv_matrix[key]) for key in non_empty_keys)
    for key in csv_matrix:
        delta = max_len - len(csv_matrix[key])
        if delta > 0:
            csv_matrix[key] = delta * [np.nan] + csv_matrix[key]

    # Compute the row range to write (full or visible range).
    if time_range is None:
        idx_ini = 0
        idx_end = max_len
    else:
        # Use the first curve with time data to compute indices.
        idx_curve = next((ci for ci in curve_items if ci.array_time), None)
        if not idx_curve:
            return
        idx_ini = idx_curve.get_time_index(time_range[0])
        idx_end = idx_curve.get_time_index(time_range[1])
        idx_ini = max(0, min(idx_ini, max_len))
        idx_end = max(0, min(idx_end, max_len))

    # Write CSV header and rows.
    with open(filename, "w+") as csv_file:
        for key in csv_matrix:
            csv_file.write(",{}".format(key))
        csv_file.write("\n")
        for idx in range(idx_ini, idx_end):
            line = str(idx)
            for key in csv_matrix:
                line += ",{}".format(_format_csv_value(csv_matrix[key][idx]))
            csv_file.write(line + "\n")

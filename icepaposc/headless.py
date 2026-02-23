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

import os
import signal
import time

from PyQt5 import QtCore, QtGui
from icepap import IcePAPController

from .collector import Collector
from .curve_item import CurveItem
from .utils import write_curves_to_csv
from icepap.utils import State

class HeadlessRunner:
    """Execute acquisitions without launching the GUI."""

    def __init__(
        self,
        settings,
        host,
        port,
        timeout,
        signals,
        output_file,
        corr_factors=None,
        icepap_controller=None,
    ):
        self.settings = settings
        self.output_file = output_file
        self.curve_items = []
        self.curves_by_id = {}

        if icepap_controller is None:
            self._controller = IcePAPController(host, port, timeout, auto_axes=True)
        else:
            self._controller = icepap_controller
        self.collector = Collector(
            self.settings,
            self._collector_callback,
            icepap_controller=self._controller,
            use_qtimer=False,
        )

        self._correction_factors = corr_factors
        self._subscribe_signals(signals)

    def _subscribe_signals(self, signals):
        if not signals:
            raise RuntimeError("No signals defined for headless acquisition")

        for driver, signal, axis in signals:
            subscription_id = self.collector.subscribe(driver, signal)
            curve = CurveItem(
                subscription_id,
                driver,
                signal,
                axis,
                QtGui.QColor(0, 0, 0),
                QtCore.Qt.SolidLine,
                "",
            )
            if self._correction_factors:
                curve.corr_factors = list(self._correction_factors)
            self.curve_items.append(curve)
            self.curves_by_id[subscription_id] = curve
            self.collector.start(subscription_id)

    def _collector_callback(self, subscription_id, value_list):
        curve = self.curves_by_id.get(subscription_id)
        if curve:
            curve.collect(value_list)

    def _flush_pending_samples(self):
        for subscription_id, channel in self.collector.channels.items():
            if channel.collected_samples:
                self._collector_callback(subscription_id, channel.collected_samples)
                channel.collected_samples = []

    def run(self, acquisition_time):
        interval = max(self.settings.sample_rate / 1000.0, 0.001)
        start = time.time()
        stop = {"flag": False}
        prev_handler = signal.getsignal(signal.SIGINT)

        def _request_stop(_signum, _frame):
            stop["flag"] = True

        signal.signal(signal.SIGINT, _request_stop)
        print("Headless acquisition running. Press Ctrl+C to stop gracefully.")
        try:
            while time.time() - start < acquisition_time and not stop["flag"]:
                self.collector.tick_once()
                if stop["flag"]:
                    break
                time.sleep(interval)
        finally:
            signal.signal(signal.SIGINT, prev_handler)
            self._flush_pending_samples()
            self.collector.stop()
            write_curves_to_csv(self.curve_items, self.output_file)
            print(f"Written to {self.output_file}")
            _report_csv_write(self.output_file)


BATCH_SIGNAL_GETTER_MAP = [
    ("PosAxis", "_getter_pos_axis"),
    ("FPosAxis", "_getter_fpos_axis"),
    ("PosTgtenc", "_getter_pos_tgtenc"),
    ("FPosTgtenc", "_getter_fpos_tgtenc"),
    ("PosShftenc", "_getter_pos_shftenc"),
    ("FPosShftenc", "_getter_fpos_shftenc"),
    ("PosEncin", "_getter_pos_encin"),
    ("PosAbsenc", "_getter_pos_absenc"),
    ("PosInpos", "_getter_pos_inpos"),
    ("PosMotor", "_getter_pos_motor"),
    ("PosCtrlenc", "_getter_pos_ctrlenc"),
    ("PosMeasure", "_getter_pos_measure"),
    ("FPosMeasure", "_getter_fpos_measure"),
    ("EncEncin", "_getter_enc_encin"),
    ("EncAbsenc", "_getter_enc_absenc"),
    ("EncTgtenc", "_getter_enc_tgtenc"),
    ("EncInpos", "_getter_enc_inpos"),
    ("EncMeasure", "_getter_enc_measure"),
    ("StatReady", "_getter_stat_ready"),
    ("FStatReady", "_getter_fstat_ready"),
    ("StatMoving", "_getter_stat_moving"),
    ("FStatMoving", "_getter_fstat_moving"),
    ("StatSettling", "_getter_stat_settling"),
    ("FStatSettling", "_getter_fstat_settling"),
    ("StatOutofwin", "_getter_stat_outofwin"),
    ("FStatOutofwin", "_getter_fstat_outofwin"),
    ("StatLim+", "_getter_stat_limit_positive"),
    ("FStatLim+", "_getter_fstat_limit_positive"),
    ("StatLim-", "_getter_stat_limit_negative"),
    ("FStatLim-", "_getter_fstat_limit_negative"),
    ("StatHome", "_getter_stat_inhome"),
    ("FStatHome", "_getter_fstat_inhome"),
    ("StatStopcode", "_getter_stat_stopcode"),
    ("FStatStopcode", "_getter_fstat_stopcode"),
]


class HeadlessBatchGetters:
    def __init__(self, icepap_controller):
        self.icepap_system = icepap_controller
        self.sig_getters = {
            name: getattr(self, method_name) for name, method_name in BATCH_SIGNAL_GETTER_MAP
        }

    def _getter_pos_axis(self, addr, indices=None):
        x = self.icepap_system.get_pos(indices, "AXIS")
        return x

    def _getter_fpos_axis(self, addr, indices=None):
        x = self.icepap_system.get_fpos(indices, "AXIS")
        return x

    def _getter_pos_tgtenc(self, addr, indices=None):
        x = self.icepap_system.get_pos(indices, "TGTENC")
        return x

    def _getter_fpos_tgtenc(self, addr, indices=None):
        x = self.icepap_system.get_fpos(indices, "TGTENC")
        return x

    def _getter_pos_shftenc(self, addr, indices=None):
        x = self.icepap_system.get_pos(indices, "SHFTENC")
        return x

    def _getter_fpos_shftenc(self, addr, indices=None):
        x = self.icepap_system.get_fpos(indices, "SHFTENC")
        return x

    def _getter_pos_encin(self, addr, indices=None):
        x = self.icepap_system.get_pos(indices, "ENCIN")
        return x

    def _getter_pos_absenc(self, addr, indices=None):
        x = self.icepap_system.get_pos(indices, "ABSENC")
        return x

    def _getter_pos_inpos(self, addr, indices=None):
        x = self.icepap_system.get_pos(indices, "INPOS")
        return x

    def _getter_pos_motor(self, addr, indices=None):
        x = self.icepap_system.get_pos(indices, "MOTOR")
        return x

    def _getter_pos_ctrlenc(self, addr, indices=None):
        x = self.icepap_system.get_pos(indices, "CTRLENC")
        return x

    def _getter_pos_measure(self, addr, indices=None):
        x = self.icepap_system.get_pos(indices, "MEASURE")
        return x

    def _getter_fpos_measure(self, addr, indices=None):
        x = self.icepap_system.get_fpos(indices, "MEASURE")
        return x

    def _getter_enc_encin(self, addr, indices=None):
        x = self.icepap_system.get_enc(indices, "ENCIN")
        return x

    def _getter_enc_absenc(self, addr, indices=None):
        x = self.icepap_system.get_enc(indices, "ABSENC")
        return x

    def _getter_enc_tgtenc(self, addr, indices=None):
        x = self.icepap_system.get_enc(indices, "TGTENC")
        return x

    def _getter_enc_inpos(self, addr, indices=None):
        x = self.icepap_system.get_enc(indices, "INPOS")
        return x

    def _getter_enc_measure(self, addr, indices=None):
        x = self.icepap_system.get_enc(indices, "MEASURE")
        return x

    # these ones have to be well implemented, but unknown if really useful
    def _getter_fstat_ready(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("FSTATUS", indices))
        )
        return [State(value).is_ready() for value in statuses]

    def _getter_stat_ready(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("STATUS", indices))
        )
        return [State(value).is_ready() for value in statuses]

    def _getter_fstat_moving(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("FSTATUS", indices))
        )
        return [State(value).is_moving() for value in statuses]

    def _getter_stat_moving(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("STATUS", indices))
        )
        return [State(value).is_moving() for value in statuses]

    def _getter_fstat_settling(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("FSTATUS", indices))
        )
        return [State(value).is_settling() for value in statuses]

    def _getter_stat_settling(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("STATUS", indices))
        )
        return [State(value).is_settling() for value in statuses]

    def _getter_fstat_outofwin(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("FSTATUS", indices))
        )
        return [State(value).is_outofwin() for value in statuses]

    def _getter_stat_outofwin(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("STATUS", indices))
        )
        return [State(value).is_outofwin() for value in statuses]

    def _getter_fstat_limit_positive(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("FSTATUS", indices))
        )
        return [State(value).is_limit_positive() for value in statuses]

    def _getter_stat_limit_positive(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("STATUS", indices))
        )
        return [State(value).is_limit_positive() for value in statuses]

    def _getter_fstat_limit_negative(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("FSTATUS", indices))
        )
        return [State(value).is_limit_negative() for value in statuses]

    def _getter_stat_limit_negative(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("STATUS", indices))
        )
        return [State(value).is_limit_negative() for value in statuses]

    def _getter_fstat_inhome(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("FSTATUS", indices))
        )
        return [State(value).is_inhome() for value in statuses]

    def _getter_stat_inhome(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("STATUS", indices))
        )
        return [State(value).is_inhome() for value in statuses]

    def _getter_fstat_stopcode(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("FSTATUS", indices))
        )
        return [State(value).get_stop_code() for value in statuses]

    def _getter_stat_stopcode(self, addr, indices=None):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd("STATUS", indices))
        )
        return [State(value).get_stop_code() for value in statuses]

    def get_status_flags(self, status_kind, indices, flags):
        statuses = _parse_status_values(
            self.icepap_system.send_cmd(_status_cmd(status_kind, indices))
        )
        return _expand_status_flags(statuses, flags)


def _status_cmd(name, indices):
    if not indices:
        return f"?{name}"
    return "?{} {}".format(name, " ".join(str(i) for i in indices))


def _parse_status_values(response):
    if response is None:
        return []
    if isinstance(response, (list, tuple)):
        return [int(val, 16) if isinstance(val, str) else int(val) for val in response]
    if isinstance(response, str):
        tokens = [t for t in response.replace(",", " ").split() if t]
        return [int(val, 16) if val.lower().startswith("0x") else int(val) for val in tokens]
    return [int(response)]


def _expand_status_flags(statuses, flags):
    flag_map = {
        "r": lambda st: st.is_ready(),
        "m": lambda st: st.is_moving(),
        "s": lambda st: st.is_settling(),
        "c": lambda st: st.get_stop_code(),
        "o": lambda st: st.is_outofwin(),
        "n": lambda st: st.is_limit_negative(),
        "p": lambda st: st.is_limit_positive(),
        "h": lambda st: st.is_inhome(),
    }
    values = []
    for status in statuses:
        st = State(status)
        for flag in flags:
            fn = flag_map.get(flag)
            if fn is None:
                raise RuntimeError("Unknown status flag: {}".format(flag))
            values.append(fn(st))
    return values


class HeadlessBatchRunner:
    """Execute headless batch acquisitions without Collector."""

    def __init__(
        self,
        settings,
        host,
        port,
        timeout,
        signals,
        output_file,
        corr_factors=None,
        icepap_controller=None,
    ):
        self.settings = settings
        self.output_file = output_file
        self.curve_items = []
        self.curves_by_key = {}

        if icepap_controller is None:
            self._controller = IcePAPController(host, port, timeout, auto_axes=True)
        else:
            self._controller = icepap_controller
        self._getters = HeadlessBatchGetters(self._controller)
        self._correction_factors = corr_factors
        self._groups = []
        self._build_groups(signals)

    def _build_groups(self, signals):
        if not signals:
            raise RuntimeError("No signals defined for headless batch acquisition")

        curve_id = 0
        for driver, signal, axis in signals:
            if "_" not in signal:
                raise RuntimeError(
                    "Headless batch mode requires composite signal names like "
                    "'PosMeasure_1_2_3'. Got: {}".format(signal)
                )
            base, suffix = signal.split("_", 1)
            indices = [int(part) for part in suffix.split("_") if part]
            if not indices:
                raise RuntimeError(
                    "Headless batch mode requires at least one index in signal name. "
                    "Got: {}".format(signal)
                )
            flags = None
            status_kind = None
            if ">" in base:
                base_name, flags = base.split(">", 1)
                base = base_name
                if base not in ("FStat", "Stat"):
                    raise RuntimeError("Unknown batch status base: {}".format(base))
                if not flags:
                    raise RuntimeError(
                        "Headless batch status signals require flags after '>'. "
                        "Got: {}".format(signal)
                    )
                flags = list(flags)
                status_kind = "FSTATUS" if base == "FStat" else "STATUS"
            getter = self._getters.sig_getters.get(base)
            if getter is None and status_kind is None:
                raise RuntimeError("Unknown batch signal base: {}".format(base))

            group_curves = []
            if flags is not None:
                for idx in indices:
                    for flag in flags:
                        curve_id += 1
                        sig_name = "{}_{}{}".format(base, idx, flag)
                        curve = CurveItem(
                            curve_id,
                            driver,
                            sig_name,
                            axis,
                            QtGui.QColor(0, 0, 0),
                            QtCore.Qt.SolidLine,
                            "",
                        )
                        if self._correction_factors:
                            curve.corr_factors = list(self._correction_factors)
                        self.curve_items.append(curve)
                        self.curves_by_key[(driver, sig_name, axis)] = curve
                        group_curves.append(curve)
            else:
                for idx in indices:
                    curve_id += 1
                    sig_name = "{}_{}".format(base, idx)
                    curve = CurveItem(
                        curve_id,
                        driver,
                        sig_name,
                        axis,
                        QtGui.QColor(0, 0, 0),
                        QtCore.Qt.SolidLine,
                        "",
                    )
                    if self._correction_factors:
                        curve.corr_factors = list(self._correction_factors)
                    self.curve_items.append(curve)
                    self.curves_by_key[(driver, sig_name, axis)] = curve
                    group_curves.append(curve)

            self._groups.append(
                {
                    "driver": driver,
                    "base": base,
                    "indices": indices,
                    "getter": getter,
                    "flags": flags,
                    "status_kind": status_kind,
                    "curves": group_curves,
                }
            )

    def _collect_once(self):
        now = time.time()
        for group in self._groups:
            if group.get("flags") is not None:
                values = self._getters.get_status_flags(
                    group["status_kind"], group["indices"], group["flags"]
                )
            else:
                values = group["getter"](group["driver"], group["indices"])
            if not isinstance(values, (list, tuple)):
                values = [values]
            if len(values) != len(group["curves"]):
                raise RuntimeError(
                    "Batch getter '{}' returned {} values for {} indices".format(
                        group["base"], len(values), len(group["curves"])
                    )
                )
            for curve, value in zip(group["curves"], values):
                curve.collect([(now, value)])

    def run(self, acquisition_time):
        interval = max(self.settings.sample_rate / 1000.0, 0.001)
        start = time.time()
        stop = {"flag": False}
        prev_handler = signal.getsignal(signal.SIGINT)

        def _request_stop(_signum, _frame):
            stop["flag"] = True

        signal.signal(signal.SIGINT, _request_stop)
        print("Headless batch acquisition running. Press Ctrl+C to stop gracefully.")
        try:
            while time.time() - start < acquisition_time and not stop["flag"]:
                self._collect_once()
                if stop["flag"]:
                    break
                time.sleep(interval)
        finally:
            signal.signal(signal.SIGINT, prev_handler)
            write_curves_to_csv(self.curve_items, self.output_file)
            print(f"Written to {self.output_file}")
            _report_csv_write(self.output_file)


def _report_csv_write(filename):
    if not filename or not os.path.isfile(filename):
        print("CSV verification failed: file not found")
        return
    header = ""
    line_count = 0
    first_line = None
    last_line = None
    try:
        with open(filename, "r") as csv_file:
            header = csv_file.readline().rstrip("\n")
            for line in csv_file:
                line_count += 1
                if first_line is None:
                    first_line = line
                last_line = line
    except Exception as e:
        print("CSV verification failed: {}".format(e))
        return
    print("CSV lines: {}".format(line_count))
    print("CSV header: {}".format(header))
    if first_line is not None and last_line is not None:
        try:
            first_parts = first_line.split(",", 2)
            last_parts = last_line.split(",", 2)
            if len(first_parts) < 2 or len(last_parts) < 2:
                raise ValueError("Missing timestamp column")
            acq_time = float(last_parts[1]) - float(first_parts[1])
            print("Acq time:{}".format(acq_time))
        except Exception as e:
            print("Acq time: unavailable ({})".format(e))

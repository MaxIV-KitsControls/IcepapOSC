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

from PyQt5 import QtCore
from collections import OrderedDict
from icepap import IcePAPController
from .channel import Channel
import time

SIGNAL_GETTER_MAP = [
    ("PosAxis", "_getter_pos_axis"),
    ("PosTgtenc", "_getter_pos_tgtenc"),
    ("PosShftenc", "_getter_pos_shftenc"),
    ("PosEncin", "_getter_pos_encin"),
    ("PosAbsenc", "_getter_pos_absenc"),
    ("PosInpos", "_getter_pos_inpos"),
    ("PosMotor", "_getter_pos_motor"),
    ("PosCtrlenc", "_getter_pos_ctrlenc"),
    ("PosMeasure", "_getter_pos_measure"),
    ("DifAxMeasure", "_getter_dif_ax_measure"),
    ("DifAxMotor", "_getter_dif_ax_motor"),
    ("DifAxTgtenc", "_getter_dif_ax_tgtenc"),
    ("DifAxShftenc", "_getter_dif_ax_shftenc"),
    ("DifAxCtrlenc", "_getter_dif_ax_ctrlenc"),
    ("DifAxEncin", "_getter_dif_ax_encin"),
    ("DifAxAbsenc", "_getter_dif_ax_absenc"),
    ("DifAxInpos", "_getter_dif_ax_inpos"),
    ("EncEncin", "_getter_enc_encin"),
    ("EncAbsenc", "_getter_enc_absenc"),
    ("EncTgtenc", "_getter_enc_tgtenc"),
    ("EncInpos", "_getter_enc_inpos"),
    ("EncMeasure", "_getter_enc_measure"),
    ("StatReady", "_getter_stat_ready"),
    ("StatMoving", "_getter_stat_moving"),
    ("StatSettling", "_getter_stat_settling"),
    ("StatOutofwin", "_getter_stat_outofwin"),
    ("StatStopcode", "_getter_stat_stopcode"),
    ("StatWarning", "_getter_stat_warning"),
    ("StatLim+", "_getter_stat_limit_positive"),
    ("StatLim-", "_getter_stat_limit_negative"),
    ("StatHome", "_getter_stat_home"),
    ("MeasI", "_getter_meas_i"),
    ("MeasIa", "_getter_meas_ia"),
    ("MeasIb", "_getter_meas_ib"),
    ("MeasVm", "_getter_meas_vm"),
    ("VelCurrent", "_getter_vel_current"),
    ("VelMotor", "_getter_vel_motor"),
    ("SyncAux", "_getter_syncaux"),
    ("SyncPos", "_getter_syncpos"),
    ("EinAux", "_getter_einaux"),
    ("EinPos", "_getter_einpos"),
    ("InpAux", "_getter_inpaux"),
    ("InpPos", "_getter_inppos"),
]
AVAILABLE_SIGNALS = [name for name, _ in SIGNAL_GETTER_MAP]


class IcePAPDescriptor:
    def __init__(self, icepap_controller, hostname):
        "This class is used to wrap hardware functionality"
        "At the moment hostname is not used. Leave it here though"

        self.sig_getters = OrderedDict(
            (name, getattr(self, method_name))
            for name, method_name in SIGNAL_GETTER_MAP
        )
        self.icepap_system = icepap_controller
        self.host = self.icepap_system.host
        self.port = self.icepap_system.port
        self.poscorr_a = 1  # These can be cleaned up. Done elsewhere
        self.poscorr_b = 0
        self.enccorr_a = 1
        self.enccorr_b = 0

        self.sig_list = list(self.sig_getters.keys())

    def get_available_drivers(self):
        """
        Retrieves the available drivers.

        Return: List of available drivers.
        """
        return self.icepap_system.axes

    def get_available_signals(self):
        """
        Retrieves the available signals.

        Return: List of available signals.
        """
        return self.sig_list

    def get_signal_index(self, signal_name):
        """
        Retrieves the fixed index of a signal from its name.

        Return: Signal index.
        """
        return self.sig_list.index(signal_name)

    def get_getters(self):
        return list(self.sig_getters.keys())

    def get_sig_getters(self):
        return self.sig_getters

    def subscription_checks(self, icepap_addr, sn, channel):
        cond_1 = sn.endswith("Tgtenc")
        cond_2 = sn.endswith("Shftenc")
        cond_3 = sn == "DifAxMeasure"
        if cond_1 or cond_2 or cond_3:
            try:
                cfg = self.icepap_system[icepap_addr].get_cfg()
            except RuntimeError as e:
                msg = (
                    "Failed to retrieve configuration parameters "
                    "for driver {}\n{}.".format(icepap_addr, e)
                )
                raise Exception(msg)
            if (cond_1 and cfg["TGTENC"].upper() == "NONE") or (
                cond_2 and cfg["SHFTENC"].upper() == "NONE"
            ):
                msg = "Signal {} is not mapped/valid.".format(sn)
                raise Exception(msg)
            if cond_3:
                channel.set_measure_resolution(cfg)

    def _getter_pos_axis(self, addr):
        x = self.icepap_system[addr].pos
        x = x * self.poscorr_a + self.poscorr_b
        return x

    def _getter_pos_tgtenc(self, addr):
        x = self.icepap_system[addr].pos_tgtenc
        x = x * self.poscorr_a + self.poscorr_b
        return x

    def _getter_pos_shftenc(self, addr):
        x = self.icepap_system[addr].pos_shftenc
        x = x * self.poscorr_a + self.poscorr_b
        return x

    def _getter_pos_encin(self, addr):
        x = self.icepap_system[addr].pos_encin
        x = x * self.poscorr_a + self.poscorr_b
        return x

    def _getter_pos_absenc(self, addr):
        x = self.icepap_system[addr].pos_absenc
        x = x * self.poscorr_a + self.poscorr_b
        return x

    def _getter_pos_inpos(self, addr):
        x = self.icepap_system[addr].pos_inpos
        x = x * self.poscorr_a + self.poscorr_b
        return x

    def _getter_pos_motor(self, addr):
        x = self.icepap_system[addr].pos_motor
        x = x * self.poscorr_a + self.poscorr_b
        return x

    def _getter_pos_ctrlenc(self, addr):
        x = self.icepap_system[addr].pos_ctrlenc
        x = x * self.poscorr_a + self.poscorr_b
        return x

    def _getter_pos_measure(self, addr):
        x = self.icepap_system.get_pos(self.icepap_system[addr].addr, "MEASURE")[0]
        x = x * self.poscorr_a + self.poscorr_b
        return x

    def _getter_dif_ax_measure(self, addr):
        pos_measure = self._getter_pos_measure(addr)
        x = self._getter_pos_axis(addr) - pos_measure
        x = x * self.poscorr_a
        return x

    def _getter_dif_ax_motor(self, addr):
        x = self._getter_pos_axis(addr) - self._getter_pos_motor(addr)
        x = x * self.poscorr_a
        return x

    def _getter_dif_ax_tgtenc(self, addr):
        x = self._getter_pos_axis(addr) - self._getter_pos_tgtenc(addr)
        x = x * self.poscorr_a
        return x

    def _getter_dif_ax_shftenc(self, addr):
        x = self._getter_pos_axis(addr) - self._getter_pos_shftenc(addr)
        x = x * self.poscorr_a
        return x

    def _getter_dif_ax_ctrlenc(self, addr):
        x = self._getter_pos_axis(addr) - self._getter_pos_ctrlenc(addr)
        x = x * self.poscorr_a
        return x

    def _getter_dif_ax_encin(self, addr):
        x = self._getter_pos_axis(addr) - self._getter_pos_encin(addr)
        x = x * self.poscorr_a
        return x

    def _getter_dif_ax_inpos(self, addr):
        x = self._getter_pos_axis(addr) - self._getter_pos_inpos(addr)
        x = x * self.poscorr_a
        return x

    def _getter_dif_ax_absenc(self, addr):
        x = self._getter_pos_axis(addr) - self._getter_pos_absenc(addr)
        x = x * self.poscorr_a
        return x

    def _getter_enc_encin(self, addr):
        x = self.icepap_system[addr].enc_encin
        x = x * self.enccorr_a + self.enccorr_b
        return x

    def _getter_enc_absenc(self, addr):
        x = self.icepap_system[addr].enc_absenc
        x = x * self.enccorr_a + self.enccorr_b
        return x

    def _getter_enc_tgtenc(self, addr):
        x = self.icepap_system[addr].enc_tgtenc
        x = x * self.enccorr_a + self.enccorr_b
        return x

    def _getter_enc_inpos(self, addr):
        x = self.icepap_system[addr].enc_inpos
        x = x * self.enccorr_a + self.enccorr_b
        return x

    def _getter_enc_measure(self, addr):
        x = self.icepap_system.get_fpos(self.icepap_system[addr].addr, "MEASURE")[0]
        x = x * self.enccorr_a + self.enccorr_b
        return x

    def _getter_stat_ready(self, addr):
        return 1 if self.icepap_system[addr].state_ready else 0

    def _getter_stat_moving(self, addr):
        return 1 if self.icepap_system[addr].state_moving else 0

    def _getter_stat_settling(self, addr):
        return 1 if self.icepap_system[addr].state_settling else 0

    def _getter_stat_outofwin(self, addr):
        return 1 if self.icepap_system[addr].state_outofwin else 0

    def _getter_stat_stopcode(self, addr):
        return self.icepap_system[addr].state_stop_code

    def _getter_stat_warning(self, addr):
        return 1 if self.icepap_system[addr].state_warning else 0

    def _getter_stat_limit_positive(self, addr):
        return 1 if self.icepap_system[addr].state_limit_positive else 0

    def _getter_stat_limit_negative(self, addr):
        return 1 if self.icepap_system[addr].state_limit_negative else 0

    def _getter_stat_home(self, addr):
        return 1 if self.icepap_system[addr].state_inhome else 0

    def _getter_meas_i(self, addr):
        return self.icepap_system[addr].meas_i

    def _getter_meas_ia(self, addr):
        return self.icepap_system[addr].meas_ia

    def _getter_meas_ib(self, addr):
        return self.icepap_system[addr].meas_ib

    def _getter_meas_vm(self, addr):
        return self.icepap_system[addr].meas_vm

    def _getter_vel_current(self, addr):
        x = self.icepap_system[addr].velocity_current
        x = x * self.poscorr_a
        return x

    def _getter_vel_motor(self, addr):
        x = self.icepap_system[addr].get_velocity(vtype="MOTOR")
        x = x * self.poscorr_a
        return x

    def _getter_syncaux(self, addr):
        return float(self.icepap_system[addr].send_cmd("?isg ?syncval")[-1])

    def _getter_syncpos(self, addr):
        return float(self.icepap_system[addr].send_cmd("?isg ?syncval")[-2])

    def _getter_einaux(self, addr):
        return float(self.icepap_system[addr].send_cmd("?isg ?encval")[-1])

    def _getter_einpos(self, addr):
        return float(self.icepap_system[addr].send_cmd("?isg ?encval")[-2])

    def _getter_inpaux(self, addr):
        return float(self.icepap_system[addr].send_cmd("?isg ?inpval")[-1])

    def _getter_inppos(self, addr):
        return float(self.icepap_system[addr].send_cmd("?isg ?inpval")[-2])


class Collector:
    """Feeds a subscriber with collected IcePAP signal data."""

    def __init__(
        self, settings, callback, icepap_controller=None, use_qtimer=True, hostname=""
    ):
        """
        Initializes an instance of class Collector.

        settings - Contain dump and sample rates. Used for automated tests among other purposes

        callback - A callback function used for sending collected signal
                   data back to the caller.
                   cb_func(subscription_id, value_list)
                       subscription_id - The subscription id retained when
                                         subscribing for a signal.
                       value_list      - A list of tuples
                                         (time_stamp, signal_value)
        icepap_controller - This class is different for normal purposes or for automated tests

        use_qtimer - Used by automated tests

        hostname - Not used, but leave it as is. Don't remove
        """
        self.settings = settings
        self.cb = callback
        self.icepap_system = None
        self.channels_subscribed = {}
        self.channels = {}
        self.channel_id = 0
        self.current_channel = 0

        try:
            self.icepap_system = IcePAPDescriptor(icepap_controller, hostname)
        except Exception as e:
            msg = (
                "Failed to instantiate master controller.\nHost: "
                "{}\nPort: {}\n{}".format(
                    icepap_controller.host, icepap_controller.port, e
                )
            )
            raise Exception(msg)

        if not self.icepap_system:
            msg = "IcePAP system {} has no active drivers! " "Aborting.".format(host)
            raise Exception(msg)

        self.sig_list = self.icepap_system.get_getters()
        self.sig_getters = self.icepap_system.get_sig_getters()

        self._use_qtimer = use_qtimer
        self.ticker = None
        if self._use_qtimer:
            self.ticker = QtCore.QTimer()
            self.ticker.timeout.connect(self._tick)
            self.ticker.start(self.settings.sample_rate)

    @staticmethod
    def get_current_time():
        """
        Retrieves the current time.

        Return: Current time as seconds (with fractions) from 1970.
        """
        return time.time()

    def subscribe(self, icepap_addr, signal_name):
        """
        Creates a new subscription for signal values.

        icepap_addr - IcePAP driver number.
        signal_name - Signal name.
        Return - A positive integer id used when unsubscribing.
        """
        for ch in list(self.channels_subscribed.values()):
            if ch.equals(icepap_addr, signal_name):
                msg = "Channel already exists.\nAddr: " "{}\nSignal: {}".format(
                    icepap_addr, signal_name
                )
                raise Exception(msg)
        channel = Channel(icepap_addr, signal_name)
        sn = str(signal_name)

        self.icepap_system.subscription_checks(icepap_addr, signal_name, channel)
        """
        ###
        cond_1 = sn.endswith('Tgtenc')
        cond_2 = sn.endswith('Shftenc')
        cond_3 = sn == 'DifAxMeasure'
        if cond_1 or cond_2 or cond_3:
            try:
                cfg = self.icepap_system[icepap_addr].get_cfg()
            except RuntimeError as e:
                msg = 'Failed to retrieve configuration parameters ' \
                      'for driver {}\n{}.'.format(icepap_addr, e)
                raise Exception(msg)
            if (cond_1 and cfg['TGTENC'].upper() == 'NONE') or \
                    (cond_2 and cfg['SHFTENC'].upper() == 'NONE'):
                msg = 'Signal {} is not mapped/valid.'.format(sn)
                raise Exception(msg)
            if cond_3:
                channel.set_measure_resolution(cfg)
        ###
        """
        self.channel_id += 1
        self.channels_subscribed[self.channel_id] = channel
        return self.channel_id

    def get_available_drivers(self):
        return self.icepap_system.get_available_drivers()

    def get_available_signals(self):
        return self.icepap_system.get_available_signals()

    def start(self, subscription_id):
        """
        Starts collecting data for a subscription.

        subscription_id - The given subscription id.
        """
        if subscription_id in list(
            self.channels_subscribed.keys()
        ) and subscription_id not in list(self.channels.keys()):
            self.channels[subscription_id] = self.channels_subscribed[subscription_id]

    def unsubscribe(self, subscription_id):
        """
        Cancels a subscription.

        subscription_id - The given subscription id.
        """
        if subscription_id in list(self.channels_subscribed.keys()):
            del self.channels[subscription_id]
            del self.channels_subscribed[subscription_id]

    def _tick(self):
        for subscription_id, channel in self.channels.items():
            self.current_channel = subscription_id
            try:
                addr = channel.icepap_address
                val = self.sig_getters[channel.sig_name](addr)
            except RuntimeError as e:
                msg = "Failed to collect data for signal " "{}\n{}".format(
                    channel.sig_name, e
                )
                print(msg)
                continue
            tv = (time.time(), val)
            channel.collected_samples.append(tv)
            if len(channel.collected_samples) >= self.settings.dump_rate:
                self.cb(subscription_id, channel.collected_samples)
                channel.collected_samples = []
        if self._use_qtimer and self.ticker is not None:
            self.ticker.start(self.settings.sample_rate)

    def tick_once(self):
        if not self._use_qtimer:
            self._tick()

    def stop(self):
        if self.ticker is not None:
            self.ticker.stop()

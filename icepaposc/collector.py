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

# from .tests.FIcePAPController import FIcePAPController as IcePAPController
from .channel import Channel
import time

# from time import time
from ctypes import c_int32, c_int16
import struct

#  General MODBUS includes
from modbus_tk.exceptions import ModbusError
import modbus_tk.defines as cst

# TCP MODBUS includes
from modbus_tk import modbus_tcp
from .dtax import dtax
from types import MethodType


class IcePAPDescriptor:
    def __init__(self, host, port, timeout):
        self.sig_getters = OrderedDict(
            [
                ("PosAxis", self._getter_pos_axis),
                ("PosTgtenc", self._getter_pos_tgtenc),
                ("PosShftenc", self._getter_pos_shftenc),
                ("PosEncin", self._getter_pos_encin),
                ("PosAbsenc", self._getter_pos_absenc),
                ("PosInpos", self._getter_pos_inpos),
                ("PosMotor", self._getter_pos_motor),
                ("PosCtrlenc", self._getter_pos_ctrlenc),
                ("PosMeasure", self._getter_pos_measure),
                ("DifAxMeasure", self._getter_dif_ax_measure),
                ("DifAxMotor", self._getter_dif_ax_motor),
                ("DifAxTgtenc", self._getter_dif_ax_tgtenc),
                ("DifAxShftenc", self._getter_dif_ax_shftenc),
                ("DifAxCtrlenc", self._getter_dif_ax_ctrlenc),
                ("EncEncin", self._getter_enc_encin),
                ("EncAbsenc", self._getter_enc_absenc),
                ("EncTgtenc", self._getter_enc_tgtenc),
                ("EncInpos", self._getter_enc_inpos),
                ("EncMeasure", self._getter_enc_measure),
                ("StatReady", self._getter_stat_ready),
                ("StatMoving", self._getter_stat_moving),
                ("StatSettling", self._getter_stat_settling),
                ("StatOutofwin", self._getter_stat_outofwin),
                ("StatStopcode", self._getter_stat_stopcode),
                ("StatWarning", self._getter_stat_warning),
                ("StatLim+", self._getter_stat_limit_positive),
                ("StatLim-", self._getter_stat_limit_negative),
                ("StatHome", self._getter_stat_home),
                ("MeasI", self._getter_meas_i),
                ("MeasIa", self._getter_meas_ia),
                ("MeasIb", self._getter_meas_ib),
                ("MeasVm", self._getter_meas_vm),
                ("VelCurrent", self._getter_vel_current),
                ("VelMotor", self._getter_vel_motor),
            ]
        )
        self.host = host
        self.port = port
        self.poscorr_a = 1  # These can be cleaned up. Done elsewhere
        self.poscorr_b = 0
        self.enccorr_a = 1
        self.enccorr_b = 0

        try:
            self.icepap_system = IcePAPController(
                self.host, self.port, timeout, auto_axes=True
            )
        except Exception as e:
            msg = (
                "Failed to instantiate master controller.\nHost: "
                "{}\nPort: {}\n{}".format(self.host, self.port, e)
            )
            raise Exception(msg)

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


class IceDtaxDescriptor(IcePAPDescriptor):
    # Address = device_property(dtype=str, default_value="192.168.2.40")
    # Address = device_property(dtype=str, default_value="10.0.108.171")
    # Address = device_property(dtype=str, default_value="172.16.142.101")  # hippie
    # Address = device_property(dtype=str, default_value="172.16.190.98")  #species
    # Address = device_property(dtype=str, default_value="172.16.166.80")  # finest
    # Address = device_property(dtype=str, default_value="172.16.182.96")  # flexpes
    NotFlexpes = True
    PortModbus = 502
    DeviceID = 1
    TimeOut = 5.0
    d = dtax()
    raw = False

    def __init__(self, host, port, timeout):
        self.host1 = host.split(",")[0]
        self.host2 = host.split(",")[1]
        self.port = port
        # since you need to connect to an icepap,
        # use that in the machine where the moxa address is the same for all epus
        if self.host1.lower() in [
            "10.113.25",
            "r1-d110710-cab40-ctl-ipap-03.maxiv.lu.se",
            "r1-d110710-cab40-ctl-ipap-03",
        ] or self.host2.lower() in [
            "172.16.166.80",
        ]:
            self.NotFlexpes = False
        else:
            self.NotFlexpes = True
        # Get the icepap
        super().__init__(self.host1, self.port, timeout)
        self.master = modbus_tcp.TcpMaster(host=self.host2, port=self.PortModbus)
        self.master.set_verbose(False)
        self.master.set_timeout(self.TimeOut)
        for n, p in self.d.dtax_params.items():
            if "getter" in p:
                pname = p["getter"].split("_")[1]
                fgetf = p["getter"]
                param = n
                methode_code = f'def {fgetf}(self, addr): return self.generic_read(addr, "{param}")'
                exec(methode_code)
                bound_method = MethodType(locals()[fgetf], self)
                setattr(self, fgetf, bound_method)
                self.sig_getters.update([(pname, bound_method)])
                print(fgetf)
        self.sig_getters.update(
            [
                ("voltagermotor", self.get_voltagermotor),
                ("voltagelmotor", self.get_voltagelmotor),
                ("voltagekmotor", self.get_voltagekmotor),
            ]
        )
        self.sig_list = list(self.sig_getters.keys())

    def get_voltagermotor(self, addr):
        par = "4.01"
        self.digitax_get_parameter(addr, self.d.dtax_params[par])
        result = self.digitaxDecodeFrame(
            self.d.dtax_params[par], scale=self.d.dtax_params[par]["scale"]
        )
        if self.NotFlexpes and addr in [1, 2, 3, 4]:
            resistancehalfphase2phase = 48.2  # 5.17
        else:
            resistancehalfphase2phase = 0.75
        resistance = 2 * resistancehalfphase2phase
        if result is None:
            return 0.0
        return resistance * abs(result)

    def get_voltagelmotor(self, addr):
        par = "4.01"
        self.digitax_get_parameter(addr, self.d.dtax_params[par])
        curr = self.digitaxDecodeFrame(
            self.d.dtax_params[par],
            scale=self.d.dtax_params[par]["scale"],
            force_not_raw=True,
        )
        par = "3.02"
        self.digitax_get_parameter(addr, self.d.dtax_params[par])
        rpms = self.digitaxDecodeFrame(
            self.d.dtax_params[par],
            scale=self.d.dtax_params[par]["scale"],
            force_not_raw=True,
        )
        if self.NotFlexpes and addr in [1, 2, 3, 4]:
            inductance = 99.2  # mh #5.24
        else:
            inductance = 19.700
        inductanceph2ph = 2 * inductance
        polespairs = 3
        result = (
            2
            * 3.14159
            * inductanceph2ph
            * 1e-3
            * polespairs
            * 60
            * rpms
            * (1 / self.d.speedFactor)
            * curr
        )
        if result is None:
            return 0.0
        return abs(result)

    def get_voltagekmotor(self, addr):
        par = "3.02"
        self.digitax_get_parameter(addr, self.d.dtax_params[par])
        rpms = self.digitaxDecodeFrame(
            self.d.dtax_params[par],
            scale=self.d.dtax_params[par]["scale"],
            force_not_raw=True,
        )
        if self.NotFlexpes and addr in [1, 2, 3, 4]:
            ke = 147  # 5.17 v/krpm
        else:
            ke = 98
        if rpms is None:
            return 0.0
        return 1e-3 * ke * abs(rpms) * (1 / self.d.speedFactor)

    def generic_read(self, addr, attr):
        par = attr
        if par.endswith("p") or par.endswith("g"):
            if addr in [1, 2, 3, 4]:
                par = par[:-1] + "g"
        attr_name = self.d.dtax_params[par]["getter"].split("_")[1]
        position_factor = 1.0
        if attr_name.startswith("position"):
            if not self.NotFlexpes:
                position_factor = self.d.positionFactorFlexpes
            elif addr in [1, 2, 3, 4]:
                position_factor = self.d.positionFactorMMGap
            else:
                position_factor = self.d.positionFactorMMPhase
        if attr_name.startswith("position") and "Rev" in attr_name:
            if not self.NotFlexpes:
                position_factor = self.d.positionRevFactorFlexpes
            elif addr in [1, 2, 3, 4]:
                position_factor = self.d.positionRevFactorMMGap
            else:
                position_factor = self.d.positionRevFactorMMPhase
        self.digitax_get_parameter(addr, self.d.dtax_params[par])
        result = self.digitaxDecodeFrame(
            self.d.dtax_params[par],
            scale=self.d.dtax_params[par]["scale"],
            extra_scale_factor=position_factor,
        )
        if result is None:
            return 0.0
        return result

    def get_registerRange(self, addr, startRegistry, numberOfIndexes):
        try:
            self.registerTab = self.master.execute(
                addr,
                cst.READ_HOLDING_REGISTERS,
                startRegistry,
                numberOfIndexes,
            )

        except ModbusError as exc:
            Except.re_throw_exception(
                exc,
                "modbusPLC.get_registerRange",
                "modbusPLC.get_registerRange method failed.",
            )
        except Exception as exc:
            if exc.errno == 8:
                Except.re_throw_exception(
                    exc,
                    "modbusPLC.get_registerRange",
                    "modbusPLC.get_registerRange method failed.",
                )
            else:
                print("Nocommunication")

    def get_digitax_address_from_menu_register(
        self, menu, register, register_data_type
    ):
        REGISTER_TYPE_INT16_ADDR = 0
        REGISTER_TYPE_INT32_ADDR = pow(14, 2)
        REGISTER_TYPE_FLOAT_ADDR = pow(15, 2)
        addr = None
        if register_data_type == "int16":
            addr = REGISTER_TYPE_INT16_ADDR + menu * 100 + register - 1
        elif register_data_type == "int32":
            addr = REGISTER_TYPE_INT32_ADDR + menu * 100 + register - 1
        elif register_data_type == "float":
            addr = REGISTER_TYPE_FLOAT_ADDR + menu * 100 + register - 1
        else:
            raise (NotImplementedError)
        return addr

    def get_digitax_number_of_modbus_registers(self, register_data_type):
        nbytes = None
        # print("gdnob:", register_data_type)
        if register_data_type == "int16":
            nbytes = 1
        elif register_data_type == "int32":
            nbytes = 2
        elif register_data_type == "float":
            nbytes = 2
        else:
            raise (NotImplementedError)
        return nbytes

    def digitax_get_parameter(self, addr, par):
        self.get_registerRange(
            addr,
            self.get_digitax_address_from_menu_register(
                par["menu"], par["register"], par["dtype"]
            ),  # start reg
            self.get_digitax_number_of_modbus_registers(
                par["dtype"]
            ),  # numberOfIndexes
        )

    def digitaxDecodeFrame(
        self, par, scale=True, force_not_raw=False, extra_scale_factor=1.0
    ):
        try:
            if not self.registerTab:
                return None
            if par["dtype"] == "int16":
                val1 = self.registerTab[0]
                if par["signed"]:
                    val1 = c_int16(val1).value
            elif par["dtype"] == "int32":
                val1 = (self.registerTab[0] << 16) | self.registerTab[1]
                if par["signed"]:
                    val1 = c_int32(val1).value
            elif par["dtype"] == "float":
                val1 = (self.registerTab[0] << 16) | self.registerTab[1]
                val1 = struct.unpack(">f", struct.pack(">I", val1))[0]
            if False:
                print(
                    "dp:",
                    par["menu"],
                    par["register"],
                    val1,
                    val1 * par["factor"],
                    par["default"],
                )
            if scale and (not self.raw or force_not_raw):
                return val1 * par["factor"] * extra_scale_factor
            else:
                return 1.0 * val1
        except Exception:
            print("Decode Frame Error")
            return None


class Collector:
    """Feeds a subscriber with collected IcePAP signal data."""

    def __init__(self, host, port, timeout, settings, callback):
        """
        Initializes an instance of class Collector.

        host     - The IcePAP system host name.
        port     - The IcePAP system port number.
        timeout  - Socket timeout.
        callback - A callback function used for sending collected signal
                   data back to the caller.
                   cb_func(subscription_id, value_list)
                       subscription_id - The subscription id retained when
                                         subscribing for a signal.
                       value_list      - A list of tuples
                                         (time_stamp, signal_value)
        """
        self.settings = settings
        self.cb = callback
        self.icepap_system = None
        self.channels_subscribed = {}
        self.channels = {}
        self.channel_id = 0
        self.current_channel = 0
        # affine corrections for POS and ENC signals (to show them in different
        # units)
        self.host = host
        self.port = port

        """
        try:
            self.icepap_system = IcePAPController(self.host, self.port,
                                                  timeout, auto_axes=True)
        except Exception as e:
            msg = 'Failed to instantiate master controller.\nHost: ' \
                  '{}\nPort: {}\n{}'.format(self.host, self.port, e)
            raise Exception(msg)
        """
        try:
            self.icepap_system = IceDtaxDescriptor(self.host, self.port, timeout)
        except Exception as e:
            msg = (
                "Failed to instantiate master controller.\nHost: "
                "{}\nPort: {}\n{}".format(host, port, e)
            )
            raise Exception(msg)

        if not self.icepap_system:
            msg = "IcePAP system {} has no active drivers! " "Aborting.".format(host)
            raise Exception(msg)

        self.sig_list = self.icepap_system.get_getters()
        self.sig_getters = self.icepap_system.get_sig_getters()

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
        self.ticker.start(self.settings.sample_rate)

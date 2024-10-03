from numpy import random
import collections
import weakref

class FIcePAPController:
    """
    Fake IcePAP motor controller class.
    Implememnts only needed functionality for icepaposc
    """
    ALL_AXES_VALID = set([r * 10 + i for r in range(16) for i in range(1, 9)])

    def __init__(self, host, port=5000, timeout=3, auto_axes=False, **kwargs):
        print("FIC __init__")
        log_name = '{0}.IcePAPController'.format(__name__)
        # self.log = logging.getLogger(log_name)

        #self._comm = IcePAPCommunication(host, port, timeout)

        self._aliases = {}
        self._axes = {}
        self._host = host
        self._port = port

        if auto_axes:
            for axis in self.find_axes(only_alive=True):
                #self._axes[axis] = IcePAPAxis(self, axis)
                # print("FIC __init__", axis)
                self._axes[axis] = FIcePAPAxis(self, axis)
        # print("FIC __init__ ended")
        # print(self._axes)

    def __getitem__(self, item):
        if isinstance(item, str):
            item = self._get_axis_for_alias(item)
        elif isinstance(item, collections.abc.Sequence):
            return [self[i] for i in item]
        if item not in self._axes:
            if item not in self.ALL_AXES_VALID:
                raise ValueError('Bad axis value.')
            self._axes[item] = IcePAPAxis(self, item)
        return self._axes[item]

    def __iter__(self):
        return self._axes.__iter__()

    def __delitem__(self, key):
        self._axes.pop(key)
        aliases_to_remove = []
        for alias, axis in self._aliases.items():
            if key == axis:
                aliases_to_remove.append(alias)
        for alias in aliases_to_remove:
            self._aliases.pop(alias)

    def __repr__(self):
        return '{}({}:{})'.format(type(self).__name__,
                                  self.host, self.port)

    def __str__(self):
        msg = 'IcePAPController connected ' \
              'to {}:{}'.format(self.host, self.port)
        return msg

# -----------------------------------------------------------------------------
#                       Properties
# -----------------------------------------------------------------------------
    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port
    '''
    @host.setter
    def host(self, host):
        self.host = host

    @port.setter
    def port(self, port):
        self.port = port
    '''
    @property
    def axes(self):
        """
        Get the axes numbers.

        :return: [int]
        """
        axes = list(self._axes.keys())
        axes.sort()
        return axes 

    def find_axes(self, only_alive=False):
        # Take the list of racks present in the system
        # IcePAP user manual pag. 137
        # racks_present = int(self._comm.send_cmd('?sysstat')[0], 16)
        # rack_mask = 1
        axes = []
        # print('FIC find_axes')
        axes.append(1)
        axes.append(2)
        axes.append(3)
        axes.append(4)
        if only_alive:
            pass
        '''
        for i in range(16):
            if (racks_present & rack_mask << i) > 0:
                # Take the motors presents for a rack.
                cmd = '?sysstat {0}'.format(i)
                drivers_mask = self._comm.send_cmd(cmd)
                # TODO: Analyze if use the present or the alive mask
                if only_alive:
                    # Drivers alive
                    drvs = int(drivers_mask[1], 16)
                else:
                    # Drivers present
                    drvs = int(drivers_mask[0], 16)
                drv_mask = 1
                for j in range(8):
                    if (drvs & drv_mask << j) > 0:
                        axis_nr = i * 10 + j + 1
                        axes.append(axis_nr)
        '''
        return axes

class FIcePAPAxis:
    """
    The IcePAP axis class contains the common IcePAP ASCii API for any
    IcePAP axis. The methods here implemented correspond to those
    at the axis level.
    """
    def __init__(self, ctrl, axis_nr):
        ref = weakref.ref(ctrl)
        self._ctrl = ref()
        self._axis_nr = axis_nr
        # print("FIA __init__ end", axis_nr)

        # if self._axis_nr != self.addr:
        #     msg = 'Initialization error: axis_nr {0} != adr {1}'.format(
        #         self._axis_nr, self.addr)
        #     raise RuntimeError(msg)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self._axis_nr)

    def __str__(self):
        return 'IcePAPAxis {} on {}'.format(self._axis_nr, self._ctrl)
    
    @property
    def axis(self):
        """
        Get the axis number (IcePAP user manual pag. 49).
        Local internal address (no communication with the IcePAP)

        :return: int
        """
        return self._axis_nr

    @property
    def addr(self):
        """
        Get the axis number (IcePAP user manual pag. 49).

        :return: int
        """
        # return int(self.send_cmd('?ADDR')[0])
        return self._axis_nr 

    @property
    def active(self):
        """
        Get if the axis is active (IcePAP user manual pag. 47).

        :return: bool
        """
        # ans = self.send_cmd('?ACTIVE')[0].upper()
        # return ans == 'YES'
        return True

    @property
    def mode(self):
        """
        Return the current mode of the axis: CONFIG, OPER, PROG, TEST, FAIL
        (IcePAP user manual pag. 91).

        :return: str
        """
        # return self.send_cmd('?MODE')[0]
        return "OPER"

    @property
    def status(self):
        """
        Return axis status word 32-bits (IcePAP user manual pag. 128).

        :return: int
        """
        # return int(self.send_cmd('?STATUS')[0], 16)
        return 0

    def get_cfg(self, parameter=''):
        """
        Get the current configuration for one or all parameters (IcePAP user
        manual pag. 54).

        :param parameter: str (optional)
        :return: dict
        """
        cfg = collections.OrderedDict()
        cfg['ANSTEP'] = 400
        cfg['TGTENC'] = "AbsEnc"
        cfg['SHFTENC'] = "NONE"
        return cfg

    @property
    def pos(self):
        """
        Read the axis nominal position pointer (IcePAP user manual pag. 108).

        :return: int
        """
        # return self.get_pos('AXIS')
        return self._axis_nr + random.rand()

    @property
    def pos_measure(self):
        """
        Read the measure register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()
        # return self.get_pos('MEASURE')

    @property
    def pos_shftenc(self):
        """
        Read the shftenc register (IcePAP user manual pag. 108).

        :return: int
        """
        # return self.get_pos('SHFTENC')
        return self._axis_nr + random.rand()
    

    @property
    def pos_tgtenc(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()
        # return self.get_pos('TGTENC')

    @property
    def pos_encin(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()        

    @property
    def pos_absenc(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()        

    @property
    def pos_inpos(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()        

    @property
    def pos_motor(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()        

    @property
    def pos_ctrlenc(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()        

    @property
    def pos_motor(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()        

    @property
    def pos_measure(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()        

    @property
    def pos_measure(self):
        """
        Read the measure register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand()
        # return self.get_pos('MEASURE')

    @property
    def pos_shftenc(self):
        """
        Read the shftenc register (IcePAP user manual pag. 108).

        :return: int
        """
        # return self.get_pos('SHFTENC')
        return self._axis_nr + random.rand()
    
    @property
    def enc_tgtenc(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand() + 100
        # return self.get_pos('TGTENC')

    @property
    def enc_encin(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand() + 100        

    @property
    def enc_absenc(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand() + 100        

    @property
    def enc_inpos(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand() + 100        

    @property
    def enc_motor(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand() + 100        

    @property
    def enc_ctrlenc(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand() + 100        

    @property
    def enc_motor(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand() + 100        

    @property
    def enc_measure(self):
        """
        Read the tgtenc register (IcePAP user manual pag. 108).

        :return: int
        """
        return self._axis_nr + random.rand() + 100        

    @property
    def meas_vcc(self):
        """
        Measured value of the main power supply (IcePAP user manual pag. 89).

        :return: float
        """
        return self._axis_nr + random.rand() + 300  

    @property
    def meas_vm(self):
        """
        Measured value of the motor voltage (IcePAP user manual pag. 89).

        :return: float
        """
        return self._axis_nr + random.rand() + 100  

    @property
    def meas_i(self):
        """
        Measured value of the motor current (IcePAP user manual pag. 89).

        :return: float
        """
        return self._axis_nr + random.rand() + 100  

    @property
    def meas_ia(self):
        """
        Measured value of the phase a current (IcePAP user manual pag. 89).

        :return: float
        """
        return self._axis_nr + random.rand() + 100  

    @property
    def meas_ib(self):
        """
        Measured value of the phase b current (IcePAP user manual pag. 89).

        :return: float
        """
        return self._axis_nr + random.rand() + 100  

    @property
    def state_present(self):
        """
        Check if the present flag is active.

        :return: bool
        """
        return True

    @property
    def state_alive(self):
        """
        Check if the alive flag is active.

        :return: bool
        """
        return True

    @property
    def state_mode_code(self):
        """
        Return the current mode.

        :return: int
        """
        return 0

    @property
    def state_disabled(self):
        """
        Check if the disable flag is active.

        :return: bool
        """
        return True

    @property
    def state_disable_code(self):
        """
        Return the disable code.

        :return: int
        """
        return 0

    @property
    def state_indexer_code(self):
        """
        Return the indexer code.

        :return: int
        """
        return 0

    @property
    def state_moving(self):
        """
        Check if the moving flag is active.

        :return: bool
        """
        return True

    @property
    def state_ready(self):
        """
        Check if the ready flag is active.

        :return: bool
        """
        return True

    @property
    def state_settling(self):
        """
        Check if the settling flag is active.

        :return: bool
        """
        return False

    @property
    def state_outofwin(self):
        """
        Check if the outofwin flag is active.

        :return: bool
        """
        return False

    @property
    def state_warning(self):
        """
        Check if the warning flag is active.

        :return: bool
        """
        return True

    @property
    def state_stop_code(self):
        """
        Return the stop code.

        :return: int
        """
        return 0

    @property
    def state_limit_positive(self):
        """
        Check if the flag limit_positive is active.

        :return: bool
        """
        return False

    @property
    def state_limit_negative(self):
        """
        Check if the flag limit_negative is active.

        :return: bool
        """
        return False

    @property
    def state_inhome(self):
        """
        Chekc if the home flag is active.

        :return: bool
        """
        return False

    @property
    def state_5vpower(self):
        """
        Check if the auxiliary power is On.

        :return: bool
        """
        return False

    @property
    def state_verserr(self):
        """
        Check if the vererr flag is active.

        :return: bool
        """
        return False

    @property
    def state_poweron(self):
        """
        Check if the flag poweron is active.

        :return: bool
        """
        return False

    @property
    def state_info_code(self):
        """
        Return the info code.

        :return: int
        """
        return 0
    
    @property
    def velocity_current(self):
        """
        Read the default velocity (see get_velocity method).

        :return: float
        """
        return 1000.0 + random.rand()

    def get_velocity(self, vtype):
        """
        Read the default velocity (see get_velocity method).

        :return: float
        """
        if vtype:
            pass
        return 1000.0 + random.rand()
    
    

'''
            [('PosAxis', self._getter_pos_axis),
             ('PosTgtenc', self._getter_pos_tgtenc),
             ('PosShftenc', self._getter_pos_shftenc),
             ('PosEncin', self._getter_pos_encin),
             ('PosAbsenc', self._getter_pos_absenc),
             ('PosInpos', self._getter_pos_inpos),
             ('PosMotor', self._getter_pos_motor),
             ('PosCtrlenc', self._getter_pos_ctrlenc),
             ('PosMeasure', self._getter_pos_measure),
             ('DifAxMeasure', self._getter_dif_ax_measure),
             ('DifAxMotor', self._getter_dif_ax_motor),
             ('DifAxTgtenc', self._getter_dif_ax_tgtenc),
             ('DifAxShftenc', self._getter_dif_ax_shftenc),
             ('DifAxCtrlenc', self._getter_dif_ax_ctrlenc),
             ('EncEncin', self._getter_enc_encin),
             ('EncAbsenc', self._getter_enc_absenc),
             ('EncTgtenc', self._getter_enc_tgtenc),
             ('EncInpos', self._getter_enc_inpos),
             ('StatReady', self._getter_stat_ready),
             ('StatMoving', self._getter_stat_moving),
             ('StatSettling', self._getter_stat_settling),
             ('StatOutofwin', self._getter_stat_outofwin),
             ('StatStopcode', self._getter_stat_stopcode),
             ('StatWarning', self._getter_stat_warning),
             ('StatLim+', self._getter_stat_limit_positive),
             ('StatLim-', self._getter_stat_limit_negative),
             ('StatHome', self._getter_stat_home),
             ('MeasI', self._getter_meas_i),
             ('MeasIa', self._getter_meas_ia),
             ('MeasIb', self._getter_meas_ib),
             ('MeasVm', self._getter_meas_vm),
             ('VelCurrent', self._getter_vel_current),
             ('VelMotor', self._getter_vel_motor)]
'''

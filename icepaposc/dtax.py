class dtax:
    # Get the info to add new params to this list from the advanced user guide
    # . There's a table there of 32b params, rest are 16b.
    registerTab = []
    # Choose speed units defining speedFactor
    speedFactorRPM = 1.0
    speedFactorRPS = 1 / 60.0  # speeds in rps instead of rpms
    speedFactorMMGap = (1 / 60.0) * (16400 / 157299.06)
    speedFactorMMPhase = (1 / 60.0) * (16400 / 47025.08961)
    speedFactorFlexpes = (1 / 60.0) * (16400 / 98400)
    speedFactor = speedFactorRPS
    # Choose position units defining positionFactor and positionRevFactor
    # Digitax uses 3 registers, but the positionFines is not useful
    positionFactorMMGap = (1 / 2**16) * (16400 / 157299.06)
    positionFactorMMPhase = (1 / 2**16) * (16400 / 47025.08961)
    positionFactorFlexpes = (1 / 2**16) * (16400 / 98400)
    positionFactorDigitaxSteps = 1.0
    positionFactor = positionFactorDigitaxSteps
    positionRevFactorMMGap = (1 / 1) * (
        16400 / 157299.06
    )  # I have not explained the 1.25 factor and am using posmotor pos reg?
    positionRevFactorMMPhase = (1 / 1) * (16400 / 47025.08961)
    positionRevFactorFlexpes = (1 / 1) * (16400 / 98400)
    positionRevFactorRevs = 1.0
    positionRevFactor = positionRevFactorRevs
    # These constants are now read from the hw
    ktGap = 2.4
    ktPhase = 1.6
    ktFlexpes = 1  # ??
    keGap = 0.147
    kePhase = 0.098
    keFlexpes = 1  # ??
    # These constants are not used by this sw
    SPEED_LIMIT_MAX = 5e5 * 60 / 1024  # fenc<500e3 30krpm
    SPEED_REF_MAX = 3e3  # rpm. 1.06 or 1.07 (clamps) 50rps
    SPEED_MAX = 2 * SPEED_REF_MAX  # 100rps
    KC_1401 = 2.58  # A.
    KC_1402 = 4.63  # A.
    # Internal dtax factors. Advanced user guide 5.6, menu4
    # maxcurrrating = 0.581*kc(kc/1.72)
    # maxstdoperatingcur or maximum current=1.75*kc(kc/0.58)
    # overcurrenttrip or drivecurrentmax = 2.222*kc (kc/0.45)
    #
    # besides those fixed values,
    # the following depend on the configured motor rated current:
    # percentage of it, most often configured in params to 300%
    # if they are given by params,
    # otherwise they max out at drivermaxstdoperatingcur/motorrated):
    # MOTOR_CURRENT_LIMIT_MAX, USER_CURRENT_MAX, TORQUE_PROD_CURRENT_MAX
    #
    # These constants are not used anymore, left here for historycal reasons
    DRIVE_CURRENT_MAX_1401 = KC_1401 / 0.45
    DRIVE_CURRENT_MAX_1402 = KC_1402 / 0.45
    DC_VOLTAGE_MAX_14XX = 830
    DC_VOLTAGE_MAX = DC_VOLTAGE_MAX_14XX
    AC_VOLTAGE_MAX = 0.78 * DC_VOLTAGE_MAX
    MOTOR_CURRENT_RATED_GAP = 1.0  # 5.07
    MOTOR_CURRENT_RATED_PHASE = 2.38  # 5.07
    MOTOR_CURRENT_RATED_FLEXPES = 2.38  #
    MOTOR_R_GAP = 48.2  # Ohm
    MOTOR_R_PHASE = 7.5
    MOTOR_L_GAP = 33.664
    MOTOR_L_PHASE = 19.7  # mH
    MOTOR_CURRENT_RATED_MAX_1401 = 1.5  # 11.32 or 1.75KC/3
    MOTOR_CURRENT_RATED_MAX_1402 = 2.7  # 11.32
    # Power constants
    POWER_MAX_1401 = 1.732 * AC_VOLTAGE_MAX * DRIVE_CURRENT_MAX_1401
    POWER_MAX_1402 = 1.732 * AC_VOLTAGE_MAX * DRIVE_CURRENT_MAX_1402
    # In general signals reading currents are to be converted against pu
    # But parameters specifying currents in % (for limits) are supposed to be read against motor rated current
    # And the readbacks from the motor are directly in amps (to make life easy)
    # These constants are not used anymore by the top level ds (it reads from hw and calculates at init, then adjusts factor from them)
    CURRENT_PU_GAP = KC_1401 / MOTOR_CURRENT_RATED_GAP
    CURRENT_PU_PHASE = KC_1402 / MOTOR_CURRENT_RATED_PHASE
    CURRENT_PU_FLEXPES = KC_1402 / MOTOR_CURRENT_RATED_FLEXPES
    # Comment this out if running in flexpes
    # CURRENT_PU_PHASE = CURRENT_PU_FLEXPES
    ct1401 = [
        KC_1401,
        DC_VOLTAGE_MAX,
        AC_VOLTAGE_MAX,
        DRIVE_CURRENT_MAX_1401,
        MOTOR_CURRENT_RATED_MAX_1401,
        POWER_MAX_1401,
    ]
    ct1402 = [
        KC_1402,
        DC_VOLTAGE_MAX,
        AC_VOLTAGE_MAX,
        DRIVE_CURRENT_MAX_1402,
        MOTOR_CURRENT_RATED_MAX_1402,
        POWER_MAX_1402,
    ]
    ctheaders = [
        "kc",
        "DCVmax",
        "ACVmax",
        "DrImax",
        "MotIratedmax",
        "PowerMax",
    ]
    dtax_params = {}
    dtax_params["4.20"] = {
        "menu": 4,
        "register": 20,
        "dtype": "int16",
        "signed": True,
        "factor": 0.1 * CURRENT_PU_GAP * 0.01,  # 65433 res 0.1A
        "scale": True,
        "desc": "torque producing current as percentage of user current max bip % user current max",
        "default": 65433,
        "getter": "get_currentTorqueProducing",
        "unit": "A",
        "factor_type": "pu",
    }  # gap motors
    dtax_params["4.19"] = {
        "menu": 4,
        "register": 19,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,  # 0..100.0 %10 ?max temp?
        "scale": True,
        "desc": "percentage of maximum temperature, 0..100.0",
        "default": 1,
        "getter": "get_tempEstimatedMotorPerCentOfMax",
        "unit": "%",
    }
    dtax_params["7.03"] = {
        "menu": 7,
        "register": 3,
        "dtype": "int16",
        "signed": True,
        "factor": 100 * (1 / 3300) * (1e4 / 100) * 0.1,
        "scale": True,
        "desc": "percentage of 10k alarm >3k3 rst <1k8 0.1%",
        "default": 11,
        "getter": "get_tempPerCentOfPTCAlarm",
        "unit": "%",
    }
    dtax_params["0.02"] = {
        "menu": 0,
        "register": 2,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1 * speedFactor,
        "scale": True,
        "desc": "max ref clamp in rpm",
        "default": 30000,
        "getter": "get_speedClampReferenceMax",
        "unit": "rpm",
    }
    dtax_params["5.11"] = {
        "menu": 5,
        "register": 11,
        "dtype": "int16",
        "signed": False,
        "factor": 1.0,
        "scale": True,
        "desc": "Number of poles (pairs)",
        "default": 3,  # val 3 for 6 poles
        "getter": "get_polePairs",
        "unit": "",
    }
    dtax_params["2.02"] = {
        "menu": 2,
        "register": 2,
        "dtype": "int16",
        "signed": False,
        "factor": 1.0,
        "scale": True,
        "desc": "Ramp enable",
        "default": 0,
        "getter": "get_confRampEnabled",
        "unit": "b",
    }
    dtax_params["2.38"] = {
        "menu": 2,
        "register": 38,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,
        "scale": True,
        "desc": "Inertia compensation torque",
        "default": 0,
        "getter": "get_torqueInertiaCompensation",
        "unit": "%",
    }
    dtax_params["3.18"] = {
        "menu": 3,
        "register": 18,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,
        "scale": True,
        "desc": "Inertia compensation torque",
        "default": 0,
        "getter": "get_inertiaMotorNLoad",
        "unit": "kg*cm2",
    }
    dtax_params["3.19"] = {
        "menu": 3,
        "register": 19,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,
        "scale": True,
        "desc": "compliance angle 0.1 deg",
        "default": 0,
        "getter": "get_angleCompliance",
        "unit": "deg",
    }
    dtax_params["3.20"] = {
        "menu": 3,
        "register": 20,
        "dtype": "int16",
        "signed": False,
        "factor": 1,
        "scale": True,
        "desc": "Bandwidth Hz",
        "default": 0,
        "getter": "get_bandwidth",
        "unit": "Hz",
    }
    dtax_params["3.21"] = {
        "menu": 3,
        "register": 21,
        "dtype": "int16",
        "signed": False,
        "factor": 1,
        "scale": True,
        "desc": "Damping factor",
        "default": 0,
        "getter": "get_dampingFactor",
        "unit": "a.u.",
    }
    dtax_params["3.25"] = {
        "menu": 3,
        "register": 25,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,
        "scale": True,
        "desc": "Encoder phasing angle",
        "default": 0,
        "getter": "get_angleEncoderPhasing",
        "unit": "deg",
    }
    dtax_params["3.34"] = {
        "menu": 3,
        "register": 34,
        "dtype": "int16",
        "signed": False,
        "factor": 1,
        "scale": True,
        "desc": "Shaft encoder lines per rev",
        "default": 0,
        "getter": "get_linesPerRevShaftEncoder",
        "unit": "",
    }
    dtax_params["3.42"] = {
        "menu": 3,
        "register": 42,
        "dtype": "int16",
        "signed": False,
        "factor": 1,
        "scale": True,
        "desc": "Drive encoder sliding window filter time ms",
        "default": 0,
        "getter": "get_timeWindowFilterShaftEncoder",
        "unit": "ms",
    }
    dtax_params["5.26"] = {
        "menu": 5,
        "register": 26,
        "dtype": "int16",
        "signed": False,
        "factor": 1,
        "scale": True,
        "desc": "High dynamic performance enable",
        "default": 0,
        "getter": "get_modeHighDynamicOn",
        "unit": "",
    }
    dtax_params["5.31"] = {
        "menu": 5,
        "register": 31,
        "dtype": "int16",
        "signed": False,
        "factor": 1,
        "scale": True,
        "desc": "Voltage controller gain",
        "default": 0,
        "getter": "get_voltageKp",
        "unit": "",
    }
    dtax_params["13.10"] = {
        "menu": 13,
        "register": 10,
        "dtype": "int16",
        "signed": False,
        "factor": 1,
        "scale": True,
        "desc": "Position controller mode",
        "default": 0,
        "getter": "get_confPositionControllerMode",
        "unit": "",
    }
    dtax_params["13.09"] = {
        "menu": 13,
        "register": 9,
        "dtype": "int16",
        "signed": False,
        "factor": 0.01,
        "scale": True,
        "desc": "Position controller kp",
        "default": 0,
        "getter": "get_positionKp",
        "unit": "rads-1/rad",
    }
    dtax_params["13.12"] = {
        "menu": 13,
        "register": 12,
        "dtype": "int16",
        "signed": False,
        "factor": 1,
        "scale": True,
        "desc": "Position controller speed clamp",
        "default": 0,
        "getter": "get_speedClampPositionController",
        "unit": "rpm",
    }

    dtax_params["0.36"] = {
        "menu": 0,
        "register": 36,
        "dtype": "int16",
        "signed": False,
        "factor": 1.0,
        "scale": True,
        "desc": "Baud rate serial comm",
        "default": 6,  # 6 19200 9 115200
        "getter": "get_baudRate",
        "unit": "",
    }
    dtax_params["0.37"] = {
        "menu": 0,
        "register": 37,
        "dtype": "int16",
        "signed": False,
        "factor": 1.0,
        "scale": True,
        "desc": "Address serial comm",
        "default": 1,
        "getter": "get_modbusAddress",
        "unit": "",
    }
    dtax_params["5.32"] = {
        "menu": 5,
        "register": 32,
        "dtype": "int16",
        "signed": False,
        "factor": 0.01,
        "scale": True,
        "desc": "Motor Kt torque constant, 0 to 500.00 NmA-1 (240 1.6)",
        "default": 240,  # 1.6 for p and 2.4 for g
        "getter": "get_kt",
        "unit": "Nm/A",
    }
    dtax_params["5.33"] = {
        "menu": 5,
        "register": 33,
        "dtype": "int16",
        "signed": False,
        "factor": 0.001,
        "scale": True,
        "desc": "Motor Ke bemf constant",
        "default": 240,  # 1.6 for p and 2.4 for g
        "getter": "get_ke",
        "unit": "V/rpm",
    }
    dtax_params["4.15"] = {
        "menu": 4,
        "register": 15,
        "dtype": "int16",
        "signed": False,
        "factor": 1,
        "scale": True,
        "desc": "Motor thermal time constant",
        "default": 240,  # 1.6 for p and 2.4 for g
        "getter": "get_thermalTimeConstant",
        "unit": "s",
    }
    dtax_params["4.05"] = {
        "menu": 4,
        "register": 5,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,  # res 0.1A
        # "factor": 1,  # res 0.1A
        "scale": True,
        "desc": "Motoring current limit 0.1 (percentage of motor rated current)",
        "default": 903.0,  # 3k for 13.545# 300.0
        "getter": "get_currentLimitMotoring",
        "unit": "% of Imotorrated",
        "factor_type": "%",
    }
    dtax_params["4.06"] = {
        "menu": 4,
        "register": 6,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,  # res 0.1A
        # "factor": 1,  # res 0.1A
        "scale": True,
        "desc": "Regen current limit 0.1",
        "default": 903.0,  # 3k for 13.545# 300.0
        "getter": "get_currentLimitRegen",
        "unit": "% of Imotorrated",
        "factor_type": "%",
    }
    dtax_params["4.07"] = {
        "menu": 4,
        "register": 7,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,  # res 0.1A
        # "factor": 1,  # res 0.1A
        "scale": True,
        "desc": "Symmetrical current limit 0.1",
        "default": 903.0,  # 3k for 13.545# 300.0
        "getter": "get_currentLimitSym",
        "unit": "% of Imotorrated",
        "factor_type": "%",
    }
    dtax_params["4.18"] = {
        "menu": 4,
        "register": 18,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,  # res 0.1A
        # "factor": 1,  # res 0.1A
        "scale": True,
        "desc": "Overriding current limit 0.1",
        "default": 903.0,  # 3k for 13.545# 300.0
        "getter": "get_currentLimitOverriding",
        "unit": "% of Imotorrated",
        "factor_type": "%",
    }
    dtax_params["0.06"] = {
        "menu": 0,
        "register": 6,
        "dtype": "int16",
        "signed": False,
        "factor": 0.1,  # res 0.1A
        "scale": True,
        "desc": "Symmetrical current limit in % of CLM res 0.1",
        "default": 903.0,  # 3k for 13.545# 300.0
        "getter": "get_currentLimit",
        "unit": "% of Imotorrated",
        "factor_type": "%",
    }
    dtax_params["0.07"] = {
        "menu": 0,
        "register": 7,
        "dtype": "int16",
        "signed": False,
        "factor": 1e-4,
        "scale": True,  # 5
        "desc": "Kp1 of velocity controller [0..6.5535] 1/rads-1",
        "default": 0.01,  # 100 for 0.0100 as int16, 1 as int32# 0.01, ? #
        "getter": "get_velocityControllerKp",
        "unit": "",
    }
    dtax_params["0.08"] = {
        "menu": 0,
        "register": 8,
        "dtype": "int16",
        "signed": False,
        "factor": 0.01,
        "scale": True,
        "desc": "Ki1 of velocity controller [0..655.35 1/rad]",
        "default": 16,  # 16 for p and 1 for g
        "getter": "get_velocityControllerKi",
        "unit": "1/rad",
    }
    ########################
    dtax_params["0.27"] = {
        "menu": 0,
        "register": 27,
        "dtype": "int16",
        "signed": False,
        "factor": 4.0,
        "scale": True,
        "desc": "Shaft encoder lines per revolution mb 1024, 4096 in app",
        "default": 1024,  # 1024 *4
        "getter": "get_shaftEncoderLinesPerRev",
        "unit": "",
    }
    dtax_params["0.09"] = {
        "menu": 0,
        "register": 9,
        "dtype": "int16",
        "signed": False,
        "factor": 0.01,
        "scale": True,
        "desc": "Speed controller D gain 0.65535 1/rads-1",
        "default": 0,  # 0.00000,
        "getter": "get_velocityControllerKd",
        "unit": "s",
    }
    dtax_params["11.32"] = {
        "menu": 11,
        "register": 32,
        "dtype": "int16",  # "int32",  #
        "signed": False,
        "factor": 0.01,
        "scale": True,
        "desc": "Motor maximum rated current 0..9999.99A",
        "default": 1.0,
        "getter": "get_currentRatedMaximumDriver",
        "unit": "A",
    }
    dtax_params["5.07"] = {
        "menu": 5,
        "register": 7,
        "dtype": "int16",  #
        "signed": False,
        "factor": 0.01,  #
        "scale": True,
        "desc": "Motor rated current max is 11.32 par",
        "default": 6.42,  # 238 i16
        "getter": "get_currentRatedMotor",
        "unit": "A",
    }
    dtax_params["5.08"] = {
        "menu": 5,
        "register": 8,
        "dtype": "int16",  #
        "signed": False,
        "factor": 0.1,  #
        "scale": True,
        "desc": "Motor rated speed",
        "default": 6.42,  # 238 i16
        "getter": "get_speedRatedMotor",
        "unit": "rpm",
    }
    dtax_params["5.09"] = {
        "menu": 5,
        "register": 9,
        "dtype": "int16",  #
        "signed": False,
        "factor": 1,  #
        "scale": True,
        "desc": "Motor rated voltage",
        "default": 6.42,  # 238 i16
        "getter": "get_voltageRatedMotor",
        "unit": "V",
    }
    dtax_params["5.24"] = {
        "menu": 5,
        "register": 24,
        "dtype": "int16",  #
        "signed": False,
        "factor": 0.001,  #
        "scale": True,
        "desc": "Motor phase inductance",
        "default": 6.42,  # 238 i16
        "getter": "get_inductanceMotor",
        "unit": "mH",
    }
    dtax_params["5.17"] = {
        "menu": 5,
        "register": 17,
        "dtype": "int16",  #
        "signed": False,
        "factor": 0.001 * 10,  #
        "scale": True,
        "desc": "Stator resistance (0.001 res is 10 Ohm)",
        "default": 6.42,  # 238 i16
        "getter": "get_resistanceMotor",
        "unit": "Ohm",
    }
    dtax_params["5.01"] = {
        "menu": 5,
        "register": 1,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  # AC_VOLTAGE_SET_MAX,
        "scale": True,
        "desc": "frequency Output bip 1250 Hz (regulation probably at controller reference frame)",
        "default": 400,
        "getter": "get_frequencyOutput",
        "unit": "V",
    }
    dtax_params["7.34"] = {
        "menu": 7,
        "register": 34,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  # AC_VOLTAGE_SET_MAX,
        "scale": True,
        "desc": "IGBT junction temperature bip 200degc",
        "default": 400,
        "getter": "get_tempIGBT",
        "unit": "degree",
    }
    dtax_params["7.35"] = {
        "menu": 7,
        "register": 35,
        "dtype": "int16",  #
        "signed": False,
        "factor": 1.0,  # AC_VOLTAGE_SET_MAX,
        "scale": True,
        "desc": "Thermal protection accumulator 0 100% of trip level ",
        "default": 400,
        "getter": "get_tempThermalAccumulator100",
        "unit": "%",
    }
    dtax_params["7.36"] = {
        "menu": 7,
        "register": 36,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  # AC_VOLTAGE_SET_MAX,
        "scale": True,
        "desc": "Power circuit temperature 3 bip 127deg",
        "default": 27,
        "getter": "get_tempPowerCircuit3",
        "unit": "%",
    }
    dtax_params["7.04"] = {
        "menu": 7,
        "register": 4,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  # AC_VOLTAGE_SET_MAX,
        "scale": True,
        "desc": "Power circuit temperature 1 bip 127deg",
        "default": 27,
        "getter": "get_tempPowerCircuit1",
        "unit": "%",
    }
    dtax_params["7.05"] = {
        "menu": 7,
        "register": 5,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  # AC_VOLTAGE_SET_MAX,
        "scale": True,
        "desc": "Power circuit temperature 2 bip 127deg",
        "default": 27,
        "getter": "get_tempPowerCircuit2",
        "unit": "%",
    }
    dtax_params["7.06"] = {
        "menu": 7,
        "register": 6,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  # AC_VOLTAGE_SET_MAX,
        "scale": True,
        "desc": "Control board temperature bip 127deg",
        "default": 27,
        "getter": "get_tempControlBoard",
        "unit": "%",
    }
    dtax_params["5.09"] = {
        "menu": 5,
        "register": 9,
        "dtype": "int16",  #
        "signed": False,
        "factor": 1.0,  # AC_VOLTAGE_SET_MAX,
        "scale": True,
        "desc": "Motor rated voltage",
        "default": 400,
        "getter": "get_voltageRatedMotor",
        "unit": "V",
    }
    dtax_params["5.33"] = {
        "menu": 5,
        "register": 33,
        "dtype": "int16",  #
        "signed": False,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Motor volts per 1krpm (Ke) 0..1e4, 147 for 98.0",
        "default": 147,  # 98 for g 147 for g
        "getter": "get_ke",
        "unit": "",
    }
    dtax_params["1.39"] = {
        "menu": 1,
        "register": 39,
        "dtype": "int16",  # "int32",  #
        "signed": True,
        "factor": 0.1 * speedFactor,  # ??
        "scale": True,
        "desc": "Velocity feed forward reference, 40000.0 rpm",
        "default": 1,  # ?i32 983041 f err
        "getter": "get_speedFFReference",
        "unit": "rpm",
    }
    dtax_params["3.01"] = {
        "menu": 3,
        "register": 1,
        "dtype": "int16",  # "int32",  # but it is a 32b param so somethign is wrong?
        "signed": True,
        "factor": 0.1 * speedFactor,  # but could be 0.1 ??
        "scale": True,
        "desc": "Final speed reference speed_max_rpm 0.1",
        "default": 1,  # ?i16 65535, i32, f err
        "getter": "get_speedReference",
        "unit": "rpm",
    }
    dtax_params["1.03"] = {
        "menu": 1,
        "register": 3,
        "dtype": "int16",  # "int32",  # but it is a 32b param so somethign is wrong?
        "signed": True,
        "factor": 0.1 * speedFactor,  # but could be 0.1 ??
        "scale": True,
        "desc": "Pre ramp speed reference speed_max_rpm",
        "default": 1,  # ?i16 65535, i32, f err
        "getter": "get_speedReferencePreRamp",
        "unit": "rpm",
    }
    dtax_params["2.01"] = {
        "menu": 2,
        "register": 1,
        "dtype": "int16",  # "int32",  # but it is a 32b param so somethign is wrong?
        "signed": True,
        "factor": 0.1 * speedFactor,  # but could be 0.1 ??
        "scale": True,
        "desc": "Post ramp speed reference speed_max_rpm",
        "default": 1,  # ?i16 65535, i32, f err
        "getter": "get_speedReferencePostRamp",
        "unit": "rpm",
    }
    dtax_params["3.22"] = {
        "menu": 3,
        "register": 22,
        "dtype": "int16",  # "int32",  # but it is a 32b param so somethign is wrong?
        "signed": True,
        "factor": 0.1 * speedFactor,  # but could be 0.1 ??
        "scale": True,
        "desc": "Hard speed reference speed_max_rpm",
        "default": 1,  # ?i16 65535, i32, f err
        "getter": "get_speedReferenceHard",
        "unit": "rpm",
    }
    dtax_params["3.27"] = {
        "menu": 3,
        "register": 27,
        "dtype": "int16",  # "float",  # 3.27 is a 32bpar but maybe int32 0.1
        "signed": True,
        "factor": 0.1 * speedFactor,  # but maybe0.1,  # ??
        "scale": True,
        "desc": "Drive shaft encoder speed feedback, 40.0krpm",
        "default": 1,  # ?9.94e-32 as f works, others not
        "getter": "get_speedFeedback",
        "unit": "rpm",
    }
    dtax_params["15.03"] = {
        "menu": 15,
        "register": 3,
        "dtype": "int16",  # 3.27 is a 32bpar but maybe int32 0.1
        "signed": True,
        "factor": 0.1 * speedFactor,  # but maybe0.1,  # ??
        "scale": True,
        "desc": "Drive encoder slot1 speed feedback, 40.0krpm",
        "default": 1,  # ?9.94e-32 as f works, others not
        "getter": "get_speedFeedbackSl1",
        "unit": "rpm",
    }
    dtax_params["3.02"] = {
        "menu": 3,
        "register": 2,
        "dtype": "int16",  # 3.02 32b par
        "signed": True,
        "factor": 0.1 * speedFactor,  #
        "scale": True,  # False,  # ??
        "desc": "Speed feedback after 3.27 bip speed_max_rpm 0.1",
        "default": 1,  # ?only reads as i16 65535, ?
        "getter": "get_speedFinalFeedback",
        "unit": "rpm",
    }
    dtax_params["3.03"] = {
        "menu": 3,
        "register": 3,
        "dtype": "int16",  # "int32",  # but 3.03 is a 32b par
        "signed": True,
        "factor": 0.1 * speedFactor,  #
        "scale": True,  # False,  # ??
        "desc": "Speed error speed_max_rpm",
        "default": 1,  # ?only reads as i16 65535, ?
        "getter": "get_speedError",
        "unit": "rpm",
    }
    dtax_params["3.04"] = {
        "menu": 3,
        "register": 4,
        "dtype": "int16",  #
        "signed": True,
        "factor": (CURRENT_PU_GAP) * 0.01 * 0.1,
        "scale": True,
        "desc": "Speed controller output in Amps 0.1%, tDem, IDem",
        "default": 1,  # ? i16 65464 i32 0 f err
        "getter": "get_speedControllerOutput",
        "unit": "A",
        "factor_type": "pu",
    }
    dtax_params["4.01"] = {
        "menu": 4,
        "register": 1,
        "dtype": "int16",  # "float",  # 4.01 is 32bpar int32 err
        "signed": False,
        "factor": 0.01,  # 0.1,  # 1.0,  # as with 4.02 only int16 and 0.1A res match the drive output
        "scale": True,
        "desc": "Motor drive current magnitude phase rms 0.01",
        "default": 0,  # ?6 f 0 i32 err
        "getter": "get_currentMagnitudeRMS",
        "unit": "A",
    }
    """
    dtax_params["4.01g"] = {
        "menu": 4,
        "register": 1,
        "dtype": "int16",  # "float",  # 4.01 is 32bpar int32 err
        "signed": False,
        "factor": 0.01
        * DRIVE_CURRENT_MAX_1401,  # 0.1,  # 1.0,  # as with 4.02 only int16 and 0.1A res match the drive output
        "scale": True,
        "desc": "Motor drive current magnitude phase rms 0.01 DRIVE_CURRENT_MAX_14",
        "default": 0,  # ?6 f 0 i32 err
        "getter": "get_currentMagnitudeRMS",
        "unit": "A",
    }
    dtax_params["4.01p"] = {
        "menu": 4,
        "register": 1,
        "dtype": "int16",  # "float",  # 4.01 is 32bpar int32 err
        "signed": False,
        "factor": 0.01
        * DRIVE_CURRENT_MAX_1402,  # 0.1,  # 1.0,  # as with 4.02 only int16 and 0.1A res match the drive output
        "scale": True,
        "desc": "Motor drive current magnitude phase rms 0.01 DRIVE_CURRENT_MAX_14",
        "default": 0,  # ?6 f 0 i32 err
        "getter": "get_currentMagnitudeRMS",
        "unit": "A",
    }
    """
    dtax_params["4.02"] = {
        "menu": 4,
        "register": 2,
        "dtype": "int16",  # "float",  # 4.02 is 32b but only makes sense as i16
        "signed": True,
        "factor": 0.01,  # 0.1,  # The drive unit seems 0.1A
        "scale": True,
        "desc": "Motor active current DRIVE_CURRENT_MAX_140x 0.01 ",
        "default": 0,  # i32 err, f 0.0 ?
        "getter": "get_currentActiveRMS",
        "unit": "A",
    }
    """
    dtax_params["4.02g"] = {
        "menu": 4,
        "register": 2,
        "dtype": "int16",  # "float",  # 4.02 is 32b but only makes sense as i16
        "signed": True,
        "factor": 0.01 * DRIVE_CURRENT_MAX_1401,  # 0.1,  # The drive unit seems 0.1A
        "scale": True,
        "desc": "Motor active current DRIVE_CURRENT_MAX_140x 0.01 ",
        "default": 0,  # i32 err, f 0.0 ?
        "getter": "get_currentActiveRMS",
        "unit": "A",
    }
    dtax_params["4.02p"] = {
        "menu": 4,
        "register": 2,
        "dtype": "int16",  # "float",  # 4.02 is 32b but only makes sense as i16
        "signed": True,
        "factor": 0.01 * DRIVE_CURRENT_MAX_1402,  # 0.1,  # The drive unit seems 0.1A
        "scale": True,
        "desc": "Motor active current DRIVE_CURRENT_MAX_140x 0.01 ",
        "default": 0,  # i32 err, f 0.0 ?
        "getter": "get_currentActiveRMS",
        "unit": "A",
    }
    """
    dtax_params["4.17"] = {
        "menu": 4,
        "register": 17,
        "dtype": "int16",  # "float",  # 4.17 is 32b same as 4.01/2
        "signed": True,
        "factor": 0.01,  # 0.1,  # 1.0,  #
        "scale": True,
        "desc": "Motor reactive current DRIVE_CURRENT_MAX_140x 0.01 ",
        "default": 1,  # i32 err f 0?
        "getter": "get_currentReactiveRMS",
        "unit": "A",
    }
    """
    dtax_params["4.17g"] = {
        "menu": 4,
        "register": 17,
        "dtype": "int16",  # "float",  # 4.17 is 32b same as 4.01/2
        "signed": True,
        "factor": 0.01 * DRIVE_CURRENT_MAX_1401,  # 0.1,  # 1.0,  #
        "scale": True,
        "desc": "Motor reactive current DRIVE_CURRENT_MAX_140x 0.01 ",
        "default": 1,  # i32 err f 0?
        "getter": "get_currentReactiveRMS",
        "unit": "A",
    }
    dtax_params["4.17p"] = {
        "menu": 4,
        "register": 17,
        "dtype": "int16",  # "float",  # 4.17 is 32b same as 4.01/2
        "signed": True,
        "factor": 0.01 * DRIVE_CURRENT_MAX_1402,  # 0.1,  # 1.0,  #
        "scale": True,
        "desc": "Motor reactive current DRIVE_CURRENT_MAX_140x 0.01 ",
        "default": 1,  # i32 err f 0?
        "getter": "get_currentReactiveRMS",
        "unit": "A",
    }
    """
    dtax_params["4.24"] = {
        "menu": 4,
        "register": 24,
        "dtype": "int16",  # 16b param
        "signed": False,
        # "factor": (CURRENT_PU_GAP) * 0.01 * 0.1,
        "factor": 0.1,
        "scale": True,
        "desc": "Torque demand (after vl output) bip % Torque prod curr max (same as curr demand before a clamper)",
        "default": 0,  # f 9.18e-41, i32 err?
        "getter": "get_currentUserMax",
        "unit": "% of Imotorrated",
        "factor_type": "%",
    }
    dtax_params["4.03"] = {
        "menu": 4,
        "register": 3,
        "dtype": "int16",  # 16b param
        "signed": True,
        "factor": (CURRENT_PU_GAP) * 0.01 * 0.1,
        "scale": True,
        "desc": "Torque demand (after vl output) bip % Torque prod curr max (same as curr demand before a clamper)",
        "default": 0,  # f 9.18e-41, i32 err?
        "getter": "get_torqueDemand",
        "unit": "A",
        "factor_type": "pu",
    }
    dtax_params["4.04"] = {
        "menu": 4,
        "register": 4,
        "dtype": "int16",  #
        "signed": True,
        "factor": (CURRENT_PU_GAP) * 0.01 * 0.1,
        "scale": True,
        "desc": "Current demand % of torque prod current max 0.1",
        "default": 65514,  # i32 2 f 1.401e-45?
        "getter": "get_currentDemand",
        "unit": "A",
        "factor_type": "pu",
    }
    dtax_params["4.08"] = {
        "menu": 4,
        "register": 8,
        "dtype": "int16",  #
        "signed": True,
        "factor": CURRENT_PU_GAP * 0.01 * 0.01,  # * 0.1,  #
        "scale": True,
        "desc": "Torque reference % user current max 0.01",
        "default": 0,  # i32 err ?
        "getter": "get_torqueReference",
        "unit": "A",
        "factor_type": "pu",
    }
    dtax_params["3.28"] = {
        "menu": 3,
        "register": 28,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Position loop fb rev",
        "default": 0,  # i32 er f 1.4e-41?
        "getter": "get_positionFbRev",
        "unit": "",
    }
    dtax_params["3.29"] = {
        "menu": 3,
        "register": 29,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Position loop fb pos",
        "default": 1,  # ?
        "getter": "get_positionFbPos",
        "unit": "",
    }
    dtax_params["3.30"] = {
        "menu": 3,
        "register": 30,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Position loop fb fine",
        "default": 1,  # ?v
        "getter": "get_positionFbFine",
        "unit": "",
    }
    dtax_params["13.01"] = {
        "menu": 13,
        "register": 1,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Position loop error rev",
        "default": 0,  # i32 er f 1.4e-41?
        "getter": "get_positionErrorRev",
        "unit": "",
    }
    dtax_params["13.02"] = {
        "menu": 13,
        "register": 2,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Position loop error pos",
        "default": 1,  # ?
        "getter": "get_positionErrorPos",
        "unit": "",
    }
    dtax_params["13.03"] = {
        "menu": 13,
        "register": 3,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Position loop error fine",
        "default": 1,  # ?v
        "getter": "get_positionErrorFine",
        "unit": "",
    }
    dtax_params["15.04"] = {
        "menu": 15,
        "register": 4,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Position loop ref rev",
        "default": 0,  # i32 er f 1.4e-41?
        "getter": "get_positionRefRev",
        "unit": "",
    }
    dtax_params["15.05"] = {
        "menu": 15,
        "register": 5,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Position loop ref pos",
        "default": 1,  # ?
        "getter": "get_positionRefPos",
        "unit": "",
    }
    dtax_params["15.06"] = {
        "menu": 15,
        "register": 6,
        "dtype": "int16",  #
        "signed": True,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Position loop ref fine",
        "default": 1,  # ?v
        "getter": "get_positionRefFine",
        "unit": "",
    }
    dtax_params["5.02"] = {
        "menu": 5,
        "register": 2,
        "dtype": "int16",  #
        "signed": False,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Output voltage",
        "default": 1,  # ?v
        "getter": "get_voltageOutputMotor",
        "unit": "V",
    }
    dtax_params["5.03"] = {
        "menu": 5,
        "register": 3,
        "dtype": "float",  # "int32",  #
        "signed": False,
        "factor": 1.0,  #
        "scale": True,
        "desc": "Output Power 0..POWER_MAX 0.01kW",
        "default": 1,  # ?v
        "getter": "get_powerOutput",
        "unit": "kW",
    }
    dtax_params["5.05"] = {
        "menu": 5,
        "register": 5,
        "dtype": "int16",  #
        "signed": False,
        "factor": 1.0,  #
        "scale": True,
        "desc": "DC bus voltage",
        "default": 565.0,  # ?v
        "getter": "get_voltageDCBus",
        "unit": "V",
    }

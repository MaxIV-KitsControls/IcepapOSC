class dtax:
    # Get the info to add new params to this list from the advanced user guide
    # . There's a table there of 32b params, rest are 16b.
    registerTab = []
    speedFactor = 1 / 60.0  # speeds in rps instead of rpms
    speedFactorMMGap = (1 / 60.0) * (16400 / 157299.06)
    speedFactorMMPhase = (1 / 60.0) * (16400 / 47025.08961)
    speedFactorFlexpes = (1 / 60.0) * (16400 / 98400)
    positionFactorMMGap = (1 / 2**16) * (16400 / 157299.06)
    positionFactorMMPhase = (1 / 2**16) * (16400 / 47025.08961)
    positionFactorFlexpes = (1 / 2**16) * (16400 / 98400)
    positionRevFactorMMGap = (1 / 1) * (
        16400 / 157299.06
    )  # I have not explained the 1.25 factor and am using posmotor
    positionRevFactorMMPhase = (1 / 1) * (16400 / 47025.08961)
    positionRevFactorFlexpes = (1 / 1) * (16400 / 98400)
    ktGap = 2.4
    ktPhase = 1.6
    ktFlexpes = 1  # ??
    keGap = 0.147
    kePhase = 0.098
    keFlexpes = 1  # ??
    SPEED_LIMIT_MAX = 5e5 * 60 / 1024  # fenc<500e3 30krpm
    SPEED_REF_MAX = 3e3  # rpm. 1.06 or 1.07 (clamps) 50rps
    SPEED_MAX = 2 * SPEED_REF_MAX  # 100rps
    # 11.32 max mot rated 1.75KC/3
    # max drive kc/0.45 and maxmot 1.75kc
    # 5.07 mot rated and mot max 1.75kc/motrated
    # 4.24 user curr max (% of rated max)
    KC_1401 = 2.58  # A.
    KC_1402 = 4.63  # A.
    DRIVE_CURRENT_MAX_1401 = KC_1401 / 0.45
    DRIVE_CURRENT_MAX_1402 = KC_1402 / 0.45
    DC_VOLTAGE_MAX_14XX = 830
    DC_VOLTAGE_MAX = DC_VOLTAGE_MAX_14XX
    AC_VOLTAGE_MAX = 0.78 * DC_VOLTAGE_MAX
    MOTOR_CURRENT_RATED_GAP = 1.0  # 5.07
    MOTOR_CURRENT_RATED_PHASE = 2.38  # 5.07
    MOTOR_CURRENT_RATED_FLEXPES = 2.38  #
    MOTOR_CURRENT_RATED_MAX_1401 = 1.5  # 11.32 or 1.75KC/3
    MOTOR_CURRENT_RATED_MAX_1402 = 2.7  # 11.32
    # MOTOR_CURRENT_LIMIT_MAX_1401 = 100 * 1.75 * KC_1401 / MOTOR_CURRENT_RATED_GAP
    # MOTOR_CURRENT_LIMIT_MAX_1402 = 100 * 1.75 * KC_1402 / MOTOR_CURRENT_RATED_PHASE
    MOTOR_CURRENT_LIMIT_MAX_1401 = 1.75 * KC_1401
    MOTOR_CURRENT_LIMIT_MAX_1402 = 1.75 * KC_1402
    # TORQUE_PROD_CURRENT_MAX_1401 = (
    #    1.75 * KC_1401
    # )  # MOTOR_CURRENT_LIMIT_MAX_1401  # 1.75KC
    # TORQUE_PROD_CURRENT_MAX_1402 = 1.75 * KC_1402  # MOTOR_CURRENT_LIMIT_MAX_1402
    TORQUE_PROD_CURRENT_MAX_1401 = (
        1.75 * KC_1401
    )  # For a 300.0% MOTOR_CURRENT_LIMIT_MAX_1402
    TORQUE_PROD_CURRENT_MAX_1402 = (
        1.75 * KC_1402
    )  # For a 300.0% MOTOR_CURRENT_LIMIT_MAX_1402
    USER_CURRENT_MAX_1401 = 3 * MOTOR_CURRENT_RATED_GAP  # 4.24
    USER_CURRENT_MAX_1402 = 3 * MOTOR_CURRENT_RATED_PHASE
    POWER_MAX_1401 = 1.732 * AC_VOLTAGE_MAX * DRIVE_CURRENT_MAX_1401
    POWER_MAX_1402 = 1.732 * AC_VOLTAGE_MAX * DRIVE_CURRENT_MAX_1402
    ct1401 = [
        KC_1401,
        DC_VOLTAGE_MAX,
        AC_VOLTAGE_MAX,
        DRIVE_CURRENT_MAX_1401,
        MOTOR_CURRENT_LIMIT_MAX_1401,
        MOTOR_CURRENT_RATED_MAX_1401,
        USER_CURRENT_MAX_1401,
        TORQUE_PROD_CURRENT_MAX_1401,
        POWER_MAX_1401,
    ]
    ct1402 = [
        KC_1402,
        DC_VOLTAGE_MAX,
        AC_VOLTAGE_MAX,
        DRIVE_CURRENT_MAX_1402,
        MOTOR_CURRENT_LIMIT_MAX_1402,
        MOTOR_CURRENT_RATED_MAX_1402,
        USER_CURRENT_MAX_1402,
        TORQUE_PROD_CURRENT_MAX_1402,
        POWER_MAX_1402,
    ]
    ctheaders = [
        "kc",
        "DCVmax",
        "ACVmax",
        "DrImax",
        "MotILimmax",
        "MotIratedmax",
        "UserImax",
        "TprodImax",
        "PowerMax",
    ]
    dtax_params = {}
    dtax_params["4.20"] = {
        "menu": 4,
        "register": 20,
        "dtype": "int16",
        "signed": True,
        "factor": 0.1,  # 65433 res 0.1A
        "scale": True,
        "desc": "+motor - regen, torque producing current as percentage of user current max bip % user current max",
        "default": 65433,
        "getter": "get_currentLoadPCMotRegen",
        "unit": "%",
    }

    dtax_params["4.20g"] = {
        "menu": 4,
        "register": 20,
        "dtype": "int16",
        "signed": True,
        "factor": 0.1 * USER_CURRENT_MAX_1401 * 0.01,  # 65433 res 0.1A
        "scale": True,
        "desc": "torque producing current as percentage of user current max bip % user current max",
        "default": 65433,
        "getter": "get_currentTorqueProducing",
        "unit": "A",
    }  # gap motors
    dtax_params["4.20p"] = {
        "menu": 4,
        "register": 20,
        "dtype": "int16",
        "signed": True,
        "factor": 0.1 * USER_CURRENT_MAX_1402 * 0.01,  # res 0.1A
        "scale": True,
        "desc": "torque producing current as percentage of user current max bip % user current max",
        "default": 65433,
        "getter": "get_currentTorqueProducing",
        "unit": "A",
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
        "units": "%",
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
        "units": "%",
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
        "units": "rpm",
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
        "factor": 0.01,  # not exactly sqrt2
        "scale": True,
        "desc": "Motor Kt torque constant, 0 to 500.00 NmA-1 (240 1.6)",
        "default": 240,  # 1.6 for p and 2.4 for g
        "getter": "get_kt",
        "unit": "Nm/A",
    }
    dtax_params["0.06g"] = {
        "menu": 0,
        "register": 6,
        "dtype": "int16",
        "signed": False,
        # "factor": (MOTOR_CURRENT_RATED_MAX_1401 * MOTOR_CURRENT_LIMIT_MAX_1401 * 0.01)
        # * 0.01
        # * 0.1,
        "factor": (MOTOR_CURRENT_LIMIT_MAX_1401 * 0.01 * 0.1),
        "scale": True,
        "desc": "Symmetrical current limit in % of CLM 0.1%",
        "default": 903.0,  # 3k for 13.545# 300.0
        "getter": "get_currentLimit",
        "units": "A",
    }
    dtax_params["0.06p"] = {
        "menu": 0,
        "register": 6,
        "dtype": "int16",  # "float",
        "signed": False,
        "factor": (MOTOR_CURRENT_LIMIT_MAX_1402 * 0.01 * 0.1),
        # "factor": (MOTOR_CURRENT_RATED_MAX_1402 * MOTOR_CURRENT_LIMIT_MAX_1402 * 0.01)
        # * 0.01
        # * 0.1,
        "scale": True,
        "desc": "Symmetrical current limit in % of CLM",
        "default": 900.3,  # 300.0
        "getter": "get_currentLimit",
        "units": "A",
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
        "units": "",
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
        "units": "1/rad",
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
        "units": "s",
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
        "desc": "Motor rated current % max is 11.32 par",
        "default": 6.42,  # 238 i16
        "getter": "get_currentRatedMotor",
        "unit": "A",
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
        "units": "",
    }
    dtax_params["1.39"] = {
        "menu": 1,
        "register": 39,
        "dtype": "int32",  #
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
        "factor": 1.0 * speedFactor,  # but could be 0.1 ??
        "scale": True,
        "desc": "Final speed reference speed_max_rpm",
        "default": 1,  # ?i16 65535, i32, f err
        "getter": "get_speedReference",
        "unit": "rpm",
    }
    dtax_params["3.27"] = {
        "menu": 3,
        "register": 27,
        "dtype": "float",  # 3.27 is a 32bpar but maybe int32 0.1
        "signed": True,
        "factor": 1.0 * speedFactor,  # but maybe0.1,  # ??
        "scale": True,
        "desc": "Driver encoder speed feedback, 40.0krpm",
        "default": 1,  # ?9.94e-32 as f works, others not
        "getter": "get_speedFeedback",
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
    dtax_params["3.04g"] = {
        "menu": 3,
        "register": 4,
        "dtype": "int16",  #
        "signed": True,
        "factor": (TORQUE_PROD_CURRENT_MAX_1401) * 0.01 * 0.1,
        # "factor": (MOTOR_CURRENT_RATED_MAX_1401 * TORQUE_PROD_CURRENT_MAX_1401 * 0.01)
        # * 0.01
        # * 0.1,
        "scale": True,
        "desc": "Speed controller output in Amps 0.1%, tDem, IDem",
        "default": 1,  # ? i16 65464 i32 0 f err
        "getter": "get_speedControllerOutput",
        "unit": "A",
    }
    dtax_params["3.04p"] = {
        "menu": 3,
        "register": 4,
        "dtype": "int16",  #
        "signed": True,
        "factor": (TORQUE_PROD_CURRENT_MAX_1402) * 0.01 * 0.1,
        # "factor": (MOTOR_CURRENT_RATED_MAX_1402 * TORQUE_PROD_CURRENT_MAX_1402 * 0.01)
        # * 0.01
        # * 0.1,
        "scale": True,
        "desc": "Speed controller output in Amps %, tDem, IDem",
        "default": 1,  # ?
        "getter": "get_speedControllerOutput",
        "unit": "A",
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
    dtax_params["4.24g"] = {
        "menu": 4,
        "register": 24,
        "dtype": "int16",  # 16b param
        "signed": False,
        # "factor": (MOTOR_CURRENT_RATED_MAX_1401 * TORQUE_PROD_CURRENT_MAX_1401 * 0.01)
        "factor": (TORQUE_PROD_CURRENT_MAX_1401) * 0.01 * 0.1,
        "scale": True,
        "desc": "Torque demand (after vl output) bip % Torque prod curr max (same as curr demand before a clamper)",
        "default": 0,  # f 9.18e-41, i32 err?
        "getter": "get_currentUserMax",
        "unit": "A",
    }
    dtax_params["4.24p"] = {
        "menu": 4,
        "register": 24,
        "dtype": "int16",  #
        "signed": False,
        "factor": (TORQUE_PROD_CURRENT_MAX_1402) * 0.01 * 0.1,
        # "factor": (MOTOR_CURRENT_RATED_MAX_1402 * TORQUE_PROD_CURRENT_MAX_1402 * 0.01)
        # * 0.01
        # * 0.1,
        "scale": True,  # ?? not clear if the 0.1 applies if so, 4.04/8 also
        "desc": "usercurrentmax bip % Torque prod curr max (same as curr demand before a clamper)",
        "default": 0,  # ?
        "getter": "get_currentUserMax",
        "unit": "A",
    }
    dtax_params["4.03g"] = {
        "menu": 4,
        "register": 3,
        "dtype": "int16",  # 16b param
        "signed": True,
        "factor": (TORQUE_PROD_CURRENT_MAX_1401) * 0.01 * 0.1,
        # "factor": (MOTOR_CURRENT_RATED_MAX_1401 * TORQUE_PROD_CURRENT_MAX_1401 * 0.01)
        # * 0.01
        # * 0.1,
        "scale": True,
        "desc": "Torque demand (after vl output) bip % Torque prod curr max (same as curr demand before a clamper)",
        "default": 0,  # f 9.18e-41, i32 err?
        "getter": "get_torqueDemand",
        "unit": "A",
    }
    dtax_params["4.03p"] = {
        "menu": 4,
        "register": 3,
        "dtype": "int16",  #
        "signed": True,
        "factor": (TORQUE_PROD_CURRENT_MAX_1402) * 0.01 * 0.1,
        # "factor": (MOTOR_CURRENT_RATED_MAX_1402 * TORQUE_PROD_CURRENT_MAX_1402 * 0.01)
        # * 0.01
        # * 0.1,
        "scale": True,  # ?? not clear if the 0.1 applies if so, 4.04/8 also
        "desc": "Torque demand (after vl output) bip % Torque prod curr max (same as curr demand before a clamper)",
        "default": 0,  # ?
        "getter": "get_torqueDemand",
        "unit": "A",
    }
    dtax_params["4.04g"] = {
        "menu": 4,
        "register": 4,
        "dtype": "int16",  #
        "signed": True,
        "factor": (TORQUE_PROD_CURRENT_MAX_1401) * 0.01 * 0.1,
        # "factor": (MOTOR_CURRENT_RATED_MAX_1401 * TORQUE_PROD_CURRENT_MAX_1401 * 0.01)
        # * 0.01
        # * 0.1,
        "scale": True,
        "desc": "Current demand % of torque prod current max 0.1",
        "default": 65514,  # i32 2 f 1.401e-45?
        "getter": "get_currentDemand",
        "unit": "A",
    }
    dtax_params["4.04p"] = {
        "menu": 4,
        "register": 4,
        "dtype": "int16",  #
        "signed": True,
        "factor": (TORQUE_PROD_CURRENT_MAX_1402) * 0.01 * 0.1,
        # "factor": (MOTOR_CURRENT_RATED_MAX_1401 * TORQUE_PROD_CURRENT_MAX_1401 * 0.01)
        # * 0.01
        # * 0.1,
        "scale": True,
        "desc": "Current demand 0.1",
        "default": 1,  # ?
        "getter": "get_currentDemand",
        "unit": "A",
    }
    dtax_params["4.08g"] = {
        "menu": 4,
        "register": 8,
        "dtype": "int16",  #
        "signed": True,
        "factor": USER_CURRENT_MAX_1401 * 0.01 * 0.01,  # * 0.1,  #
        "scale": True,
        "desc": "Torque reference % user current max 0.01",
        "default": 0,  # i32 err ?
        "getter": "get_torqueReference",
        "unit": "A",
    }
    dtax_params["4.08p"] = {
        "menu": 4,
        "register": 8,
        "dtype": "int16",  #
        "signed": True,
        "factor": USER_CURRENT_MAX_1402 * 0.01 * 0.01,  # 0.1,  #
        "scale": True,
        "desc": "Torque reference % user current max 0.01",
        "default": 1,  # ?
        "getter": "get_torqueReference",
        "unit": "A",
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

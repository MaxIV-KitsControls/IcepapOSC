"""Correction profiles for IcePAP OSC signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Sequence, Tuple

ScaleOffset = Tuple[float, float]
FactorsMap = Dict[str, ScaleOffset]
BuildInfo = Optional[Dict[str, object]]


@dataclass
class DeviceProfile:
    name: str
    states: Sequence[str]
    build_factors: Callable[
        [object, int, str, Optional[Sequence[ScaleOffset]], BuildInfo],
        Tuple[str, FactorsMap],
    ]


IPAP_ECTS_SOURCES = [
    "enctgtenc",
    "encshftenc",
    "encencin",
    "encabsenc",
    "encinpos",
    "encmeasure",
]
IPAP_STEP_SOURCES = [
    "postgtenc",
    "posshftenc",
    "posencin",
    "posabsenc",
    "posinpos",
    "posaxis",
    "posmeasure",
    "posmotor",
    "posctrlenc",
]
IPAP_STEPS_SOURCES = [
    "velmotor",
    "velcurrent",
    "difaxtgtenc",
    "difaxmotor",
    "difaxshftenc",
    "difaxctrlenc",
    "difaxmeasure",
    "difaxabsenc",
    "difaxencin",
    "difaxinpos",
]


def _build_ipap(
    icepap_system,
    addr,
    signal_name,
    manual: Optional[Sequence[ScaleOffset]],
    build_info: BuildInfo = None,
):
    # Build correction factors for a signal using IcePAP config + optional manual overrides.
    source = "units"
    anstep = None
    anturn = None
    absnstep = None
    absnturn = None
    einnstep = None
    einnturn = None
    inpnstep = None
    inpnturn = None
    tgtenc = None
    shftenc = None
    ctrlenc = None
    defvel = None
    try:
        cfg = icepap_system[addr].get_cfg()
        anstep = cfg.get("ANSTEP")
        anturn = cfg.get("ANTURN")
        absnstep = cfg.get("ABSNSTEP")
        absnturn = cfg.get("ABSNTURN")
        einnstep = cfg.get("EINNSTEP")
        einnturn = cfg.get("EINNTURN")
        inpnstep = cfg.get("INPNSTEP")
        inpnturn = cfg.get("INPNTURN")
        tgtenc = cfg.get("TGTENC")
        shftenc = cfg.get("SHFTENC")
        ctrlenc = cfg.get("CTRLENC")
        defvel = float(cfg.get("DEFVEL"))
    except Exception as e:
        print(e)
        pass
    sign = 1.0
    step_per_unit = 1.0
    offset = 0.0
    offsete = 0.0  # If manual corr factors ects can have a different offset than steps
    esff = 1.0
    step_per_mt = 400.0
    if anstep and anturn:
        try:
            step_per_mt = float(anstep) / float(anturn)
        except Exception:
            pass

    if manual:
        # Manual factors override computed conversion (pos, enc).
        pos = manual[0] if len(manual) > 0 else (1.0, 0.0)
        enc = manual[1] if len(manual) > 1 else (1.0, 0.0)
        step_per_unit = 1.0 / float(pos[0]) if pos[0] else 1.0
        offset = float(pos[1])
        # At the moment enc offset is ignored to keep parity with taurus usage.
        esff = float(enc[0]) if enc[0] else 1.0
        offsete = float(enc[1])
        if step_per_unit < 0:
            step_per_unit = -1 * step_per_unit
            esff = -1 * esff
            sign = -1

    attr = (signal_name or "").lower()
    tgtenc_u = str(tgtenc).upper() if tgtenc is not None else None
    shftenc_u = str(shftenc).upper() if shftenc is not None else None
    ctrlenc_u = str(ctrlenc).upper() if ctrlenc is not None else None
    # Determine which encoder is used as "measure" based on config.
    if tgtenc_u and tgtenc_u != "NONE":
        measureenc_u = tgtenc_u
    elif shftenc_u and shftenc_u != "NONE":
        measureenc_u = shftenc_u
    else:
        measureenc_u = "POSAXIS"
    # Validate configured encoders when required by the signal type.
    if attr in ("enctgtenc", "postgtenc"):
        if tgtenc_u == "NONE":
            raise ValueError(
                "TGTENC is NONE; target encoder signals are not available."
            )
    if attr in ("encshftenc", "posshftenc"):
        if shftenc_u == "NONE":
            raise ValueError(
                "SHFTENC is NONE; shaft encoder signals are not available."
            )
    if attr in ("encctrlenc", "posctrlenc"):
        if ctrlenc_u == "NONE":
            raise ValueError("CTRLENC is NONE; ctrl encoder signals are not available.")
    ratio_abs = None
    ratio_ein = None
    ratio_inp = None
    if anstep and anturn:
        try:
            motor_steps_per_turn = float(anstep) / float(anturn)
            if absnstep and absnturn:
                ratio_abs = (float(absnstep) / float(absnturn)) / motor_steps_per_turn
            if einnstep and einnturn:
                ratio_ein = (float(einnstep) / float(einnturn)) / motor_steps_per_turn
            if inpnstep and inpnturn:
                ratio_inp = (float(inpnstep) / float(inpnturn)) / motor_steps_per_turn
        except Exception:
            ratio_abs = None
            ratio_ein = None
            ratio_inp = None

    # Map encoder name to ratio relative to motor steps.
    def _ratio_for_encoder(enc_name):
        enc_name = (enc_name or "").upper()
        if enc_name == "ABSENC":
            return ratio_abs
        if enc_name == "ENCIN":
            return ratio_ein
        if enc_name == "INPOS":
            return ratio_inp
        return None

    # Compute ECTS ratio per signal from encoder config.
    def _ects_ratio_for_signal(name):
        name = (name or "").lower()
        if name in ("enctgtenc", "postgtenc"):
            return _ratio_for_encoder(tgtenc_u)
        if name in ("encshftenc", "posshftenc"):
            return _ratio_for_encoder(shftenc_u)
        if name in ("encctrlenc", "posctrlenc"):
            return _ratio_for_encoder(ctrlenc_u)
        if name in ("encmeasure", "posmeasure"):
            return _ratio_for_encoder(measureenc_u)
        if name in ("encabsenc", "posabsenc"):
            return ratio_abs
        if name in ("encencin", "posencin"):
            return ratio_ein
        if name in ("encinpos", "posinpos"):
            return ratio_inp
        if name in ("encaxis", "posaxis"):
            return _ratio_for_encoder(measureenc_u)
        return None

    # Compute steps ratio for signals that map from ECTS.
    def _steps_ratio_for_signal(name):
        _ects_ratio = _ects_ratio_for_signal(name)
        if _ects_ratio:
            return 1.0 / _ects_ratio
        else:
            return None

    # print("_build_ipap:", attr)
    # print("_build_ipap:", sign, step_per_unit, offset, esff, step_per_mt)
    # print("_build_ipap:", manual)
    # print("_build_ipap:", tgtenc_u, shftenc_u, measureenc_u)
    if measureenc_u == "POSAXIS":
        print(
            "_build_ipap:",
            addr,
            attr,
            " no virtual encoder assigned, using trace corrections to convert to ects",
        )
    # Build factors for "measure" signals based on virtual encoder configuration.
    if attr in ("posmeasure", "encmeasure"):
        if measureenc_u == "POSAXIS":
            source = "steps"
            ects_ratio = _ects_ratio_for_signal(attr)
            if ects_ratio is None:
                ects_ratio = (
                    1.0 / esff / step_per_unit if step_per_unit and esff else 1.0
                )
            factors = {
                "units": (sign / step_per_unit, offset),
                "steps": (1.0, 0.0),
                "ects": (ects_ratio, 0.0),
                "mt": (1.0 / step_per_mt, 0.0),
            }
        elif attr == "posmeasure":
            source = "steps"
            # If no virtual encoder assigned, no meaningful conversion to ects
            # But sometimes we disconfigure the virtuals, keeping esff
            ects_ratio = _ects_ratio_for_signal(attr)
            if ects_ratio is None:
                ects_ratio = (
                    1.0 / step_per_unit / esff if step_per_unit and esff else 1.0
                )
            factors = {
                "units": (sign / step_per_unit, offset),
                "steps": (1.0, 0.0),
                "ects": (ects_ratio, 0.0),
                "mt": (1.0 / step_per_mt, 0.0),
            }
        else:
            source = "ects"
            steps_ratio = _steps_ratio_for_signal(attr)
            if steps_ratio is None:
                steps_ratio = step_per_unit * esff
            factors = {
                "units": (sign * esff, offsete),
                "steps": (steps_ratio, 0.0),
                "ects": (1.0, 0.0),
                "mt": (steps_ratio / step_per_mt, 0.0),
            }
    elif attr in ("posaxis", "encaxis"):
        source = "steps"
        # If no virtual encoder assigned, no meaningful conversion to ects
        # But sometimes we disconfigure the virtuals, keeping esff
        # Warning message is hopefully enough
        # ects_ratio = _ects_ratio_for_signal(attr)
        ects_ratio = _ects_ratio_for_signal(attr)
        if ects_ratio is None:
            ects_ratio = 1.0 / esff / step_per_unit if step_per_unit and esff else 1.0
        factors = {
            "units": (sign / step_per_unit, offset),
            "steps": (1.0, 0.0),
            "ects": (ects_ratio, 0.0),
            "mt": (1.0 / step_per_mt, 0.0),
        }
    # Build factors for encoder signals.
    elif attr in IPAP_ECTS_SOURCES:
        source = "ects"
        steps_ratio = _steps_ratio_for_signal(attr)
        if steps_ratio is None:
            steps_ratio = step_per_unit * esff
        factors = {
            "units": (sign * esff, offsete),
            "steps": (steps_ratio, 0.0),
            "ects": (1.0, 0.0),
            "mt": (steps_ratio / step_per_mt, 0.0),
        }
    # Build factors for position signals (units/steps/ects/mt).
    elif attr in IPAP_STEP_SOURCES:
        source = "steps"
        ects_ratio = _ects_ratio_for_signal(attr)
        if ects_ratio is None:
            ects_ratio = 1.0 / esff / step_per_unit if step_per_unit and esff else 1.0
        factors = {
            "units": (sign / step_per_unit, offset),
            "steps": (1.0, 0.0),
            "ects": (ects_ratio, 0.0),
            "mt": (1.0 / step_per_mt, 0.0),
        }
    # Build factors for velocity/delta signals (steps/ects/mt).
    elif attr in IPAP_STEPS_SOURCES:
        source = "steps"
        ects_ratio = _ects_ratio_for_signal(attr)
        if ects_ratio is None:
            ects_ratio = 1.0 / esff / step_per_unit if step_per_unit and esff else 1.0
        factors = {
            "units": (sign / step_per_unit, 0.0),
            "steps": (1.0, 0.0),
            "ects": (ects_ratio, 0.0),
            "mt": (1.0 / step_per_mt, 0.0),
        }
        if attr.lower() in ["velmotor", "velcurrent"]:
            factors["vr"] = (1.0 / defvel, 0.0)
    else:
        source = "units"
        factors = {"units": (1.0, 0.0)}
    return source, factors


def _ipap_build(
    icepap_system,
    addr,
    signal_name,
    manual: Optional[Sequence[ScaleOffset]],
    build_info: BuildInfo = None,
):
    return _build_ipap(icepap_system, addr, signal_name, manual, build_info)


def _dtax_group(addr, build_info: Dict[str, object]) -> str:
    not_flexpes = bool(build_info.get("not_flexpes", True))
    if not_flexpes:
        try:
            addr_i = int(addr)
        except Exception:
            addr_i = 0
        gap_max = int(build_info.get("gap_max_addr", 4))
        return "gap" if addr_i <= gap_max else "phase"
    return "flexpes"


def _dtax_mm_per_step(build_info: Dict[str, object], group: str) -> Optional[float]:
    val = build_info.get(f"position_mm_per_step_{group}")
    try:
        return float(val)
    except Exception:
        return None


def _dtax_mm_per_rev(build_info: Dict[str, object], group: str) -> Optional[float]:
    val = build_info.get(f"position_mm_per_rev_{group}")
    try:
        return float(val)
    except Exception:
        return None


def _build_dtax(
    icepap_system,
    addr,
    signal_name,
    manual: Optional[Sequence[ScaleOffset]],
    build_info: BuildInfo = None,
):
    info = build_info or {}
    name = (signal_name or "").lower()
    if (
        name in IPAP_ECTS_SOURCES
        or name in IPAP_STEP_SOURCES
        or name in IPAP_STEPS_SOURCES
        or name
        in (
            "posaxis",
            "encaxis",
            "posmeasure",
            "encmeasure",
        )
    ):
        return _build_ipap(icepap_system, addr, signal_name, manual, build_info)
    factors = {"units": (1.0, 0.0)}

    if name.startswith("position"):
        group = _dtax_group(addr, info)
        mm_per_step = _dtax_mm_per_step(info, group)
        mm_per_rev = _dtax_mm_per_rev(info, group)
        steps_per_mm = 1.0 / mm_per_step if mm_per_step else None
        steps_per_rev = (
            (mm_per_rev / mm_per_step) if mm_per_rev and mm_per_step else None
        )
        #Digitax position is spread across 3 registers, fine (1/2**16) steps, steps and revolutions
        if "rev" in name.lower():
            source = "mt"
            factors["mt"] = (1.0, 0.0)
            if mm_per_rev:
                factors["mm"] = (mm_per_rev, 0.0)
                factors["units"] = (mm_per_rev, 0.0)
            if steps_per_rev:
                factors["steps"] = (steps_per_rev, 0.0)
        elif "fine" in name.lower():
            source = "steps"
            factors["steps"] = (1.0/(2**16), 0.0)
            if mm_per_step:
                factors["mm"] = (mm_per_step/(2**16), 0.0)
                factors["units"] = (mm_per_step/(2**16), 0.0)
            if steps_per_rev:
                factors["mt"] = (1.0 / ((2**16)*steps_per_rev), 0.0)
        else:
            source = "mt"
            factors["steps"] = (1.0, 0.0)
            if mm_per_step:
                factors["mm"] = (mm_per_step, 0.0)
                factors["units"] = (mm_per_step, 0.0)
            if steps_per_rev:
                factors["mt"] = (1.0 / steps_per_rev, 0.0)

    elif name.startswith("speed"):
        group = _dtax_group(addr, info)
        mm_per_step = _dtax_mm_per_step(info, group)
        mm_per_rev = _dtax_mm_per_rev(info, group)
        steps_per_mm = 1.0 / mm_per_step if mm_per_step else None
        steps_per_rev = (
            (mm_per_rev / mm_per_step) if mm_per_rev and mm_per_step else None
        )

        factors["mt"] = (1.0, 0.0)
        source = "mt"
        if mm_per_rev:
            factors["mm"] = (mm_per_rev, 0.0)
            factors["units"] = (mm_per_rev, 0.0)
        if steps_per_rev:
            factors["steps"] = (steps_per_rev, 0.0)
    return source, factors


# Default correction profile for IcePAP signals.
IPAP_PROFILE = DeviceProfile(
    name="ipap_motor",
    states=["units", "steps", "ects", "mt"],
    build_factors=_build_ipap,
)

# Correction profile for Digitax (DTAX) signals.
DTAX_PROFILE = DeviceProfile(
    name="dtax_motor",
    states=["units", "steps", "mm", "mt"],
    build_factors=_build_dtax,
)

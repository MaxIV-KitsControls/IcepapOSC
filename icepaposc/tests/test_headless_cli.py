from types import SimpleNamespace

import pytest

from icepaposc import __main__ as main_mod
from icepaposc.window_main import SIGNAL_SETS


@pytest.fixture
def dummy_runner(monkeypatch):
    # Capture parameters passed to HeadlessRunner without doing real work.
    captured = {}

    class DummyRunner:
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
            captured["signals"] = signals
            captured["output_file"] = output_file

        def run(self, acquisition_time):
            captured["acquisition_time"] = acquisition_time

    # Replace the real runner with the dummy in the CLI module.
    monkeypatch.setattr(main_mod, "HeadlessRunner", DummyRunner)
    return captured


def _base_args(**overrides):
    # Build a SimpleNamespace matching the CLI args object.
    base = dict(
        host="localhost",
        port=5000,
        timeout=3,
        sig=[],
        sigset="",
        preset="",
        axis=1,
        corr="",
        headless=True,
        acquisition_time=5,
        output_file="out.csv",
        dump_rate=1,
        sample_rate=1,
        list_signals=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_run_headless_with_sig_list(dummy_runner):
    # CLI mode with explicit --sig list should parse into signal tuples.
    args = _base_args(sig=["2:PosAxis:1"])
    main_mod._run_headless(args)
    assert dummy_runner["signals"] == [(2, "PosAxis", 1)]
    assert dummy_runner["acquisition_time"] == 5


def test_run_headless_with_sigset(tmp_path, dummy_runner):
    # CLI mode with --sigset should load the list file and map to tuples.
    sigset_file = tmp_path / "signals.lst"
    sigset_file.write_text("PosAxis 3 0xff0000 0\n")
    args = _base_args(sigset=str(sigset_file), axis=7)
    main_mod._run_headless(args)
    assert dummy_runner["signals"] == [(7, "PosAxis", 3)]


def test_run_headless_with_preset(dummy_runner):
    # CLI mode with --preset should expand the built-in preset map.
    preset_name = next(iter(SIGNAL_SETS.keys()))
    args = _base_args(preset=preset_name, axis=5)
    main_mod._run_headless(args)
    expected = [(5, sig[0], sig[1]) for sig in SIGNAL_SETS[preset_name]["signals"]]
    assert dummy_runner["signals"] == expected

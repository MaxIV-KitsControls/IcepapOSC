#!/usr/bin/env python3
"""Sequential manual test runner for `icepaposc`.

Each scenario launches the CLI with a different combination of options and
waits for the user to close the GUI window before continuing. Use this helper
for quick, repeatable checks of plotting, CSV tools, correction factors, and
signal set import.

Adjust the vars repo_root and sigseth_path to where the test files are located
Choose a driver configured if possible with Absenc, otherwise adjust the variable signals_driver
in this script

Examples:

python run_icepaposc_manual.py --host w-kitslab-icepap-21 --driver 1
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def build_scenarios(
    host: str | None,
    port: int,
    timeout: int,
    driver: int,
    driver2: int | None,
    icepaposc_cmd: str,
) -> List[Dict[str, Any]]:
    """Return the list of scenarios to execute."""
    host_arg = host or "<host>"
    base_cmd = [
        icepaposc_cmd,
        host_arg,
        "--port",
        str(port),
        "--timeout",
        str(timeout),
    ]

    repo_root = Path(__file__).resolve().parents[1]
    sigset_path = (repo_root / "python"/"icepaposc" / "manual_test" / "SignalSet.lst").resolve()
    #sigset_path = (repo_root / "icepaposc" / "tests" / "SignalSet.lst").resolve()
    csv_fft = (
        repo_root / "python"/"icepaposc" / "manual_test" / "csv_fft_sines.csv"
        #repo_root / "python"/"icepaposc" / "manual_test" / "csv_fft_sines.csv"
    ).resolve()
    csv_der = (
        repo_root / "python"/"icepaposc" / "manual_test" / "csv_derivative_shapes.csv"
        #repo_root / "icepaposc" / "tests" / "csv_derivative_shapes.csv"
    ).resolve()

    signals_driver = [
        f"{driver}:PosAxis:1",
        f"{driver}:EncMeasure:2",
        f"{driver}:EncTgtenc:3",
        f"{driver}:EncAbsenc:4",
    ]

    scenarios: List[Dict[str, Any]] = [
        {
            "name": "List available signals and presets",
            "description": (
                "Runs with --list-signals to show the collector signals and predefined sets. "
                "This should exit immediately without opening a GUI."
            ),
            "cmd": [icepaposc_cmd, "--list-signals"],
        },
        {
            "name": "Basic live signals (single driver)",
            "description": (
                "Launches a live plot using explicit signal definitions with Y axes. "
                "Close the window after confirming curves update and axes look correct."
                "Check ctrl+H to see the different hotkeys, you can test all of them in this scenario"
            ),
            "cmd": base_cmd + ["--axis", str(driver), "-s", *signals_driver],
            "requires_host": True,
        },
        {
            "name": "Selected driver differs from signal driver",
            "description": (
                "Uses --axis to preselect a different driver in the UI while plotting signals "
                "from the default driver. Verify the driver selection changes but curves remain."
            ),
            "cmd": base_cmd + ["--axis", str(driver2 or driver), "-s", *signals_driver],
            "requires_host": True,
            "requires_driver2": True,
        },
        {
            "name": "Import signal set file",
            "description": (
                "Loads the predefined SignalSet.lst. Verify background and signal list, then "
                "test toggling Ctrl+T/Ctrl+Y and moving curves."
            ),
            "cmd": base_cmd + ["--sigset", str(sigset_path)],
            "requires_host": True,
        },
        {
            "name": "Manual correction factors override",
            "description": (
                "Uses --corr and a few live signals. Toggle Ctrl+U and confirm "
                "that the status line at the bottom of the window changes between "
                "the different states OFF/UNITS/STEPS/ECTS/MT "
                "Units from pos signals are steps*0.1 and for enc signals *0.01"
            ),
            "cmd": base_cmd
            + [
                "--corr",
                "0.1,1,0.01,1",
                "-s",
                *signals_driver,
            ],
            "requires_host": True,
        },
        {
            "name": "Sample/dump rate adjustments",
            "description": (
                "Uses slower sample/dump rates. Verify the update cadence and autosave "
                "behaviour after enabling autosave in Settings."
            ),
            "cmd": base_cmd
            + [
                "--sigset",
                str(sigset_path),
                "--sample_rate",
                "100",
                "--dump_rate",
                "10",
            ],
            "requires_host": True,
        },
        {
            "name": "CSV load (FFT fixture)",
            "description": (
                "Loads csv_fft_sines.csv via --csv-open. Exercise Ctrl+Y (Y autorange) and "
                "open FFT (Ctrl+F). Save FFT via Ctrl+O inside the FFT window."
            ),
            "cmd": [
                icepaposc_cmd,
                "--csv-open",
                str(csv_fft),
                "-y",
                "Y1,Y2,Y3",
            ],
        },
        {
            "name": "CSV list columns (no GUI)",
            "description": "Uses --csv-lst to print available signal indices and exit.",
            "cmd": [icepaposc_cmd, "--csv-lst", str(csv_fft)],
        },
        {
            "name": "CSV load with column subset",
            "description": "Loads only the first signal pair via --csv-cols=1.",
            "cmd": [
                icepaposc_cmd,
                "--csv-open",
                str(csv_fft),
                "--csv-cols",
                "1",
            ],
        },
        {
            "name": "CSV load (Derivative fixture)",
            "description": (
                "Loads csv_derivative_shapes.csv via --csv-open. Exercise Ctrl+D "
                "(Derivative tool) and save via Ctrl+O inside the derivative window."
            ),
            "cmd": [
                icepaposc_cmd,
                "--csv-open",
                str(csv_der),
                "-yy",
            ],
        },
    ]

    for sc in scenarios:
        sc.setdefault("requires_host", False)
        sc.setdefault("requires_driver2", False)

    return scenarios


def run_scenario(idx: int, total: int, scenario: Dict[str, Any]) -> int:
    """Execute one scenario, returning the subprocess return code."""
    print(f"\n[{idx}/{total}] {scenario['name']}")
    print(
        f"{scenario['description']}\n\nCommand: {' '.join(shlex.quote(a) for a in scenario['cmd'])}"
    )
    try:
        input("\nPress Enter to launch (Ctrl+C to abort)... ")
    except KeyboardInterrupt:
        print("\nAborted by user before launch.")
        return 130

    try:
        result = subprocess.run(scenario["cmd"], check=False)
    except KeyboardInterrupt:
        print("\nScenario interrupted by user.")
        return 130

    if result.returncode == 0:
        print("✔ Scenario completed (window closed).")
    else:
        print(f"✖ Scenario exited with code {result.returncode}.")
    return result.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host",
        default=None,
        help=(
            "IcePAP host to use for live scenarios. If omitted, the script will prompt "
            "interactively (or skip live tests if stdin is not a TTY)."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="IcePAP port (default: 5000).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3,
        help="Socket timeout in seconds (default: 3).",
    )
    parser.add_argument(
        "--driver",
        type=int,
        default=1,
        help="Driver ID to use in signal definitions (default: 1).",
    )
    parser.add_argument(
        "--driver2",
        type=int,
        default=None,
        help="Optional second driver ID to preselect in the UI for one scenario.",
    )
    parser.add_argument(
        "--no-live",
        action="store_true",
        help="Skip scenarios that require a live IcePAP host connection.",
    )
    parser.add_argument(
        "--icepaposc-cmd",
        default="icepaposc",
        help='Command used to invoke icepaposc (default: "icepaposc").',
    )
    parser.add_argument(
        "tests",
        nargs="*",
        help=(
            "Optional list of scenario numbers to run (e.g. '1 3 5'). "
            "Use '?' to list all scenarios with descriptions."
        ),
    )
    parser.add_argument(
        "-l",
        "--list-tests",
        action="store_true",
        help="List available scenarios and exit (same as passing '?').",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tests = args.tests or []
    request_listing = args.list_tests or any(token == "?" for token in tests)

    icepaposc_path = shutil.which(args.icepaposc_cmd)
    if not icepaposc_path:
        if request_listing:
            icepaposc_path = args.icepaposc_cmd
        else:
            print(f"Error: '{args.icepaposc_cmd}' not found in PATH.", file=sys.stderr)
            return 127

    host = args.host or os.environ.get("ICEPAPOSC_TEST_HOST")
    if args.no_live:
        host = None

    if request_listing:
        has_host = host is not None
        has_driver2 = args.driver2 is not None
        scenarios = build_scenarios(
            host or "<host>",
            args.port,
            args.timeout,
            args.driver,
            args.driver2,
            icepaposc_path,
        )
        print("Available manual scenarios:\n")
        for idx, sc in enumerate(scenarios, 1):
            print(f"{idx:2d}. {sc['name']}\n    {sc['description']}\n")
            if sc.get("requires_host") and not has_host:
                print("    [Requires --host to run]\n")
            elif sc.get("requires_driver2") and not has_driver2:
                print("    [Requires --driver2 to run]\n")
            else:
                print()
        if len(tests) > 1:
            print("(Ignored additional scenario indices after '?'.)")
        return 0

    if host is None and sys.stdin.isatty():
        try:
            prompt = (
                "Enter the IcePAP host to use for live tests (leave blank to skip): "
            )
            response = input(prompt).strip()
            host = response or None
        except KeyboardInterrupt:
            print("\nAborted while waiting for host input.")
            return 130

    all_scenarios = build_scenarios(
        host,
        args.port,
        args.timeout,
        args.driver,
        args.driver2,
        icepaposc_path,
    )

    selected_scenarios = list(all_scenarios)
    total = len(all_scenarios)

    if tests:
        selections = []
        for token in tests:
            try:
                idx = int(token)
                if idx < 1 or idx > total:
                    raise ValueError
                selections.append(idx)
            except ValueError:
                print(f"Invalid scenario index: {token}", file=sys.stderr)
                return 2
        selected_scenarios = [all_scenarios[i - 1] for i in selections]

    missing_required = [
        sc for sc in selected_scenarios if sc.get("requires_host") and host is None
    ]
    if missing_required:
        if tests:
            names = ", ".join(sc["name"] for sc in missing_required)
            print(
                f"Scenario(s) require --host to run: {names}",
                file=sys.stderr,
            )
            return 2
        else:
            print("Skipping live scenarios (pass --host to include them).")

    scenarios = [
        sc
        for sc in selected_scenarios
        if host is not None or not sc.get("requires_host")
    ]
    scenarios = [
        sc
        for sc in scenarios
        if args.driver2 is not None or not sc.get("requires_driver2")
    ]

    if not scenarios:
        print("No runnable scenarios (check --host setting).", file=sys.stderr)
        return 1

    print(
        f"Running {len(scenarios)} manual scenario(s). Close each window to continue."
    )
    overall_rc = 0
    for idx, scenario in enumerate(scenarios, 1):
        rc = run_scenario(idx, len(scenarios), scenario)
        if rc not in (0, 130):
            overall_rc = rc
        if rc == 130:
            overall_rc = rc
            break

    print("\nAll requested scenarios processed.")
    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())

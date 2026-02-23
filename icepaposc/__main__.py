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

import sys
import argparse

from PyQt5.QtWidgets import QApplication

from . import version
from .window_main import WindowMain, SIGNAL_SETS
from .settings import Settings
from .headless import HeadlessRunner, HeadlessBatchRunner, BATCH_SIGNAL_GETTER_MAP
from .utils import parse_signal_definition, load_signal_set_file
from .collector import AVAILABLE_SIGNALS
from .csvloader import load_csv_items, inspect_csv_columns


def get_parser():
    desc = "IcePAP Oscilloscope Application, base on ethernet communication\n"
    desc += "Version: {}.\n".format(version)
    desc += "\n"
    desc += "Hotkeys:\n"
    desc += "Ctrl+O: Save VISIBLE contents to csv format file\n"
    desc += "Ctrl+Shift+O: Save raw + corrected states (OFF only)\n"
    desc += "Ctrl+U: Cycle correction state (OFF -> units -> steps -> ects -> mt)\n"
    desc += "Ctrl+I: Input dialog for csv file name\n"
    desc += "Ctrl+Y: Enable autorange on Ys\n"
    desc += "Ctrl+R: Zoom IN time axis\n"
    desc += "Ctrl+E: Zoom OUT time axis\n"
    desc += "Ctrl+Left Click: Snap min time border to cursor\n"
    desc += "Ctrl+T: Toggle autorange X/autopan X\n"
    desc += "Ctrl+F: FFT selector\n"
    desc += "Ctrl+Shift+F: Refresh FFT\n"
    desc += "Ctrl+D: Derivative selector\n"
    desc += "Ctrl+Shift+D: Refresh derivative\n"
    desc += "Ctrl+H: Toggle hotkey help overlay\n"
    desc += "Ctrl+Shift+H: Toggle correction debug overlay\n"
    desc += "\n"
    desc += "Import/export format:\n"
    desc += "Signal yaxis(1-6) color driver_addr lsb_line_style_msbs_linemarker 1blackbackground(optional)\n"
    desc += "PosAxis 1 0xff0000 5 5 (style 4 marker 1 see UI buttons order) 1 (enable black bakg)\n"
    desc += "\n"
    desc += "\nExamples usage with UI:\n"
    desc += "  \nicepaposc <host> -s 1:PosAxis:1 2:PosAxis:2 "
    desc += "  icepaposc <host> --axis 1 --sigset aa.lst"
    desc += "\nExample headless usage:\n"
    desc += "  icepaposc <host> --headless --preset Closed_loop_plot "
    desc += "--axis 5 --acquisition-time 10 --output-file capture.csv\n"
    desc += '  icepaposc <host> --headless -s "1:PosAxis:1" "2:PosAxis:1" '
    desc += "--axis 5 --acquisition-time 10 --output-file capture.csv\n"
    epi = "Documentation: https://alba-synchrotron.github.io/pyIcePAP-doc/\n"
    epi += (
        "Copyright 2017:\n"
        "   MAX IV Laboratory, Lund, Sweden\n"
        "   CELLS / ALBA Synchrotron, Bellaterra, Spain."
    )
    fmt = argparse.RawTextHelpFormatter
    parse = argparse.ArgumentParser(description=desc, formatter_class=fmt, epilog=epi)
    ver = "%(prog)s {0}".format(version)

    parse.add_argument("--version", action="version", version=ver)

    parse.add_argument(
        "host",
        nargs="?",
        default="localhost",
        help="IcePAP host (required for GUI/headless capture; optional for --list-signals)",
    )
    parse.add_argument("--axis", help="Selected axis / driver id", default=1, type=int)
    parse.add_argument("-p", "--port", type=int, default=5000, help="IcePAP port")
    parse.add_argument("-t", "--timeout", type=int, default=3, help="Socket timeout")
    parse.add_argument(
        "--sigset", default="", help=".lst filename to import signals from"
    )
    parse.add_argument(
        "--corr",
        default="",
        help="Default curves correction factors" "--corr='pa,pb,ea,eb'",
    )
    # This feature does not make sense in the current implementation state 251029
    # parse.add_argument(
    #     "--yrange",
    #     default="",
    #     help="Default yaxes with skipped autorange when "
    #     "tiled yview --yrange='1,3,5'",
    # )
    parse.add_argument(
        "-dr",
        "--dump_rate",
        type=int,
        default=10,
        help="Number of samples acquired before update ui",
    )
    parse.add_argument(
        "-sr",
        "--sample_rate",
        type=int,
        default=10,
        help="Number of ms between samples (best effort)",
    )
    parse.add_argument(
        "-s",
        "--sig",
        nargs="*",
        default=[],
        help="Preselected signals (<driver>:<signal name>:<Y-axis>)",
    )
    parse.add_argument(
        "--headless",
        action="store_true",
        help="Run acquisition headlessly and save to CSV",
    )
    parse.add_argument(
        "--headless-ma",
        action="store_true",
        help="Run acquisition headlessly in multi-signal batch mode (exclusive)",
    )
    parse.add_argument(
        "--acquisition-time",
        type=float,
        default=0.0,
        help="Acquisition time (seconds) for headless mode",
    )
    parse.add_argument(
        "--output-file",
        default="",
        help="CSV output filename for headless mode (required when --headless or --headless-ma)",
    )
    parse.add_argument(
        "--list-signals",
        action="store_true",
        help="List available collector signals and predefined sets and exit",
    )
    parse.add_argument(
        "--csv-open",
        default="",
        help="CSV mode only. If no --csv-cols, all signals are taken.\nLoad curves from CSV instead of live acquisition",
    )
    parse.add_argument(
        "--csv-cols",
        default="",
        help="CSV mode only. Requires --csv-open. Comma-separated 1-based signal indices (time/value pairs).\nUse --csv-lst before to get the csv col/signal matching. Default: all",
    )
    parse.add_argument(
        "--csv-lst",
        default="",
        help="CSV mode only. Requires --csv-open. List signals from CSV (index + time/value pairs) and exit",
    )
    parse.add_argument(
        "-y",
        "--signal-yaxes",
        default="",
        help=(
            "CSV mode only. Requires --csv-open and --csv-cols. Define which axes the signals are to be plotted in. "
            "Comma-separated 'YN' (example: -y=Y2,Y4,Y1). "
            "Use -yy for sequential y axis assignment."
        ),
    )
    parse.add_argument(
        "-yy",
        "--signal-yaxes-seq",
        action="store_true",
        help="CSV mode only. Requires --csv-open and --csv-cols. Assign signals sequentially to different Y axes",
    )
    parse.add_argument(
        "--preset",
        default="",
        help="Name of predefined signal set to use in the signal acquisition (headless mode only)",
    )

    # TODO: Allow to pass the axes preselected and type of graph
    # parse.add_argument('-a', nargs='*', help='Axes to save, default all',
    #                    type=int, default=[])
    # save_cmd.add_argument('-d', '--debug', action='store_true',
    #                       help='Activate log level DEBUG')

    return parse


def _run_headless(args):
    if not args.output_file:
        raise SystemExit("Headless mode requires --output-file")
    if args.acquisition_time <= 0:
        raise SystemExit("Headless mode requires --acquisition-time > 0")

    signals = []
    if args.sig:
        for sig in args.sig:
            try:
                signals.append(parse_signal_definition(sig))
            except ValueError as exc:
                raise SystemExit(str(exc))
    if args.sigset:
        signal_defs, _ = load_signal_set_file(args.sigset)
        for entry in signal_defs:
            signals.append((args.axis, entry["signal_name"], entry["axis"]))
    if args.preset:
        preset = SIGNAL_SETS.get(args.preset)
        if not preset:
            raise SystemExit(f"Unknown preset '{args.preset}'")
        for sig_def in preset["signals"]:
            signals.append((args.axis, sig_def[0], sig_def[1]))
    if not signals:
        raise SystemExit("Headless mode requires --sig, --sigset, or --preset")

    settings = Settings()
    settings.dump_rate = args.dump_rate
    settings.sample_rate = args.sample_rate

    corr_factors = None
    if args.corr and args.corr.count(",") == 3:
        corr_values = [float(value) for value in args.corr.split(",")]
        if len(corr_values) == 4:
            corr_factors = corr_values

    runner = HeadlessRunner(
        settings,
        args.host,
        args.port,
        args.timeout,
        signals,
        args.output_file,
        corr_factors=corr_factors,
    )
    runner.run(args.acquisition_time)


def _run_headless_ma(args):
    if not args.output_file:
        raise SystemExit("Headless mode requires --output-file")
    if args.acquisition_time <= 0:
        raise SystemExit("Headless mode requires --acquisition-time > 0")
    signals = []
    if args.sig:
        for sig in args.sig:
            try:
                signals.append(parse_signal_definition(sig))
            except ValueError as exc:
                raise SystemExit(str(exc))
    if args.sigset:
        signal_defs, _ = load_signal_set_file(args.sigset)
        for entry in signal_defs:
            signals.append((args.axis, entry["signal_name"], entry["axis"]))
    if args.preset:
        preset = SIGNAL_SETS.get(args.preset)
        if preset is None:
            raise SystemExit(f"Unknown preset: {args.preset}")
        for sig_def in preset["signals"]:
            signals.append((args.axis, sig_def[0], sig_def[1]))
    if not signals:
        raise SystemExit("No signals defined for headless batch acquisition")

    settings = Settings()
    settings.dump_rate = args.dump_rate
    settings.sample_rate = args.sample_rate
    corr_factors = None
    if args.corr and args.corr.count(",") == 3:
        corr_values = [float(value) for value in args.corr.split(",")]
        if len(corr_values) == 4:
            corr_factors = corr_values
    runner = HeadlessBatchRunner(
        settings,
        args.host,
        args.port,
        args.timeout,
        signals,
        args.output_file,
        corr_factors=corr_factors,
    )
    runner.run(args.acquisition_time)


def main():
    args = get_parser().parse_args()
    if args.list_signals:
        if args.headless_ma:
            _print_batch_signal_info(args)
        else:
            _print_signal_info(args)
        return
    if args.csv_lst:
        _print_csv_columns(args.csv_lst)
        return
    if args.headless and args.headless_ma:
        raise SystemExit("Choose only one: --headless or --headless-ma")
    if args.headless:
        _run_headless(args)
        return
    if args.headless_ma:
        _run_headless_ma(args)
        return
    if args.csv_open and (args.sig or args.sigset):
        raise SystemExit("CSV mode is exclusive: do not pass signals or sigset.")

    app = QApplication(sys.argv)
    csv_items = None
    csv_axes = None
    csv_mode = False
    if args.csv_open:
        csv_mode = True
        signal_yaxes = args.signal_yaxes
        if args.signal_yaxes_seq:
            signal_yaxes = "y"
        try:
            csv_items = load_csv_items(args.csv_open, args.csv_cols)
        except Exception as exc:
            raise SystemExit(str(exc))
        csv_axes = _axis_sequence_for_items(len(csv_items), signal_yaxes)
    win = WindowMain(
        args.host,
        args.port,
        args.timeout,
        args.sig,
        args.axis,
        args.sigset,
        args.corr,
        # args.yrange,
        args.dump_rate,
        args.sample_rate,
        csv_mode=csv_mode,
        csv_items=csv_items,
        csv_axes=csv_axes,
    )
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


def _print_signal_info(args):
    print("Available signals:")
    for sig in AVAILABLE_SIGNALS:
        print(f"  - {sig}")
    print("\nHeadless batch status syntax:")
    print("  FStat>flags_1_2_3 or Stat>flags_1_2_3")
    print(
        "  flags: r(ready) m(moving) s(settling) c(stopcode) o(outofwin) n(lim-) p(lim+) h(home)"
    )
    print("\nPredefined signal sets:")
    for name, config in SIGNAL_SETS.items():
        print(f"  {name}:")
        for signal_def in config["signals"]:
            sig_name, axis = signal_def[0], signal_def[1]
            print(f"    * {sig_name} (axis {axis})")


def _print_batch_signal_info(args):
    print("Available batch signal bases:")
    for sig, _ in BATCH_SIGNAL_GETTER_MAP:
        print(f"  - {sig}")
    print("\nBatch syntax:")
    print("  Base_1_2_3 (e.g. PosMeasure_1_2_3)")
    print("  FStat>flags_1_2_3 or Stat>flags_1_2_3")
    print(
        "  flags: r(ready) m(moving) s(settling) c(stopcode) o(outofwin) n(lim-) p(lim+) h(home)"
    )


def _available_axis_names():
    return ["Y1", "Y2", "Y3", "Y4", "Y5", "Y6"]


def _axis_sequence_for_items(n_items, signal_yaxes):
    axis_names = _available_axis_names()
    if not axis_names or n_items == 0:
        return []
    value = (signal_yaxes or "").strip()
    if not value or value.lower() == "y":
        seq = axis_names
    else:
        seq = [
            axis.strip().upper()
            for axis in value.replace("=", "").split(",")
            if axis.strip()
        ]
        if not seq:
            seq = axis_names
    result = []
    for idx in range(n_items):
        axis = seq[idx] if idx < len(seq) else seq[-1]
        if axis not in axis_names:
            axis = axis_names[-1]
        result.append(axis)
    return result


def _print_csv_columns(path):
    try:
        labels = inspect_csv_columns(path)
    except Exception as exc:
        raise SystemExit(str(exc))
    for idx, label in enumerate(labels, start=1):
        print(f"{idx}: {label}")

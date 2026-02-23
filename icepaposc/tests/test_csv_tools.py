import csv
import math
from pathlib import Path

import pytest
from PyQt5.QtCore import Qt

from icepaposc.csvloader import load_csv_items
from icepaposc.window_main import WindowMain


DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def csv_window(qtbot):
    # Build a minimal WindowMain instance wired to CSV mode for tests.
    def _make(path, axes=None):
        # Load PlotDataItems from CSV and inject them into the window.
        items = load_csv_items(str(path))
        win = WindowMain(
            "csv",
            0,
            0,
            [],
            1,
            "",
            "",
            csv_mode=True,
            csv_items=items,
            csv_axes=axes,
        )
        qtbot.addWidget(win)
        win.show()
        return win

    return _make


def _read_csv_header(path):
    # Helper to grab the first row for header validation.
    with open(path, newline="") as f:
        reader = csv.reader(f)
        return next(reader, [])


def _read_csv_columns(path):
    # Helper to map header names -> float columns (empty cells as NaN).
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        cols = {name: [] for name in header[1:]}
        for row in reader:
            if not row:
                continue
            for idx, name in enumerate(header[1:], start=1):
                cell = row[idx] if idx < len(row) else ""
                if cell == "":
                    cols[name].append(float("nan"))
                else:
                    cols[name].append(float(cell))
        return cols


def test_csv_fft_export(csv_window, tmp_path, qtbot):
    # Load the FFT sample CSV in multi-axis mode.
    win = csv_window(DATA_DIR / "csv_fft_sines.csv", axes=["Y1", "Y2", "Y3"])
    # Open FFT dialog, select all signals, and run the transform.
    tool = win.fftTool
    tool._open_dialog(win._plot_item)
    for i in range(tool._list.count()):
        tool._list.item(i).setCheckState(Qt.Checked)
    tool._run_fft(win._plot_item)

    # Redirect the quick-save path to a temp file and save.
    out = tmp_path / "fft.csv"
    tool._build_quicksave_path = lambda suffix: str(out)
    tool._save_fft()

    # Validate header contains FFT columns for time/value pairs.
    header = _read_csv_header(out)
    assert header
    assert sum(name.endswith("_fft") for name in header) == 6

    # Validate FFT peaks around the known frequencies and magnitudes.
    cols = _read_csv_columns(out)
    for idx, target_freq in enumerate((1.0, 2.0, 5.0), start=1):
        freq_key = f"time-{idx}_sig{idx}_fft"
        val_key = f"val-{idx}_sig{idx}_fft"
        freqs = cols[freq_key]
        vals = cols[val_key]
        pairs = [(f, v) for f, v in zip(freqs, vals) if not math.isnan(f)]
        pairs = [(f, v) for f, v in pairs if f >= 0.0]
        assert pairs
        peak_f, peak_v = max(pairs, key=lambda p: p[1])
        assert abs(peak_f - target_freq) <= 0.1
        assert 450.0 <= peak_v <= 550.0
        dc = vals[0]
        # default FFT bandpass removes the DC component, so expect it near zero
        assert math.isclose(dc, 0.0, abs_tol=1e-6)


def test_csv_derivative_export(csv_window, tmp_path, qtbot):
    # Load the derivative sample CSV in multi-axis mode.
    win = csv_window(DATA_DIR / "csv_derivative_shapes.csv", axes=["Y1", "Y2", "Y3", "Y4"])
    # Open derivative dialog, select all signals, and run the derivative.
    tool = win.derivativeTool
    tool._open_dialog(win._plot_item)
    for i in range(tool._list.count()):
        tool._list.item(i).setCheckState(Qt.Checked)
    tool._run_derivative(win._plot_item)

    # Redirect the quick-save path to a temp file and save.
    out = tmp_path / "derivative.csv"
    tool._build_quicksave_path = lambda suffix: str(out)
    tool._save_derivative()

    # Validate expected outputs: zero/constant inputs produce zero derivative.
    cols = _read_csv_columns(out)
    zero_key = next(k for k in cols if "val-1_zero_der" in k)
    const_key = next(k for k in cols if "val-2_const_der" in k)
    for v in cols[zero_key]:
        assert math.isclose(v, 0.0, abs_tol=1e-6)
    for v in cols[const_key]:
        assert math.isclose(v, 0.0, abs_tol=1e-6)

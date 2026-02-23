import os
import time

import pytest

from icepaposc.headless import HeadlessRunner
from icepaposc.settings import Settings
from icepaposc.tests.FIcePAPController import FIcePAPController


@pytest.fixture
def fake_time(monkeypatch):
    # Deterministic clock to avoid real sleeps and timestamps in tests.
    class FakeClock:
        def __init__(self):
            self.current = 0.0

        def __call__(self):
            val = self.current
            self.current += 1.0
            return val

    clock = FakeClock()
    # Patch all time usage in headless pipeline and fake controller.
    monkeypatch.setattr("icepaposc.headless.time.time", clock)
    monkeypatch.setattr("icepaposc.collector.time.time", clock)
    monkeypatch.setattr("icepaposc.tests.FIcePAPController.time.time", clock)
    monkeypatch.setattr("icepaposc.headless.time.sleep", lambda _: None)
    monkeypatch.setattr("icepaposc.collector.time.sleep", lambda _: None)
    original_localtime = time.localtime
    original_mktime = time.mktime

    # Ensure any date formatting calls are still valid under fake time.
    def fake_localtime(_=None):
        return original_localtime(clock.current + 1_000_000)

    def fake_mktime(t):
        return original_mktime(t)

    monkeypatch.setattr(
        "icepaposc.tests.FIcePAPController.time.localtime", fake_localtime
    )
    monkeypatch.setattr(
        "icepaposc.tests.FIcePAPController.time.mktime", fake_mktime
    )
    return clock


def test_headless_runner_writes_csv(tmp_path, fake_time):
    # Configure a fast acquisition so the test completes quickly.
    settings = Settings()
    settings.sample_rate = 100
    settings.dump_rate = 1
    output_file = tmp_path / "capture.csv"

    # Use a fake controller and a single signal to keep the CSV small.
    controller = FIcePAPController("localhost", auto_axes=True)
    runner = HeadlessRunner(
        settings,
        host="localhost",
        port=5000,
        timeout=3,
        signals=[(1, "PosAxis", 1)],
        output_file=str(output_file),
        corr_factors=[1, 0, 1, 0],
        icepap_controller=controller,
    )

    runner.run(acquisition_time=10)

    # Validate the output CSV exists and has a header with time columns.
    assert output_file.exists()
    content = output_file.read_text().strip().splitlines()
    assert len(content) > 1
    header = content[0].split(",")
    assert header[1].startswith("time-1-PosAxis")

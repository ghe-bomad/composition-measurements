import math

import pytest

from h2s_reader.h2s_sensor import (
    vout_to_current_uA,
    current_to_ppm,
    vnode_to_rntc,
    rntc_to_celsius,
)


def test_current_is_zero_at_internal_zero_voltage():
    assert vout_to_current_uA(0.50) == 0.0


def test_current_at_span_point():
    # 9.9 uA -> VOUT = 0.5 + 9.9e-6 * 7000 = 0.5693 V
    assert vout_to_current_uA(0.5693) == pytest.approx(9.9, abs=1e-3)


def test_ppm_baseline_and_span():
    assert current_to_ppm(0.063) == pytest.approx(0.0, abs=1e-9)   # baseline -> 0 ppm
    assert current_to_ppm(9.9) == pytest.approx(99.36, abs=0.01)   # span -> ~100 ppm


def test_thermistor_resistance_at_midpoint():
    assert vnode_to_rntc(1.65) == pytest.approx(10000.0, abs=1.0)


def test_thermistor_open_and_short_guarded():
    assert math.isnan(vnode_to_rntc(3.3))   # node at rail -> open NTC
    assert math.isnan(vnode_to_rntc(0.0))   # node at gnd  -> shorted


def test_celsius_at_nominal_resistance():
    assert rntc_to_celsius(10000.0) == pytest.approx(25.0, abs=0.05)


def test_celsius_nan_when_resistance_invalid():
    assert math.isnan(rntc_to_celsius(math.nan))

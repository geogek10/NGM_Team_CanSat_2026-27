import numpy as np
from cansat_core import (
    compute_air_density,
    compute_isa_altitude,
    compute_vertical_speed,
    validate_live_packet,
)


def test_isa_altitude_zero_at_qfe():
    assert abs(compute_isa_altitude(1005.0, p0_hpa=1005.0)) < 1e-6


def test_isa_altitude_climb():
    alt = compute_isa_altitude(900.0, p0_hpa=1013.25)
    assert 980.0 < alt < 995.0


def test_air_density_sea_level():
    rho = compute_air_density(1013.25, 15.0)
    assert 1.22 < rho < 1.23


def test_vertical_speed_constant_descent():
    t = np.linspace(0, 20, 41)  # 0.5s step
    alt = 500.0 - 8.0 * t       # constant -8 m/s
    vz = compute_vertical_speed(alt, t)
    assert np.allclose(vz, -8.0, atol=0.1)


def test_live_packet_validation():
    good_pkt = {
        "temp_c": 20.0, "press_hpa": 1010.0, "hum_pct": 50.0,
        "batt_v": 15.8, "sats": 14, "hdop": 0.9,
    }
    ok, warnings = validate_live_packet(good_pkt)
    assert ok and warnings == []

    bad_pkt = {**good_pkt, "temp_c": 150.0, "sats": 3}
    ok, warnings = validate_live_packet(bad_pkt)
    assert not ok
    assert "TEMP_OUT_OF_BOUNDS" in warnings
    assert "LOW_GNSS_SATS" in warnings
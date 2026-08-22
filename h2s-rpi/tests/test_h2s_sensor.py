from h2s_reader import config
from h2s_reader.h2s_sensor import H2SSensor, Reading
from fakes import FakeBus


def _bus_with(vout_bytes, temp_bytes):
    bus = FakeBus()
    bus.byte_regs[(config.LMP91002_ADDR, config.REG_STATUS)] = 0x01
    bus.conversion_by_config[config.ADS_CONF_AIN0] = vout_bytes
    bus.conversion_by_config[config.ADS_CONF_AIN2] = temp_bytes
    return bus


def test_configure_runs_lmp_sequence():
    bus = _bus_with([0x10, 0xB9], [0x33, 0x90])
    H2SSensor(bus).configure()
    # unlock, TIACN, REFCN, lock, MODECN
    assert len(bus.writes) == 5
    assert bus.writes[2] == (config.LMP91002_ADDR, config.REG_REFCN, config.REFCN_VALUE)


def test_read_returns_ppm_and_temp():
    # AIN0 = 0x10B9 = 4281 -> 0.535125 V -> ~5.02 uA -> ~50 ppm
    # AIN2 = 0x3390 = 13200 -> 1.65 V -> 10 kohm -> 25 C
    bus = _bus_with([0x10, 0xB9], [0x33, 0x90])
    sensor = H2SSensor(bus)
    sensor.configure()
    r = sensor.read()
    assert isinstance(r, Reading)
    assert abs(r.ppm - 50.0) < 0.2
    assert abs(r.temp_c - 25.0) < 0.1
    assert abs(r.vout_v - 0.535125) < 1e-6
    assert abs(r.r_ntc_ohm - 10000.0) < 1.0

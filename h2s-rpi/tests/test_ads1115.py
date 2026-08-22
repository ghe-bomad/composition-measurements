import pytest

from h2s_reader import config
from h2s_reader.ads1115 import ADS1115, counts_to_volts
from fakes import FakeBus


def test_counts_to_volts_zero_and_fullscale():
    assert counts_to_volts(0) == 0.0
    assert counts_to_volts(13200) == pytest.approx(1.65, abs=1e-6)  # 13200 * 4.096 / 32768


def test_counts_to_volts_negative():
    assert counts_to_volts(-1) == pytest.approx(-0.000125, abs=1e-9)


def test_read_channel_writes_config_and_returns_volts():
    bus = FakeBus()
    bus.conversion_by_config[config.ADS_CONF_AIN0] = [0x33, 0x90]  # 0x3390 = 13200
    ads = ADS1115(bus)
    volts = ads.read_channel_volts(config.ADS_CONF_AIN0, settle_s=0.0)
    assert volts == pytest.approx(1.65, abs=1e-6)
    assert bus.block_writes[0] == (config.ADS1115_ADDR, config.ADS_REG_CONFIG, [0xC3, 0x83])

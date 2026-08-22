"""Minimal ADS1115 single-shot reader. The I2C bus is injected."""

import time

from . import config


def counts_to_volts(raw, fsr=config.ADS_FSR):
    """Convert a signed 16-bit conversion result to volts."""
    return raw * fsr / 32768.0


def _to_signed16(value):
    """Interpret a 16-bit unsigned value as two's-complement signed."""
    return value - 65536 if value & 0x8000 else value


class ADS1115:
    def __init__(self, bus, addr=config.ADS1115_ADDR):
        self._bus = bus
        self._addr = addr

    def read_channel_volts(self, config_word, settle_s=0.01):
        """Start a single conversion for the given config word and return volts."""
        msb = (config_word >> 8) & 0xFF
        lsb = config_word & 0xFF
        self._bus.write_i2c_block_data(self._addr, config.ADS_REG_CONFIG, [msb, lsb])
        if settle_s:
            time.sleep(settle_s)  # 128 SPS -> ~7.8 ms/conversion
        data = self._bus.read_i2c_block_data(self._addr, config.ADS_REG_CONVERSION, 2)
        raw = _to_signed16((data[0] << 8) | data[1])
        return counts_to_volts(raw)

"""H2S sensor domain layer: calibration math, then composition of the two drivers."""

import math
from dataclasses import dataclass

from . import config
from .ads1115 import ADS1115
from .lmp91002 import LMP91002


def vout_to_current_uA(vout, v_zero=config.V_ZERO, r_tia=config.R_TIA,
                       polarity=config.POLARITY):
    """LMP91002 TIA output voltage -> working-electrode current in microamps."""
    return polarity * (vout - v_zero) / r_tia * 1e6


def current_to_ppm(i_uA, i0=config.I0_UA, sensitivity=config.SENSITIVITY_UA_PER_PPM):
    """Electrode current (uA) -> H2S concentration (ppm) via two-point calibration."""
    return (i_uA - i0) / sensitivity


def vnode_to_rntc(v_node, r_fixed=config.NTC_R_FIXED, vsupply=config.NTC_VSUPPLY):
    """Divider node voltage -> NTC resistance. VSUPPLY--R_FIXED--node--NTC--GND.

    Returns NaN for an open (node at rail) or shorted (node at gnd) thermistor.
    """
    if v_node <= 0 or v_node >= vsupply:
        return math.nan
    return r_fixed * v_node / (vsupply - v_node)


def rntc_to_celsius(r_ntc, r0=config.NTC_R0, beta=config.NTC_BETA, t0_k=config.NTC_T0_K):
    """NTC resistance -> temperature (deg C) via the Beta equation."""
    if not math.isfinite(r_ntc) or r_ntc <= 0:
        return math.nan
    inv_t = 1.0 / t0_k + math.log(r_ntc / r0) / beta
    return 1.0 / inv_t - 273.15


@dataclass
class Reading:
    ppm: float
    i_we_uA: float
    vout_v: float
    temp_c: float
    r_ntc_ohm: float


class H2SSensor:
    """Composes the LMP91002 AFE and ADS1115 ADC into calibrated readings."""

    def __init__(self, bus):
        self._lmp = LMP91002(bus)
        self._ads = ADS1115(bus)

    @classmethod
    def open(cls, bus_num=config.I2C_BUS):
        from smbus2 import SMBus  # lazy: only needed on real hardware
        return cls(SMBus(bus_num))

    def configure(self):
        self._lmp.wait_ready()
        self._lmp.configure()

    def read(self):
        vout = self._ads.read_channel_volts(config.ADS_CONF_AIN0)
        v_node = self._ads.read_channel_volts(config.ADS_CONF_AIN2)
        i_uA = vout_to_current_uA(vout)
        r_ntc = vnode_to_rntc(v_node)
        return Reading(
            ppm=current_to_ppm(i_uA),
            i_we_uA=i_uA,
            vout_v=vout,
            temp_c=rntc_to_celsius(r_ntc),
            r_ntc_ohm=r_ntc,
        )

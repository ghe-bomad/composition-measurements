"""Command-line entry point: python -m h2s_reader [--stream] [--selftest]."""

import argparse
import sys
import time

from . import config
from .h2s_sensor import H2SSensor


def format_reading(r):
    return (f"H2S={r.ppm:7.2f} ppm  I_we={r.i_we_uA:7.3f} uA  "
            f"Vout={r.vout_v:6.4f} V  T={r.temp_c:6.2f} C")


def selftest(bus):
    ok = True
    for name, addr in (("LMP91002", config.LMP91002_ADDR),
                       ("ADS1115", config.ADS1115_ADDR)):
        try:
            bus.read_byte(addr)
            print(f"OK   {name} @ 0x{addr:02X}")
        except OSError:
            print(f"FAIL {name} @ 0x{addr:02X} not responding")
            ok = False
    return 0 if ok else 1


def main(argv=None):
    p = argparse.ArgumentParser(prog="h2s_reader",
                                description="Read the H2S PCB over I2C")
    p.add_argument("--bus", type=int, default=config.I2C_BUS)
    p.add_argument("--stream", action="store_true", help="repeat until interrupted")
    p.add_argument("--interval", type=float, default=2.0, help="seconds between reads")
    p.add_argument("--selftest", action="store_true",
                   help="check both I2C devices respond, then exit")
    args = p.parse_args(argv)

    from smbus2 import SMBus  # lazy: only needed on real hardware
    bus = SMBus(args.bus)

    if args.selftest:
        return selftest(bus)

    sensor = H2SSensor(bus)
    sensor.configure()
    try:
        while True:
            print(format_reading(sensor.read()))
            if not args.stream:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

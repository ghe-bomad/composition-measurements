import sys
from pathlib import Path

from smbus2 import SMBus


PROJECT_ROOT = Path(__file__).resolve().parent.parent
H2S_READER_DIR = PROJECT_ROOT / "h2s-rpi"

if str(H2S_READER_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(H2S_READER_DIR),
    )


from h2s_reader import config as h2s_config
from h2s_reader.h2s_sensor import H2SSensor


class H2SController:

    def __init__(self):
        self.bus = None
        self.sensor = None

    def connect(self):
        if self.sensor is not None:
            return

        print(
            "Connecting to Mzuzu H2S sensor..."
        )

        self.bus = SMBus(
            h2s_config.I2C_BUS
        )

        self.sensor = H2SSensor(
            self.bus
        )

        self.sensor.configure()

        print(
            "Mzuzu H2S sensor connected"
        )

    def read(self):
        if self.sensor is None:
            raise RuntimeError(
                "Mzuzu H2S sensor is not connected."
            )

        reading = self.sensor.read()

        return {
            "h2s_ppm": float(
                reading.ppm
            ),
            "temperature_c": float(
                reading.temp_c
            ),
            "current_uA": float(
                reading.i_we_uA
            ),
            "vout_v": float(
                reading.vout_v
            ),
            "r_ntc_ohm": float(
                reading.r_ntc_ohm
            ),
        }

    def disconnect(self):
        self.sensor = None

        if self.bus is not None:
            try:
                self.bus.close()
            except Exception:
                pass

        self.bus = None

        print(
            "Mzuzu H2S sensor disconnected"
        )

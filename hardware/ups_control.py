from smbus2 import SMBus


I2C_BUS = 1
UPS_ADDRESS = 0x36

SOC_REGISTER = 0x04
VOLTAGE_REGISTER = 0x02


def _swap_word(value):
    return (
        ((value & 0xFF) << 8)
        | ((value >> 8) & 0xFF)
    )


class UPSController:

    def __init__(self):
        self.bus = None

    def connect(self):
        if self.bus is None:
            self.bus = SMBus(I2C_BUS)

    def read_status(self):
        if self.bus is None:
            self.connect()

        soc_raw = self.bus.read_word_data(
            UPS_ADDRESS,
            SOC_REGISTER,
        )

        voltage_raw = self.bus.read_word_data(
            UPS_ADDRESS,
            VOLTAGE_REGISTER,
        )

        soc_raw = _swap_word(soc_raw)
        voltage_raw = _swap_word(voltage_raw)

        battery_percent = (
            (soc_raw >> 8)
            + ((soc_raw & 0xFF) / 256.0)
        )

        battery_voltage = (
            voltage_raw
            * 1.25
            / 1000
            / 16
        )

        return {
            "battery_percent": round(
                battery_percent,
                1,
            ),
            "battery_voltage": round(
                battery_voltage,
                3,
            ),
        }

    def disconnect(self):
        if self.bus is not None:
            try:
                self.bus.close()
            except Exception:
                pass

        self.bus = None


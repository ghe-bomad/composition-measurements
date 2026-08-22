from drager_xam_8000.xam8000.device import DragerXam8000


class DragerController:
    def __init__(self, pump_flow=350):
        self.pump_flow = pump_flow
        self.device = None

    def connect(self):
        if self.device is not None:
            return

        print("Verbinde mit Dräger...")

        self.device = DragerXam8000()
        self.device.connect()

        print("Dräger verbunden")

    def disconnect(self):
        if self.device is None:
            return

        print("Trenne Dräger-Verbindung")

        self.device.disconnect()
        self.device = None

    def pump_on(self):
        if self.device is None:
            raise RuntimeError("Dräger ist nicht verbunden.")

        self.device.set_pump(self.pump_flow)

        print(f"Pumpe eingeschaltet: {self.pump_flow} ml/min")

    def pump_off(self):
        if self.device is None:
            return

        self.device.set_pump(0)

        print("Pumpe ausgeschaltet")

    def read_measurements(self):
        if self.device is None:
            raise RuntimeError("Dräger ist nicht verbunden.")

        readings = self.device.get_gas_readings()

        measurements = []

        for reading in readings:
            measurements.append(
                {
                    "channel": reading.channel,
                    "gas": reading.gas_name,
                    "value": reading.value if reading.is_valid else None,
                    "unit": reading.unit_label,
                    "valid": reading.is_valid,
                }
            )

        return measurements

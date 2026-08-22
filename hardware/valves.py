from hardware import PiRelay6


class ValveController:
    def __init__(self):
        self.relays = {
            1: PiRelay6.Relay("RELAY1"),
            2: PiRelay6.Relay("RELAY2"),
            3: PiRelay6.Relay("RELAY3"),
            4: PiRelay6.Relay("RELAY4"),
            5: PiRelay6.Relay("RELAY5"),
            6: PiRelay6.Relay("RELAY6"),
        }

        self.current_valve = None
        self.close_all()

    def open_valve(self, valve_number):
        if valve_number not in self.relays:
            raise ValueError(
                f"Valve {valve_number} doesn't exist. "
                "Valve 1 to 6 are are allowed."
            )

        self.close_all()

        self.relays[valve_number].on()
        self.current_valve = valve_number

        print(f"Valve {valve_number} is open")

    def close_valve(self, valve_number):
        if valve_number not in self.relays:
            raise ValueError(
                f"Valve {valve_number} doesn't exist."
            )

        self.relays[valve_number].off()

        if self.current_valve == valve_number:
            self.current_valve = None

        print(f"Valve {valve_number} closed")

    def close_all(self):
        for relay in self.relays.values():
            relay.off()

        self.current_valve = None

        print("All valves are closed")

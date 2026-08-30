
import json
import time
from pathlib import Path

from hardware.valves import ValveController
from hardware.drager_control import DragerController
from hardware.h2s_control import H2SController

from csv_data.csv_storage import CSVStorage

from system_logs.status_storage import (
    StatusStorage,
)

from settings.config_storage import (
    load_config,
)


CONFIG_PATH = (
    Path(__file__).parent
    / "config.json"
)


def load_config():
    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as config_file:
        return json.load(
            config_file
        )


def read_all_sensors(
    drager,
    h2s_sensor,
):
    drager_measurements = (
        drager.read_measurements()
    )

    mzuzu_measurement = (
        h2s_sensor.read()
    )

    return (
        drager_measurements,
        mzuzu_measurement,
    )


def print_measurements(
    valve_number,
    drager_measurements,
    mzuzu_measurement,
):
    print()
    print(
        f"Valve {valve_number}:"
    )

    for measurement in drager_measurements:
        print(
            f"{measurement['gas']}: "
            f"{measurement['value']} "
            f"{measurement['unit']}"
        )

    print(
        "H2S Mzuzu: "
        f"{mzuzu_measurement['h2s_ppm']:.2f} ppm"
    )

    print(
        "Mzuzu temperature: "
        f"{mzuzu_measurement['temperature_c']:.2f} C"
    )


def measure_active_valve(
    valves,
    drager,
    h2s_sensor,
    csv_storage,
    status_storage,
    valve_number,
    cycle_number,
    duration_seconds,
    interval_seconds,
    mode,
):
    valves.open_valve(
        valve_number
    )

    if mode == "flush":
        message = (
            f"System is flushing through "
            f"Valve {valve_number}."
        )
    else:
        message = (
            f"Valve {valve_number} "
            "is being measured."
        )

    status_storage.update(
        running=True,
        mode=mode,
        current_valve=valve_number,
        cycle=cycle_number,
        pump=True,
        message=message,
    )

    start_time = time.monotonic()

    try:
        while (
            time.monotonic()
            - start_time
            < duration_seconds
        ):
            (
                drager_measurements,
                mzuzu_measurement,
            ) = read_all_sensors(
                drager,
                h2s_sensor,
            )

            csv_storage.save_measurement(
                valve=valve_number,
                drager_measurements=(
                    drager_measurements
                ),
                mzuzu_measurement=(
                    mzuzu_measurement
                ),
            )

            status_storage.update(
                running=True,
                mode=mode,
                current_valve=valve_number,
                cycle=cycle_number,
                pump=True,
                message=message,
                measurements=(
                    drager_measurements
                ),
                mzuzu=(
                    mzuzu_measurement
                ),
            )

            print_measurements(
                valve_number,
                drager_measurements,
                mzuzu_measurement,
            )

            elapsed_time = (
                time.monotonic()
                - start_time
            )

            remaining_time = (
                duration_seconds
                - elapsed_time
            )

            if remaining_time > 0:
                time.sleep(
                    min(
                        interval_seconds,
                        remaining_time,
                    )
                )

    finally:
        valves.close_valve(
            valve_number
        )


def measure_valve(
    valves,
    drager,
    h2s_sensor,
    csv_storage,
    status_storage,
    valve_number,
    cycle_number,
    measurement_duration_seconds,
    measurement_interval_seconds,
):
    print()
    print(
        f"Starting measurement for "
        f"Valve {valve_number}"
    )

    measure_active_valve(
        valves=valves,
        drager=drager,
        h2s_sensor=h2s_sensor,
        csv_storage=csv_storage,
        status_storage=status_storage,
        valve_number=valve_number,
        cycle_number=cycle_number,
        duration_seconds=(
            measurement_duration_seconds
        ),
        interval_seconds=(
            measurement_interval_seconds
        ),
        mode="measurement",
    )

    print(
        f"Measurement for Valve "
        f"{valve_number} completed."
    )


def flush_system(
    valves,
    drager,
    h2s_sensor,
    csv_storage,
    status_storage,
    flush_valve,
    flush_seconds,
    measurement_interval_seconds,
    cycle_number,
):
    print()
    print(
        f"Starting flush through "
        f"Valve {flush_valve}"
    )

    measure_active_valve(
        valves=valves,
        drager=drager,
        h2s_sensor=h2s_sensor,
        csv_storage=csv_storage,
        status_storage=status_storage,
        valve_number=flush_valve,
        cycle_number=cycle_number,
        duration_seconds=(
            flush_seconds
        ),
        interval_seconds=(
            measurement_interval_seconds
        ),
        mode="flush",
    )

    print(
        "Flush completed."
    )


def run_measurement_cycle(
    valves,
    drager,
    h2s_sensor,
    csv_storage,
    status_storage,
    measurement_valves,
    flush_valve,
    flush_seconds,
    measurement_duration_seconds,
    measurement_interval_seconds,
    cycle_number,
):
    for valve_number in measurement_valves:
        measure_valve(
            valves=valves,
            drager=drager,
            h2s_sensor=h2s_sensor,
            csv_storage=csv_storage,
            status_storage=status_storage,
            valve_number=valve_number,
            cycle_number=cycle_number,
            measurement_duration_seconds=(
                measurement_duration_seconds
            ),
            measurement_interval_seconds=(
                measurement_interval_seconds
            ),
        )

        flush_system(
            valves=valves,
            drager=drager,
            h2s_sensor=h2s_sensor,
            csv_storage=csv_storage,
            status_storage=status_storage,
            flush_valve=flush_valve,
            flush_seconds=flush_seconds,
            measurement_interval_seconds=(
                measurement_interval_seconds
            ),
            cycle_number=cycle_number,
        )


def run():
    config = load_config()

    measurement_valves = (
        config["measurement_valves"]
    )

    flush_valve = (
        config["flush_valve"]
    )

    pump_start_delay_seconds = (
        config[
            "pump_start_delay_seconds"
        ]
    )

    flush_seconds = (
        config["flush_seconds"]
    )

    measurement_duration_seconds = (
        config[
            "measurement_duration_seconds"
        ]
    )

    measurement_interval_seconds = (
        config[
            "measurement_interval_seconds"
        ]
    )

    cycle_pause_seconds = (
        config[
            "cycle_pause_seconds"
        ]
    )

    continuous_mode = (
        config[
            "continuous_mode"
        ]
    )

    pump_flow = (
        config[
            "pump_flow"
        ]
    )

    valves = ValveController()

    drager = DragerController(
        pump_flow=pump_flow
    )

    h2s_sensor = H2SController()

    csv_storage = CSVStorage()

    status_storage = StatusStorage()

    cycle_number = 1

    try:
        valves.close_all()

        status_storage.update(
            running=True,
            mode="starting",
            current_valve=None,
            cycle=cycle_number,
            pump=False,
            message=(
                "Connecting sensors."
            ),
        )

        drager.connect()

        h2s_sensor.connect()

        drager.pump_on()

        status_storage.update(
            running=True,
            mode="pump_start_delay",
            current_valve=None,
            cycle=cycle_number,
            pump=True,
            message=(
                f"Waiting "
                f"{pump_start_delay_seconds} "
                "seconds for the pump "
                "to reach stable operation."
            ),
        )

        print(
            f"Waiting "
            f"{pump_start_delay_seconds} "
            "seconds for the pump "
            "to reach stable operation."
        )

        time.sleep(
            pump_start_delay_seconds
        )

        while True:
            print()
            print(
                "=" * 50
            )

            print(
                f"Starting measurement cycle "
                f"{cycle_number}"
            )

            print(
                "=" * 50
            )

            run_measurement_cycle(
                valves=valves,
                drager=drager,
                h2s_sensor=h2s_sensor,
                csv_storage=csv_storage,
                status_storage=status_storage,
                measurement_valves=(
                    measurement_valves
                ),
                flush_valve=(
                    flush_valve
                ),
                flush_seconds=(
                    flush_seconds
                ),
                measurement_duration_seconds=(
                    measurement_duration_seconds
                ),
                measurement_interval_seconds=(
                    measurement_interval_seconds
                ),
                cycle_number=(
                    cycle_number
                ),
            )

            print()
            print(
                f"Measurement cycle "
                f"{cycle_number} "
                "completed."
            )

            if not continuous_mode:
                print(
                    "Continuous mode is disabled."
                )
                break

            cycle_number += 1

            if cycle_pause_seconds > 0:
                status_storage.update(
                    running=True,
                    mode="cycle_pause",
                    current_valve=None,
                    cycle=cycle_number,
                    pump=True,
                    message=(
                        f"Waiting "
                        f"{cycle_pause_seconds} "
                        "seconds before the "
                        "next measurement cycle."
                    ),
                )

                print(
                    f"Waiting "
                    f"{cycle_pause_seconds} "
                    "seconds before the "
                    "next measurement cycle."
                )

                time.sleep(
                    cycle_pause_seconds
                )

    except KeyboardInterrupt:
        print()
        print(
            "Program stopped manually."
        )

    except Exception as error:
        print()
        print(
            f"Error: {error}"
        )

        status_storage.update(
            running=False,
            mode="error",
            current_valve=None,
            cycle=cycle_number,
            pump=False,
            message=str(
                error
            ),
        )

    finally:
        print()
        print(
            "Safely shutting down measurement system."
        )

        try:
            valves.close_all()
        except Exception as error:
            print(
                "Error while closing valves: "
                f"{error}"
            )

        try:
            drager.pump_off()
        except Exception as error:
            print(
                "Pump could not be switched off: "
                f"{error}"
            )

        try:
            drager.disconnect()
        except Exception as error:
            print(
                "Drager could not be disconnected: "
                f"{error}"
            )

        try:
            h2s_sensor.disconnect()
        except Exception as error:
            print(
                "Mzuzu sensor could not be disconnected: "
                f"{error}"
            )

        try:
            csv_storage.close()
        except Exception as error:
            print(
                "CSV file could not be closed: "
                f"{error}"
            )

        status_storage.set_idle(
            message=(
                "System was safely stopped."
            ),
            clear_measurements=True,
        )

        print(
            "System safely stopped."
        )


if __name__ == "__main__":
    run()
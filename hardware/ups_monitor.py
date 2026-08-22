import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

from hardware.ups_control import UPSController
from system_logs.system_logger import (
    log_ups_shutdown,
)


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

SYSTEM_LOG_DIR = (
    PROJECT_ROOT
    / "system_logs"
)

UPS_STATUS_PATH = (
    SYSTEM_LOG_DIR
    / "ups_status.json"
)

UPS_HISTORY_PATH = (
    SYSTEM_LOG_DIR
    / "ups_history.json"
)


# =========================================================
# SETTINGS
# =========================================================

CHECK_INTERVAL_SECONDS = 5

WARNING_PERCENT = 25.0
SHUTDOWN_PERCENT = 15.0

WARNING_VOLTAGE = 3.40
SHUTDOWN_VOLTAGE = 3.25

REQUIRED_LOW_READINGS = 3

GASMONITOR_SERVICE = "gasmonitor.service"


# =========================================================
# TIME
# =========================================================

def timestamp_now():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# =========================================================
# JSON HELPERS
# =========================================================

def write_json_atomic(
    path,
    data,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = (
        path.with_suffix(".tmp")
    )

    with open(
        temporary_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )

    temporary_path.replace(
        path
    )


# =========================================================
# HISTORY
# =========================================================

def load_history():
    if not UPS_HISTORY_PATH.exists():
        return {
            "last_shutdown": None,
        }

    try:
        with open(
            UPS_HISTORY_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(
                file
            )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {
            "last_shutdown": None,
        }


def save_shutdown_event(
    battery_percent,
    battery_voltage,
    reason,
):
    history = load_history()

    history["last_shutdown"] = {
        "time": timestamp_now(),
        "reason": reason,
        "battery_percent": battery_percent,
        "battery_voltage": battery_voltage,
    }

    write_json_atomic(
        UPS_HISTORY_PATH,
        history,
    )


# =========================================================
# LIVE UPS STATUS
# =========================================================

def update_status(
    battery_percent,
    battery_voltage,
    warning=False,
    shutdown_pending=False,
    message="UPS operating normally.",
):
    status = {
        "battery_percent": battery_percent,
        "battery_voltage": battery_voltage,
        "warning": warning,
        "shutdown_pending": shutdown_pending,
        "message": message,
        "power_loss_detection":
            "unavailable_gpio_conflict",
        "last_update": timestamp_now(),
    }

    write_json_atomic(
        UPS_STATUS_PATH,
        status,
    )


# =========================================================
# GAS MONITOR SHUTDOWN
# =========================================================

def stop_measurement_service():
    print(
        "Stopping gas monitoring service...",
        flush=True,
    )

    subprocess.run(
        [
            "systemctl",
            "stop",
            "--no-block",
            GASMONITOR_SERVICE,
        ],
        check=False,
    )

    # Give the measurement system enough time
    # to close valves, stop the Drager pump,
    # disconnect sensors and close the CSV file.
    for second in range(30):

        result = subprocess.run(
            [
                "systemctl",
                "is-active",
                GASMONITOR_SERVICE,
            ],
            capture_output=True,
            text=True,
        )

        service_state = (
            result.stdout.strip()
        )

        print(
            f"Gas monitor state: "
            f"{service_state} "
            f"({second + 1}/30)",
            flush=True,
        )

        if service_state not in (
            "active",
            "activating",
            "deactivating",
        ):
            print(
                "Gas monitoring service "
                "stopped safely.",
                flush=True,
            )

            return True

        time.sleep(1)

    print(
        "WARNING: Gas monitoring service "
        "did not finish stopping "
        "within 30 seconds.",
        flush=True,
    )

    return False


# =========================================================
# SAFE SYSTEM SHUTDOWN
# =========================================================

def shutdown_system(
    battery_percent,
    battery_voltage,
    reason,
):
    print(
        "Critical UPS battery level detected.",
        flush=True,
    )

    print(
        f"Battery: "
        f"{battery_percent:.1f} %",
        flush=True,
    )

    print(
        f"Voltage: "
        f"{battery_voltage:.3f} V",
        flush=True,
    )


    # -----------------------------------------------------
    # Update dashboard status
    # -----------------------------------------------------

    update_status(
        battery_percent,
        battery_voltage,
        warning=True,
        shutdown_pending=True,
        message=(
            "Critical battery level. "
            "Safe shutdown initiated."
        ),
    )


    # -----------------------------------------------------
    # Stop measurement system first
    # -----------------------------------------------------

    print(
        "Initiating safe measurement-system "
        "shutdown...",
        flush=True,
    )

    service_stopped = (
        stop_measurement_service()
    )

    if service_stopped:
        print(
            "Measurement system "
            "stopped successfully.",
            flush=True,
        )

    else:
        print(
            "Measurement system did not report "
            "a clean stop within the timeout. "
            "Continuing with system shutdown.",
            flush=True,
        )


    # -----------------------------------------------------
    # Store UPS shutdown history
    # -----------------------------------------------------

    save_shutdown_event(
        battery_percent,
        battery_voltage,
        reason,
    )


    # -----------------------------------------------------
    # Store shutdown in system event log
    # -----------------------------------------------------

    try:
        log_ups_shutdown(
            battery_percent,
            battery_voltage,
        )

    except Exception as error:
        print(
            "Could not write system "
            f"event log: {error}",
            flush=True,
        )


    # -----------------------------------------------------
    # Final system shutdown
    # -----------------------------------------------------

    print(
        "Waiting 3 seconds before "
        "system poweroff...",
        flush=True,
    )

    time.sleep(3)

    print(
        "Powering off Raspberry Pi now.",
        flush=True,
    )

    subprocess.run(
        [
            "systemctl",
            "poweroff",
        ],
        check=False,
    )


# =========================================================
# MAIN MONITOR LOOP
# =========================================================

def main():
    ups = UPSController()

    consecutive_low_readings = 0

    print(
        "UPS monitor started.",
        flush=True,
    )

    print(
        f"Warning threshold: "
        f"{WARNING_PERCENT:.1f} % / "
        f"{WARNING_VOLTAGE:.2f} V",
        flush=True,
    )

    print(
        f"Shutdown threshold: "
        f"{SHUTDOWN_PERCENT:.1f} % / "
        f"{SHUTDOWN_VOLTAGE:.2f} V",
        flush=True,
    )


    try:
        while True:

            try:
                status = (
                    ups.read_status()
                )

                battery_percent = float(
                    status[
                        "battery_percent"
                    ]
                )

                battery_voltage = float(
                    status[
                        "battery_voltage"
                    ]
                )


                print(
                    f"Battery: "
                    f"{battery_percent:.1f} % | "
                    f"{battery_voltage:.3f} V",
                    flush=True,
                )


                # -------------------------------------
                # Warning threshold
                # -------------------------------------

                warning = (
                    battery_percent
                    <= WARNING_PERCENT

                    or

                    battery_voltage
                    <= WARNING_VOLTAGE
                )


                # -------------------------------------
                # Critical threshold
                # -------------------------------------

                critical = (
                    battery_percent
                    <= SHUTDOWN_PERCENT

                    or

                    battery_voltage
                    <= SHUTDOWN_VOLTAGE
                )


                if critical:
                    consecutive_low_readings += 1

                    print(
                        "Critical battery reading "
                        f"{consecutive_low_readings}/"
                        f"{REQUIRED_LOW_READINGS}",
                        flush=True,
                    )

                else:
                    consecutive_low_readings = 0


                # -------------------------------------
                # Dashboard message
                # -------------------------------------

                if warning:
                    message = (
                        "UPS battery level is low."
                    )

                else:
                    message = (
                        "UPS battery status normal."
                    )


                update_status(
                    battery_percent,
                    battery_voltage,
                    warning=warning,
                    shutdown_pending=False,
                    message=message,
                )


                # -------------------------------------
                # Safe shutdown
                # -------------------------------------

                if (
                    consecutive_low_readings
                    >= REQUIRED_LOW_READINGS
                ):
                    reason = (
                        "Battery reached critical "
                        "shutdown threshold."
                    )

                    shutdown_system(
                        battery_percent,
                        battery_voltage,
                        reason,
                    )

                    return


            except Exception as error:
                print(
                    "UPS monitoring error: "
                    f"{error}",
                    flush=True,
                )


            time.sleep(
                CHECK_INTERVAL_SECONDS
            )


    finally:
        try:
            ups.disconnect()

        except Exception:
            pass


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()

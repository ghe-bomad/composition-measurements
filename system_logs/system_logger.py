import csv
import json
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).parent

EVENT_LOG_PATH = PROJECT_DIR / "system_events.csv"
STATE_PATH = PROJECT_DIR / "system_state.json"


EVENT_HEADERS = [
    "Timestamp",
    "Event",
    "Details",
]


def now_string():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def write_json_atomic(
    path,
    data,
):
    temporary_path = path.with_suffix(
        ".tmp"
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


def load_state():
    if not STATE_PATH.exists():
        return {}

    try:
        with open(
            STATE_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}


def append_event(
    event,
    details="",
):
    file_exists = (
        EVENT_LOG_PATH.exists()
    )

    with open(
        EVENT_LOG_PATH,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=EVENT_HEADERS,
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "Timestamp": now_string(),
                "Event": event,
                "Details": details,
            }
        )


def log_boot():
    state = load_state()

    boot_time = datetime.now()

    previous_shutdown = state.get(
        "last_shutdown"
    )

    if previous_shutdown:
        try:
            shutdown_time = (
                datetime.strptime(
                    previous_shutdown,
                    "%Y-%m-%d %H:%M:%S",
                )
            )

            offline_seconds = int(
                (
                    boot_time
                    - shutdown_time
                ).total_seconds()
            )

            details = (
                "System started. "
                f"Offline duration: "
                f"{offline_seconds} seconds."
            )

        except ValueError:
            details = (
                "System started."
            )

    else:
        details = (
            "System started. "
            "No previous clean shutdown "
            "timestamp was available."
        )

    append_event(
        "BOOT",
        details,
    )

    state["last_boot"] = (
        boot_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    state["running"] = True

    write_json_atomic(
        STATE_PATH,
        state,
    )


def log_shutdown(
    reason="Normal system shutdown.",
):
    state = load_state()

    shutdown_time = now_string()

    append_event(
        "SHUTDOWN",
        reason,
    )

    state["last_shutdown"] = (
        shutdown_time
    )

    state["shutdown_reason"] = (
        reason
    )

    state["running"] = False

    write_json_atomic(
        STATE_PATH,
        state,
    )


def log_ups_shutdown(
    battery_percent,
    battery_voltage,
):
    details = (
        "Safe shutdown triggered by UPS. "
        f"Battery: {battery_percent:.1f} %. "
        f"Voltage: {battery_voltage:.3f} V."
    )

    append_event(
        "UPS_SHUTDOWN",
        details,
    )

    log_shutdown(
        reason=details,
    )


if __name__ == "__main__":
    log_boot()


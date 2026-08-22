# status_storage.py

import json
from datetime import datetime
from pathlib import Path


class StatusStorage:

    def __init__(self):
        self.status_path = (
            Path(__file__).parent
            / "status.json"
        )

        self.latest_measurements = []
        self.latest_mzuzu = None
        self.last_measurement_time = None

        if self.status_path.exists():
            self._load_existing_status()
        else:
            self.set_idle()

    def _load_existing_status(self):
        try:
            with open(
                self.status_path,
                "r",
                encoding="utf-8",
            ) as status_file:
                status = json.load(
                    status_file
                )

            self.latest_measurements = (
                status.get(
                    "measurements",
                    [],
                )
            )

            self.latest_mzuzu = (
                status.get(
                    "mzuzu"
                )
            )

            self.last_measurement_time = (
                status.get(
                    "last_measurement_time"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            self.latest_measurements = []
            self.latest_mzuzu = None
            self.last_measurement_time = None

    def update(
        self,
        running,
        mode,
        current_valve=None,
        cycle=0,
        pump=False,
        message="",
        measurements=None,
        mzuzu=None,
    ):
        if measurements is not None:
            self.latest_measurements = (
                measurements
            )

        if mzuzu is not None:
            self.latest_mzuzu = (
                mzuzu
            )

        if (
            measurements is not None
            or mzuzu is not None
        ):
            self.last_measurement_time = (
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        status = {
            "running": running,
            "mode": mode,
            "current_valve": current_valve,
            "cycle": cycle,
            "pump": pump,
            "message": message,
            "measurements": self.latest_measurements,
            "mzuzu": self.latest_mzuzu,
            "last_measurement_time": self.last_measurement_time,
            "last_update": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

        temporary_path = (
            self.status_path
            .with_suffix(".tmp")
        )

        with open(
            temporary_path,
            "w",
            encoding="utf-8",
        ) as status_file:
            json.dump(
                status,
                status_file,
                indent=4,
                ensure_ascii=False,
            )

        temporary_path.replace(
            self.status_path
        )

    def set_idle(
        self,
        message="System is ready.",
        clear_measurements=True,
    ):
        if clear_measurements:
            self.latest_measurements = []
            self.latest_mzuzu = None
            self.last_measurement_time = None

        self.update(
            running=False,
            mode="idle",
            current_valve=None,
            cycle=0,
            pump=False,
            message=message,
        )

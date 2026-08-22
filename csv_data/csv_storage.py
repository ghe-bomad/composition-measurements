import csv
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATA_DIR = PROJECT_ROOT / "data"


class CSVStorage:

    def __init__(self):
        self.data_folder = DATA_DIR

        self.data_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.headers = [
            "Timestamp",
            "Valve",
            "CO2",
            "CH4",
            "O2",
            "H2S",
            "CO",
            "NH3",
            "H2S_Mzuzu",
            "H2S_Temperature",
        ]

        self.file = None
        self.writer = None
        self.current_date = None
        self.filepath = None

    def _open_file_for_today(self):
        now = datetime.now()

        today = now.strftime(
            "%Y-%m-%d"
        )

        if (
            self.file is not None
            and self.current_date == today
        ):
            return

        self.close()

        day_folder = (
            self.data_folder
            / today
        )

        day_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = now.strftime(
            "%Y-%m-%d_%H-%M-%S.csv"
        )

        self.filepath = (
            day_folder
            / filename
        )

        self.file = open(
            self.filepath,
            "w",
            newline="",
            encoding="utf-8",
        )

        self.writer = csv.DictWriter(
            self.file,
            fieldnames=self.headers,
        )

        self.writer.writeheader()
        self.file.flush()

        self.current_date = today

        print(
            "CSV file created: "
            f"{self.filepath}"
        )

    def save_measurement(
        self,
        valve,
        drager_measurements,
        mzuzu_measurement,
    ):
        self._open_file_for_today()

        row = {
            "Timestamp":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            "Valve": valve,
            "CO2": "",
            "CH4": "",
            "O2": "",
            "H2S": "",
            "CO": "",
            "NH3": "",
            "H2S_Mzuzu": "",
            "H2S_Temperature": "",
        }

        for measurement in drager_measurements:
            gas = measurement.get(
                "gas"
            )

            if gas in row:
                row[gas] = (
                    measurement.get(
                        "value",
                        "",
                    )
                )

        if mzuzu_measurement:
            row["H2S_Mzuzu"] = (
                mzuzu_measurement.get(
                    "h2s_ppm",
                    "",
                )
            )

            row[
                "H2S_Temperature"
            ] = (
                mzuzu_measurement.get(
                    "temperature_c",
                    "",
                )
            )

        self.writer.writerow(
            row
        )

        self.file.flush()

    def close(self):
        if self.file is not None:
            try:
                self.file.flush()
            except Exception:
                pass

            try:
                self.file.close()
            except Exception:
                pass

        self.file = None
        self.writer = None
        self.current_date = None

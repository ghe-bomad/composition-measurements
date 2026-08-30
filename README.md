# Dräger X-am 8000 Valve Monitoring System

## Contents

- [1. Project overview](#1-project-overview)
- [2. Project structure](#2-project-structure)
- [3. main.py — measurement engine](#3-mainpy--measurement-engine)
- [4. dashboard.py - operator interface](#4-dashboardpy--operator-interface)
- [5. Measurement cycle](#5-Measurement-cycle)
- [6. Data storage](#6-Data-storage)
- [7. Settings](#7-Settings)
- [8. Logs and runtime status](#8-logs-and-runtime-status)
- [9. GitHub Backup](#9-GitHub-Backup)
- [10. Systemd services ](#10-Systemd-services)
- [11. Useful commands](#11-Useful-commands)
- [12. Development checks](#12-Development-checks)
- [13. Troubleshooting](#13-Troubleshooting)

## 1. Project overview

This project is a Raspberry Pi 5 based gas-monitoring and valve-control system.

The system automatically measures gas from several sampling lines. A six-channel relay board opens and closes the valves that select the active gas line. A Dräger X-am 8000 measures the main gas components, while an additional Mzuzu H₂S sensor provides a second higher resolution H₂S measurement.

The Raspberry Pi stores all measurements locally as CSV files. A web dashboard is used to start and stop measurements, view live values, change measurement settings, download recorded data, and check battery and system information.

An X1205 UPS supplies backup power during a power failure and monitors the battery level. If the battery becomes critically low, the measurement process is stopped safely before the Raspberry Pi shuts down.

Measurement data and the system event log are also backed up automatically to GitHub every 12 hours.

The system is designed for long unattended measurement periods. It can run continuously for hours or days while writing data to disk during the measurement.

---

## 2. Project structure

```text
Drager_XAM8000_valves/
│
├── main.py
├── dashboard.py
│
├── hardware/
├── csv_data/
├── settings/
├── system_logs/
├── github/
├── services/
├── data/
├── drager_xam_8000/
├── h2s-rpi/
├── .streamlit/
└── .venv/
```

### Root files

#### `main.py`
The measurement engine. It performs the complete valve and sensor measurement sequence.

#### `dashboard.py`
The Streamlit web interface. It is the main user interface for operating and monitoring the system.

---

### `hardware/`

Contains the project-specific hardware interfaces.

This folder connects the measurement logic to the physical devices.

Important files include:

```text
hardware/valves.py
hardware/PiRelay6.py
hardware/drager_control.py
hardware/h2s_control.py
hardware/ups_control.py
hardware/ups_monitor.py
```

The folder is responsible for:

- opening and closing valves,
- controlling the six-channel relay board,
- communicating with the Dräger X-am 8000,
- reading the additional H₂S sensor,
- reading UPS battery information,
- safely shutting the system down at critical battery level.

See `hardware/README.md` for detailed explanations.

---

### `csv_data/`

Contains the code responsible for writing measurement results to CSV files.

The main file is:

```text
csv_data/csv_storage.py
```

It receives measurement values from `main.py` and stores them below `data/`.

See `csv_data/README.md`.

---

### `settings/`

Contains all measurement configuration files and the code used to read and write them.

```text
settings/config.json
settings/default_config.json
settings/config_storage.py
```

The current settings and the standard/default settings are intentionally stored separately.

See the detailed explanation in the Settings section below and in `settings/README.md`.

---

### `system_logs/`

Contains live system-status files and persistent system-event information.

Examples:

```text
system_logs/status.json
system_logs/ups_status.json
system_logs/ups_history.json
system_logs/system_events.csv
system_logs/system_state.json
```

This folder allows separate processes such as `main.py`, the UPS monitor, and the dashboard to exchange system status without requiring a database.

See `system_logs/README.md`.

---

### `github/`

Contains the automatic GitHub backup script.

```text
github/github_backup.py
```

Only measurement data and the system event log are copied to the separate Git backup repository.

See `github/README.md`.

---

### `services/`

Contains project-level code and reference files related to Linux `systemd` services.

```text
services/service_controller.py
services/gasmonitor.service
```

`service_controller.py` is used by the dashboard to start and stop the measurement service.

The actual active `systemd` service files are normally installed under:

```text
/etc/systemd/system/
```

See the Systemd section below and `services/README.md`.

---

### `data/`

Contains all recorded measurement CSV files.

Files are grouped by date:

```text
data/
├── 2026-08-17/
│   ├── 2026-08-17_15-23-11.csv
│   └── ...
├── 2026-08-18/
│   └── ...
└── ...
```

See `data/README.md`.

---

### `drager_xam_8000/`

External library used to communicate with the Dräger X-am 8000.

This folder is kept intact because it is an external codebase.

The project-specific interface to this library is:

```text
hardware/drager_control.py
```

---

### `h2s-rpi/`

External reader package for the additional Mzuzu H₂S sensor.

This folder is also kept intact.

The project-specific interface to this library is:

```text
hardware/h2s_control.py
```

---

### `.streamlit/`

Contains Streamlit configuration.

The main file is:

```text
.streamlit/config.toml
```

It is read automatically when the dashboard is started.

---

### `.venv/`

Python virtual environment used by the project.

It contains installed Python packages and should not be edited manually.

---

## 3. `main.py` — measurement engine

`main.py` is the core measurement program.

It is responsible for the complete physical measurement sequence.

### Main responsibilities

When started, `main.py`:

- loads the current measurement settings,
- controls the valve sequence and sensor readings,
- stores each measurement in CSV files,
- updates the dashboard status and handles shutdowns safely if the service stops or an error occurs.

### Input files and modules used by `main.py`

#### Settings input

```text
settings/config.json
```

Loaded through:

```text
settings/config_storage.py
```

This determines values such as:

- measurement valves,
- flush valve,
- measurement duration,
- measurement interval,
- flush duration,
- pause between cycles,
- pump startup delay,
- pump flow,
- continuous mode.

---

#### Valve control

```text
hardware/valves.py
```

which internally uses:

```text
hardware/PiRelay6.py
```

---

#### Dräger control

```text
hardware/drager_control.py
```

which internally uses:

```text
drager_xam_8000/
```

---

#### Additional H₂S sensor

```text
hardware/h2s_control.py
```

which internally uses:

```text
h2s-rpi/
```

---

#### CSV output

```text
csv_data/csv_storage.py
```

which writes to:

```text
data/
```

---

#### Live status output

```text
system_logs/status_storage.py
```

which writes:

```text
system_logs/status.json
```

The dashboard reads this file to display the current measurement state and the latest gas values.

### How `main.py` is normally started

`main.py` is normally started through:

```text
gasmonitor.service
```

The operator presses START in the dashboard. The dashboard uses `services/service_controller.py`, which tells `systemd` to start `gasmonitor.service`. The service then launches `main.py`.

This separation is intentional and makes the measurement process independent from the dashboard itself.

---

## 4. `dashboard.py` — operator interface

`dashboard.py` is the main user interface.

It runs as a Streamlit web application.

The dashboard does not directly open valves or communicate with sensors. Instead, it reads status files and controls the measurement service.

### Main functions

The dashboard allows the user to:

- start measurement,
- stop measurement,
- see whether the system is running,
- see the active valve,
- see the pump state,
- see the current cycle,
- see the latest Dräger measurements,
- see the latest Mzuzu H₂S value,
- see sensor temperature,
- edit measurement settings while the system is stopped,
- restore standard/default settings,
- download measurement CSV data,
- select data by date range,
- download individual source CSV files,
- download consolidated data,
- view UPS battery percentage and voltage,
- view UPS shutdown information,
- view the system event log,
- download the system event log.

### Input files used by `dashboard.py`

#### Current measurement status

```text
system_logs/status.json
```

Provides:

- current valve,
- pump state,
- cycle,
- mode,
- latest gas measurements,
- latest H₂S reading,
- status message,
- last update.

---

#### UPS status

```text
system_logs/ups_status.json
```

Provides:

- battery percentage,
- battery voltage,
- warning state,
- shutdown-pending state,
- UPS message.

---

#### UPS history

```text
system_logs/ups_history.json
```

Provides information about the last UPS-triggered shutdown.

---

#### System state

```text
system_logs/system_state.json
```

Provides information such as:

- last boot,
- last shutdown,
- shutdown reason.

---

#### System event log

```text
system_logs/system_events.csv
```

Displayed in the Battery & System Status tab and available for download.

---

#### Measurement data

```text
data/
```

The dashboard scans all CSV files recursively and can create filtered or consolidated downloads.

---

#### Current and default settings

```text
settings/config.json
settings/default_config.json
```

Accessed through:

```text
settings/config_storage.py
```

---

#### Service control

```text
services/service_controller.py
```

This module starts and stops:

```text
gasmonitor.service
```

### Why the dashboard does not launch `main.py` directly

If the dashboard created a Python subprocess itself, it would be easier to accidentally start multiple copies of the measurement program.

Using `systemd` ensures there is one controlled measurement service with clear process state and logs.

---

## 5. Measurement cycle

A typical measurement cycle is:

```text
START
  ↓
Load settings
  ↓
Close all valves
  ↓
Connect Dräger
  ↓
Connect additional H₂S sensor
  ↓
Start Dräger pump
  ↓
Wait for pump startup delay
  ↓
Open measurement valve
  ↓
Read Dräger values
  ↓
Read additional H₂S value
  ↓
Write measurement to CSV immediately
  ↓
Update dashboard status
  ↓
Repeat measurements until valve duration is complete
  ↓
Close measurement valve
  ↓
Open Valve 6
  ↓
Flush sampling system
  ↓
Read and record Valve 6 data
  ↓
Close Valve 6
  ↓
Continue with next valve
  ↓
Repeat cycle if continuous mode is enabled
```

Valve 6 is also recorded. This allows the operator to check whether the flushing step actually produces clean-air values.

---

## 6. Data storage

Measurement data is stored below:

```text
data/YYYY-MM-DD/
```

Example:

```text
data/
├── 2026-08-17/
│   ├── 2026-08-17_15-23-11.csv
│   └── 2026-08-17_18-58-18.csv
└── 2026-08-18/
    └── 2026-08-18_08-10-15.csv
```

The storage code is:

```text
csv_data/csv_storage.py
```

### Continuous storage

Measurements are written while the system is running.

The system does not wait until the user presses STOP.

After a measurement row is written, the file is flushed to disk. This reduces the amount of data that can be lost after an unexpected interruption.

### Multi-day operation

The system can run continuously for several days.

If the date changes while measurement is active, the storage layer switches to the new day automatically.

---

## 7. Settings

The settings system uses three files.

### `settings/config.json`

This is the **current active configuration**.

These are the settings that will be used the next time the measurement process starts.

The dashboard edits this file indirectly through `config_storage.py`.

Typical values include:

```text
measurement_valves
flush_valve
pump_start_delay_seconds
flush_seconds
measurement_duration_seconds
measurement_interval_seconds
cycle_pause_seconds
continuous_mode
pump_flow
```

---

### `settings/default_config.json`

This contains the **standard configuration**.

It is kept separate from `config.json` so that the standard values are never lost when a user changes the current settings.

The dashboard's "RESTORE DEFAULTS" button copies these standard values back into the active configuration.

This means:

```text
default_config.json = reference / standard values
config.json         = current user-selected values
```

---

### `settings/config_storage.py`

This file contains the Python functions used to read and write the two JSON files.

Typical functions are:

```text
load_config()
save_config()
reset_config_to_defaults()
```

It is used by:

```text
main.py
dashboard.py
```

The reason for having this separate Python module is to avoid duplicating JSON file handling in both programs.

### Why settings cannot be changed during measurement

`main.py` loads the configuration when the measurement process starts.

Changing `config.json` halfway through an active cycle could create confusion because the running process may still be using settings that were loaded earlier.

For this reason, the dashboard disables the settings controls while measurement is active.

---

## 8. Logs and runtime status

System information is stored in:

```text
system_logs/
```

Important files include:

### `status.json`
Live measurement state and latest sensor values.

Written by:

```text
main.py
```

through:

```text
system_logs/status_storage.py
```

Read by:

```text
dashboard.py
```

---

### `ups_status.json`
Current UPS battery state.

Written by:

```text
hardware/ups_monitor.py
```

Read by:

```text
dashboard.py
```

---

### `ups_history.json`
Information about the most recent UPS-triggered shutdown.

---

### `system_events.csv`
Persistent chronological system event log.

This file is:

- displayed in the dashboard,
- downloadable from the dashboard,
- backed up to GitHub.

---

### `system_state.json`
Stores information about the latest boot/shutdown state.

---

## 9. GitHub backup

The GitHub backup is intentionally limited to:

```text
data/
system_logs/system_events.csv
```

The backup code is:

```text
github/github_backup.py
```

It copies these files into a separate local Git repository:

```text
/home/valvescontroller/Desktop/gasmonitor-data-backup
```

The separate repository is used so that source code, runtime JSON files, credentials or other project files cannot accidentally be pushed.

The backup is scheduled every 12 hours.

---

## 10. systemd services

`systemd` is the Linux service manager used by Raspberry Pi OS.

In this project it is used to run important programs in a controlled way.

Instead of manually keeping several terminal windows open, Linux manages the processes.

This provides:

- automatic startup after boot,
- clear running/stopped state,
- automatic restart where configured,
- central log output through `journalctl`,
- safer process control,
- separation between the dashboard and the measurement engine.

### `gasmonitor.service`

Purpose:

```text
Run main.py as the measurement process.
```

The dashboard starts and stops this service.

When START is pressed:

```text
dashboard.py
  ↓
service_controller.py
  ↓
systemctl start gasmonitor.service
  ↓
main.py starts
```

When STOP is pressed:

```text
dashboard.py
  ↓
service_controller.py
  ↓
systemctl stop gasmonitor.service
  ↓
main.py performs safe cleanup and exits
```

---

### `gasmonitor-dashboard.service`

Purpose:

```text
Run dashboard.py as a Streamlit web application.
```

This service allows the dashboard to start automatically when the Raspberry Pi boots.

---

### `ups-monitor.service`

Purpose:

```text
Run hardware/ups_monitor.py continuously.
```

It checks battery status independently from the measurement service.

This is important because the UPS must still be monitored even if measurement is stopped.

---

### `gasmonitor-github-backup.service`

Purpose:

```text
Run one GitHub backup operation.
```

It starts `github/github_backup.py`, performs the backup and then exits.

---

### `gasmonitor-github-backup.timer`

Purpose:

```text
Start gasmonitor-github-backup.service automatically every 12 hours.
```

The timer schedules the job. The service performs the actual job.

---

### `system-event-boot.service`

Purpose:

```text
Write a system boot event to the logging system.
```

---

### `system-event-shutdown.service`

Purpose:

```text
Write a shutdown/reboot event before Linux shuts down.
```

---

## 11. Useful commands

All commands below are intended to be run in a Raspberry Pi terminal.

### Check whether the measurement service is running

```bash
sudo systemctl status gasmonitor --no-pager
```

Purpose:

Shows whether `main.py` is currently running as the measurement service.

Expected when measurement is active:

```text
Active: active (running)
```

Expected when measurement is stopped:

```text
Active: inactive (dead)
```

---

### View recent measurement-service logs

```bash
sudo journalctl -u gasmonitor -n 100 --no-pager
```

Purpose:

Shows the last 100 log lines from the measurement process.

Use this when:

- measurement stops unexpectedly,
- a Dräger connection error occurs,
- an I²C error occurs,
- a Python exception occurs.

Expected during normal measurement:

log messages showing valve changes, sensor values and normal operation.

---

### Check dashboard service

```bash
sudo systemctl status gasmonitor-dashboard --no-pager
```

Purpose:

Checks whether the Streamlit dashboard is running.

Expected:

```text
Active: active (running)
```

---

### Restart the dashboard

```bash
sudo systemctl restart gasmonitor-dashboard
```

Purpose:

Restarts Streamlit after changes to `dashboard.py` or if the dashboard stops responding.

After the command, reload the dashboard page in the browser.

---

### Check the UPS monitor

```bash
sudo systemctl status ups-monitor --no-pager
```

Purpose:

Checks whether battery supervision is running.

Expected:

```text
Active: active (running)
```

---

### View UPS monitor logs

```bash
sudo journalctl -u ups-monitor -n 100 --no-pager
```

Purpose:

Shows battery readings and UPS shutdown messages.

During normal operation, repeated battery percentage and voltage readings should appear.

---

### Check automatic GitHub backup schedule

```bash
systemctl list-timers --all | grep gasmonitor-github
```

Purpose:

Shows when the next automatic GitHub backup is scheduled.

Expected:

A line containing `gasmonitor-github-backup.timer` and a future NEXT execution time.

---

### Manually run the GitHub backup

```bash
cd ~/Desktop/Drager_XAM8000_valves
source .venv/bin/activate
python3 -m github.github_backup
```

Purpose:

Tests the backup without waiting for the 12-hour timer.

Possible normal output:

```text
Preparing GitHub data backup...
No new data to push.
```

or:

```text
Preparing GitHub data backup...
Changes committed.
GitHub backup completed successfully.
```

---

### Check I²C devices

```bash
i2cdetect -y 1
```

Purpose:

Checks whether the UPS and additional H₂S sensor are visible on the Raspberry Pi I²C bus.

Expected addresses:

```text
0x36  X1205 fuel gauge
0x48  LMP91002
0x49  ADS1115
```

---

## 12. Development checks

These checks are useful after Python files are edited or moved.

They are not part of normal measurement operation.

### Python syntax check

```bash
cd ~/Desktop/Drager_XAM8000_valves
source .venv/bin/activate

python3 -m py_compile \
main.py \
dashboard.py \
hardware/*.py \
csv_data/*.py \
settings/*.py \
system_logs/*.py \
github/*.py \
services/*.py
```

Purpose:

Python reads and compiles the files without starting the measurement system.

This catches syntax errors such as:

- missing brackets,
- incorrect indentation,
- invalid Python syntax.

Expected result:

```text
no output
```

If no message appears, the syntax check succeeded.

---

### Import check

```bash
python3 -c "
from hardware.valves import ValveController
from hardware.drager_control import DragerController
from hardware.h2s_control import H2SController
from hardware.ups_control import UPSController
from csv_data.csv_storage import CSVStorage
from settings.config_storage import load_config
from system_logs.status_storage import StatusStorage
from services.service_controller import is_service_active
print('All imports OK')
"
```

Purpose:

Checks whether the new folder structure and Python imports are correct.

This is especially useful after moving files into new subfolders.

Expected result:

```text
All imports OK
```

If an `ImportError` or `ModuleNotFoundError` appears, one of the module paths is incorrect.

---

## 13. Troubleshooting

### Error 121 — `Remote I/O error`

Example:

```text
OSError: [Errno 121] Remote I/O error
```

In this project this normally indicates that an I²C device stopped responding.

The additional H₂S sensor is the first thing to check.

Run:

```bash
i2cdetect -y 1
```

Expected:

```text
0x36
0x48
0x49
```

If `0x48` and `0x49` are missing, the H₂S sensor is no longer connected correctly.

Check the physical cables between the sensor and the Raspberry Pi:

```text
5 V
GND
SDA
SCL
```

In practice, this error has normally occurred when one of these sensor wires became loose or fell out of the connector.

Push each connector in firmly and then run:

```bash
i2cdetect -y 1
```

again.

Only restart measurement once `0x48` and `0x49` are visible again.

---

### Dräger is not found

Check USB devices:

```bash
lsusb
```

Check serial devices:

```bash
ls /dev/ttyUSB*
```

The Dräger DIRA adapter must be visible before the measurement service can communicate with the detector.

---

### Dashboard does not load

Check:

```bash
sudo systemctl status gasmonitor-dashboard --no-pager
```

Then inspect logs:

```bash
sudo journalctl -u gasmonitor-dashboard -n 100 --no-pager
```

---

### Measurement stops unexpectedly

Check:

```bash
sudo journalctl -u gasmonitor -n 100 --no-pager
```

The final lines normally show which sensor, hardware interface or Python function caused the stop.

---

### UPS status is not updating

Check:

```bash
sudo systemctl status ups-monitor --no-pager
```

Then:

```bash
sudo journalctl -u ups-monitor -n 100 --no-pager
```

Also inspect:

```bash
cat system_logs/ups_status.json
```

The `last_update` field should change regularly while the UPS monitor is running.

---

## 14. Safe shutdown behaviour

Safe shutdown is important because the project controls physical valves and continuously writes measurement files.

If `main.py` stops normally or because of an exception, it should:

1. close all valves,
2. stop the Dräger pump,
3. disconnect from the Dräger,
4. disconnect the additional H₂S sensor,
5. flush and close the active CSV file,
6. update the live system status.

If the UPS reaches the critical battery threshold:

1. `hardware/ups_monitor.py` detects the critical level,
2. it requests `gasmonitor.service` to stop,
3. it waits for the measurement process to finish its cleanup,
4. it records the UPS shutdown event,
5. it requests Raspberry Pi poweroff.


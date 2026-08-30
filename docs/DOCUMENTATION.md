# Detailed Project Documentation

## Contents

1. [Purpose of this document](#1-purpose-of-this-document)
2. [System architecture](#2-system-architecture)
3. [main.py](#3-mainpy)
4. [dashboard.py](#4-dashboardpy)
5. [hardware](#5-hardware)
6. [csv_data](#6-csv_data)
7. [settings](#7-settings)
8. [system_logs](#8-system_logs)
9. [github](#9-github)
10. [services and systemd](#10-services-and-systemd)
11. [data](#11-data)
12. [External libraries](#12-external-libraries)
13. [Measurement flow](#13-measurement-flow)
14. [Live status and file exchange](#14-live-status-and-file-exchange)
15. [Useful commands](#15-useful-commands)
16. [Development checks](#16-development-checks)
17. [Troubleshooting](#17-troubleshooting)
18. [Safe shutdown behaviour](#18-safe-shutdown-behaviour)
19. [Notes for future changes](#19-notes-for-future-changes)

---

## 1. Purpose of this document

This file contains the detailed technical documentation for the gas-monitoring project.

The main `README.md` gives a short overview of the system. This document explains how the individual Python files, folders, services and data files work together.

It is intended for someone who opens the repository for the first time and needs enough context to understand or modify the code.

---

## 2. System architecture

The project is split into several independent parts.

```text
dashboard.py
    │
    ├── reads current status
    ├── reads recorded data
    ├── reads settings
    └── starts/stops measurement
               │
               ▼
services/service_controller.py
               │
               ▼
       gasmonitor.service
               │
               ▼
            main.py
               │
      ┌────────┼────────┐
      │        │        │
      ▼        ▼        ▼
   valves    Dräger    H₂S
      │        │        │
      ▼        ▼        ▼
 PiRelay 6   X-am     Mzuzu

main.py
   ├──► csv_data/csv_storage.py ──► data/
   └──► system_logs/status_storage.py ──► status.json

hardware/ups_monitor.py
   ├──► hardware/ups_control.py
   ├──► ups_status.json
   ├──► ups_history.json
   └──► system_events.csv

github/github_backup.py
   ├──► data/
   └──► system_events.csv
```

The design keeps hardware access out of the dashboard and keeps the user interface out of the measurement loop.

---

## 3. `main.py`

### Role

`main.py` is the measurement engine.

It contains the sequence that controls valves, starts the Dräger pump, reads sensors, stores measurements and performs cleanup.

It is normally launched by:

```text
gasmonitor.service
```

rather than by the dashboard directly.

### Inputs

#### Current configuration

```text
settings/config.json
```

Loaded through:

```text
settings/config_storage.py
```

The configuration contains values such as:

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

#### Valve interface

```text
hardware/valves.py
```

#### Dräger interface

```text
hardware/drager_control.py
```

#### Additional H₂S interface

```text
hardware/h2s_control.py
```

### Outputs

#### Measurement data

Written through:

```text
csv_data/csv_storage.py
```

to:

```text
data/
```

#### Live status

Written through:

```text
system_logs/status_storage.py
```

to:

```text
system_logs/status.json
```

### Main sequence

At startup, `main.py`:

1. loads the current configuration,
2. initializes controllers,
3. closes all valves,
4. connects to the Dräger,
5. connects to the H₂S sensor,
6. starts the pump,
7. waits for the configured pump startup delay.

It then loops through the configured measurement valves.

For each valve, it:

1. opens the selected valve,
2. reads the Dräger measurements,
3. reads the additional H₂S sensor,
4. writes a combined row to CSV,
5. updates `status.json`,
6. repeats the measurement at the configured interval,
7. closes the valve after the configured duration.

After each measurement valve, Valve 6 is opened for flushing.

Valve 6 measurements are stored as well.

### Why `main.py` does not contain low-level hardware code

Direct GPIO, serial and I²C details are kept in `hardware/`.

That makes the measurement sequence easier to read and allows individual hardware interfaces to be changed without rewriting the whole measurement loop.

### Cleanup

When the process stops, it should leave the physical system in a safe state.

Cleanup includes:

- closing all valves,
- stopping the Dräger pump,
- disconnecting the Dräger,
- disconnecting the H₂S sensor,
- closing/flushing the CSV file,
- updating the status file.

---

## 4. `dashboard.py`

### Role

`dashboard.py` is the Streamlit web interface.

It is the main user-facing part of the system.

The dashboard does not directly control the valves or sensors. It reads files produced by other parts of the project and controls the measurement process through `systemd`.

### Main functions

The dashboard provides:

- START and STOP controls,
- current system status,
- active valve,
- pump state,
- current cycle,
- latest gas values,
- current settings,
- Restore Defaults,
- CSV download,
- date-range filtering,
- battery status,
- system state,
- UPS shutdown information,
- system event log download.

### Inputs

#### Current measurement status

```text
system_logs/status.json
```

Used for:

- current valve,
- running/idle state,
- pump state,
- cycle,
- latest Dräger values,
- latest Mzuzu values,
- status message,
- timestamps.

#### Current settings

```text
settings/config.json
```

Accessed through:

```text
settings/config_storage.py
```

#### Default settings

```text
settings/default_config.json
```

Used when the operator selects Restore Defaults.

#### UPS status

```text
system_logs/ups_status.json
```

Used for battery percentage, voltage, warning state and shutdown state.

#### UPS history

```text
system_logs/ups_history.json
```

Used to show information about the most recent UPS-triggered shutdown.

#### System state

```text
system_logs/system_state.json
```

Used for boot/shutdown information.

#### System event log

```text
system_logs/system_events.csv
```

Displayed in the Battery & System Status section and available for download.

#### Measurement data

```text
data/
```

The dashboard scans CSV files below this directory and can create filtered or consolidated downloads.

### Service control

The dashboard uses:

```text
services/service_controller.py
```

to start and stop:

```text
gasmonitor.service
```

This prevents the dashboard from launching duplicate measurement processes.

### Settings while measurement is running

The dashboard disables settings while the measurement service is active.

This is intentional. `main.py` loads settings when it starts, so changing the configuration during a running cycle could make the displayed settings differ from the values currently being used.

---

## 5. `hardware/`

The `hardware/` folder contains the project-specific hardware interfaces.

```text
hardware/
├── __init__.py
├── valves.py
├── PiRelay6.py
├── drager_control.py
├── h2s_control.py
├── ups_control.py
└── ups_monitor.py
```

### `valves.py`

Provides the project-level valve interface. It converts valve numbers into relay actions and provides functions for opening one valve, closing one valve and closing all valves.

Used by:

```text
main.py
```

Uses:

```text
hardware/PiRelay6.py
```

### `PiRelay6.py`

Low-level driver for the SB Components PiRelay 6-channel board.

Current physical pin mapping:

```text
Relay 1 → physical pin 29 → GPIO5
Relay 2 → physical pin 31 → GPIO6
Relay 3 → physical pin 33 → GPIO13
Relay 4 → physical pin 35 → GPIO19
Relay 5 → physical pin 37 → GPIO26
Relay 6 → physical pin 40 → GPIO21
```

This file is used by `hardware/valves.py`.

GPIO6 is already occupied by Relay 2 in this design.

### `drager_control.py`

Project-specific wrapper for the Dräger library.

It provides a smaller interface for connecting, disconnecting, pump control and reading gas measurements.

Used by:

```text
main.py
```

Uses:

```text
drager_xam_8000/
```

### `h2s_control.py`

Project-specific wrapper for the additional H₂S sensor.

The sensor PCB uses:

```text
0x48  LMP91002
0x49  ADS1115
```

The wrapper opens the I²C bus, configures the sensor and returns values in a form that `main.py` can use.

Used by:

```text
main.py
```

Uses:

```text
h2s-rpi/
```

### `ups_control.py`

Low-level interface for X1205 battery information.

The UPS fuel-gauge interface appears at:

```text
0x36
```

It provides battery percentage and voltage.

Used by:

```text
hardware/ups_monitor.py
```

### `ups_monitor.py`

Long-running battery supervisor.

It reads battery information, writes current UPS status, checks warning/shutdown thresholds, waits for consecutive critical readings, stops `gasmonitor.service`, stores UPS shutdown information and requests Raspberry Pi poweroff.

Started by:

```text
ups-monitor.service
```

Current production thresholds are approximately:

```text
Warning percentage: 25 %
Shutdown percentage: 15 %
Warning voltage: 3.40 V
Shutdown voltage: 3.25 V
```

Temporary test thresholds should not be left enabled in normal operation.

---

## 6. `csv_data/`

```text
csv_data/
├── __init__.py
└── csv_storage.py
```

### `csv_storage.py`

Responsible for persistent measurement storage.

Used by:

```text
main.py
```

Typical stored columns:

```text
Timestamp
Valve
CO2
CH4
O2
H2S
CO
NH3
H2S_Mzuzu
H2S_Temperature
```

Files are stored below:

```text
data/YYYY-MM-DD/
```

The file is flushed after writes. This means measurements are already on disk while the system is still running.

If the date changes during a measurement, storage switches to a new daily file/location.

The stored files are later used by:

```text
dashboard.py
github/github_backup.py
```

---

## 7. `settings/`

```text
settings/
├── __init__.py
├── config.json
├── default_config.json
└── config_storage.py
```

### `config.json`

Contains the current active settings. These are the values used when the next measurement process starts.

### `default_config.json`

Contains the reference/default values.

It is kept separate so the standard settings remain available after the operator changes the active configuration.

The Restore Defaults function uses this file.

### `config_storage.py`

Contains shared configuration functions, for example:

```text
load_config()
save_config()
reset_config_to_defaults()
```

Used by:

```text
main.py
dashboard.py
```

The separate storage module prevents both files from implementing their own JSON handling.

---

## 8. `system_logs/`

```text
system_logs/
├── __init__.py
├── status_storage.py
├── status.json
├── system_logger.py
├── system_events.csv
├── system_state.json
├── log_shutdown.py
├── ups_status.json
└── ups_history.json
```

### `status_storage.py`

Writes live measurement information to `system_logs/status.json`.

Used by `main.py` and read by `dashboard.py`.

### `status.json`

Live measurement state. It is not a historical measurement file.

Typical content includes current valve, pump state, cycle, status message, latest sensor values and update time.

### `system_logger.py`

Handles persistent system events and related system-state information.

### `system_events.csv`

Persistent chronological system event log.

Used by:

```text
dashboard.py
github/github_backup.py
```

This is the only file from `system_logs/` included in the automatic GitHub data backup.

### `system_state.json`

Stores the latest known system lifecycle state, such as last boot and last shutdown information.

Read by:

```text
dashboard.py
```

### `log_shutdown.py`

Small entry point used when Linux shuts down or reboots. It records the shutdown through `system_logger.py`.

### `ups_status.json`

Live UPS state.

Written by:

```text
hardware/ups_monitor.py
```

Read by:

```text
dashboard.py
```

### `ups_history.json`

Stores information about the most recent UPS-triggered shutdown.

Written by `hardware/ups_monitor.py` and read by `dashboard.py`.

---

## 9. `github/`

```text
github/
├── __init__.py
└── github_backup.py
```

### `github_backup.py`

Creates the automatic data backup.

The script backs up only:

```text
data/
system_logs/system_events.csv
```

It copies these into the separate local Git repository:

```text
/home/valvescontroller/Desktop/gasmonitor-data-backup
```

The backup repository is separate from the source-code repository on purpose.

Typical backup sequence:

```text
copy selected project data
        ↓
git add
        ↓
check whether anything changed
        ↓
commit if needed
        ↓
git push origin main
```

If no data changed, no unnecessary commit is created.

---

## 10. `services/` and systemd

```text
services/
├── __init__.py
├── service_controller.py
└── gasmonitor.service
```

### What is systemd?

`systemd` is the Linux service manager used by Raspberry Pi OS.

It starts, stops and monitors background programs. The project uses it so important processes do not depend on an open terminal window.

The active installed service files are normally stored under:

```text
/etc/systemd/system/
```

### `service_controller.py`

Used by:

```text
dashboard.py
```

Provides functions such as:

```text
start_service()
stop_service()
restart_service()
is_service_active()
```

It controls:

```text
gasmonitor.service
```

### `gasmonitor.service`

Purpose:

```text
launch main.py as the managed measurement process
```

The service is not the measurement code itself. It tells Linux which working directory, Python environment and Python file to run.

The measurement service is not intended to start automatically after every reboot. The operator starts measurement from the dashboard.

### `gasmonitor-dashboard.service`

Runs `dashboard.py` through Streamlit and starts automatically so the dashboard becomes available after boot.

### `ups-monitor.service`

Runs:

```text
python -m hardware.ups_monitor
```

It stays active independently from measurement.

### `gasmonitor-github-backup.service`

Runs one execution of:

```text
python -m github.github_backup
```

and exits when the backup is complete.

### `gasmonitor-github-backup.timer`

Schedules the backup service.

Current intended schedule:

```text
06:30
18:30
```

with:

```text
Persistent=true
```

### `system-event-boot.service`

Records a boot event.

### `system-event-shutdown.service`

Records operating-system shutdown/reboot information.

---

## 11. `data/`

The `data/` directory contains measurement CSV files.

Example:

```text
data/
├── 2026-08-17/
│   ├── 2026-08-17_15-23-11.csv
│   └── 2026-08-17_18-58-18.csv
└── 2026-08-18/
    └── 2026-08-18_07-02-44.csv
```

Files are created by:

```text
csv_data/csv_storage.py
```

Used by:

```text
dashboard.py
github/github_backup.py
```

This directory should be treated as measurement data storage, not as general project storage.

---

## 12. External libraries

### `drager_xam_8000/`

External library for communication with the Dräger X-am 8000.

Project integration path:

```text
main.py
   ↓
hardware/drager_control.py
   ↓
drager_xam_8000/
```

The external library should generally remain intact.

### `h2s-rpi/`

External package for the Mzuzu H₂S sensor.

Project integration path:

```text
main.py
   ↓
hardware/h2s_control.py
   ↓
h2s-rpi/
```

Expected I²C devices:

```text
0x48  LMP91002
0x49  ADS1115
```

Standalone self-test:

```bash
python -m h2s_reader --selftest
```

---

## 13. Measurement flow

A full cycle can be summarized as:

```text
Load configuration
       ↓
Initialize hardware
       ↓
Start pump
       ↓
Measurement Valve 1
       ↓
Valve 6 flush
       ↓
Measurement Valve 2
       ↓
Valve 6 flush
       ↓
...
       ↓
Measurement Valve 5
       ↓
Valve 6 flush
       ↓
Next cycle
```

During every active valve period:

```text
Dräger reading
       +
Mzuzu H₂S reading
       ↓
combined measurement
       ↓
CSVStorage
       ↓
data/YYYY-MM-DD/*.csv
```

The latest values are also written into `status.json` for the dashboard.

---

## 14. Live status and file exchange

The dashboard and measurement process are separate programs.

They exchange information through files rather than direct function calls.

### Measurement status

```text
main.py
   ↓
status_storage.py
   ↓
status.json
   ↓
dashboard.py
```

### UPS status

```text
ups_monitor.py
   ↓
ups_status.json
   ↓
dashboard.py
```

This approach keeps the dashboard independent from the hardware process. If the dashboard is restarted, the measurement process can continue running.

---

## 15. Useful commands

### Check measurement service

```bash
sudo systemctl status gasmonitor --no-pager
```

Purpose: check whether the measurement process is active.

Expected while running:

```text
Active: active (running)
```

Expected while stopped:

```text
Active: inactive (dead)
```

### View measurement logs

```bash
sudo journalctl -u gasmonitor -n 100 --no-pager
```

Purpose: show the most recent 100 log lines from the measurement service.

Use this after an unexpected stop or sensor error.

### Check dashboard service

```bash
sudo systemctl status gasmonitor-dashboard --no-pager
```

Expected:

```text
Active: active (running)
```

### Restart dashboard

```bash
sudo systemctl restart gasmonitor-dashboard
```

Use this after changing dashboard code or if Streamlit stops responding.

### Check UPS monitor

```bash
sudo systemctl status ups-monitor --no-pager
```

Expected:

```text
Active: active (running)
```

### View UPS logs

```bash
sudo journalctl -u ups-monitor -n 100 --no-pager
```

Use this to inspect battery readings or shutdown decisions.

### Check GitHub backup timer

```bash
systemctl list-timers --all | grep gasmonitor-github
```

Expected: a line containing `gasmonitor-github-backup.timer` and the next scheduled run.

### Manual GitHub data backup

```bash
cd ~/Desktop/Drager_XAM8000_valves
source .venv/bin/activate
python3 -m github.github_backup
```

Possible normal output:

```text
Preparing GitHub data backup...
No new data to push.
```

or a successful commit/push message.

### Check I²C devices

```bash
i2cdetect -y 1
```

Expected:

```text
0x36
0x48
0x49
```

---

## 16. Development checks

These checks are useful after code is edited or files are moved. They are not required during normal system operation.

### Syntax check

```bash
cd ~/Desktop/Drager_XAM8000_valves
source .venv/bin/activate

python3 -m py_compile main.py dashboard.py hardware/*.py csv_data/*.py settings/*.py system_logs/*.py github/*.py services/*.py
```

Purpose: check Python syntax without starting measurement.

Expected result:

```text
no output
```

No output means the syntax check passed.

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

Purpose: check that package paths and imports still work after files are reorganized.

Expected:

```text
All imports OK
```

---

## 17. Troubleshooting

### `Remote I/O error 121`

Example:

```text
OSError: [Errno 121] Remote I/O error
```

This normally means an I²C device is not responding.

Run:

```bash
i2cdetect -y 1
```

Expected:

```text
0x36  X1205
0x48  LMP91002
0x49  ADS1115
```

If `0x48` and `0x49` are missing, check the cables between the H₂S sensor and the Raspberry Pi:

```text
5 V
GND
SDA
SCL
```

In this system, Error 121 has normally appeared when one of the H₂S sensor wires became loose or fell out of the connector.

Reconnect the cables firmly and run `i2cdetect -y 1` again. Only restart measurement once `0x48` and `0x49` are visible.

### Dräger is not found

Check:

```bash
lsusb
```

Then:

```bash
ls /dev/ttyUSB*
```

The Dräger DIRA adapter must be available before `main.py` can communicate with the detector.

If the USB device appears but `/dev/ttyUSB0` is missing, check the USB serial driver/device mapping.

### Measurement stops unexpectedly

Run:

```bash
sudo journalctl -u gasmonitor -n 100 --no-pager
```

The final lines usually show whether the failure came from Dräger communication, H₂S I²C communication, valve control or Python code.

### Dashboard does not load

Check:

```bash
sudo systemctl status gasmonitor-dashboard --no-pager
```

Then:

```bash
sudo journalctl -u gasmonitor-dashboard -n 100 --no-pager
```

### UPS status does not update

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
cat ~/Desktop/Drager_XAM8000_valves/system_logs/ups_status.json
```

The update timestamp should change regularly.

---

## 18. Safe shutdown behaviour

Safe shutdown is important because the Raspberry Pi controls physical valves and writes measurement data continuously.

### Normal measurement stop

When `main.py` exits, it should:

1. close all valves,
2. stop the Dräger pump,
3. disconnect from the Dräger,
4. disconnect the additional H₂S sensor,
5. close the CSV file,
6. update live status.

### Critical UPS battery

When the battery reaches the shutdown threshold:

```text
ups_monitor.py
       ↓
stop gasmonitor.service
       ↓
wait for main.py cleanup
       ↓
save UPS history
       ↓
write shutdown event
       ↓
systemctl poweroff
```

The UPS monitor and measurement process are separate so the battery can still be supervised even when no measurement is active.

---

## 19. Notes for future changes

Keep the following separation where possible:

```text
dashboard.py
    user interface

main.py
    measurement sequence

hardware/
    hardware-specific code

csv_data/
    measurement storage

settings/
    configuration handling

system_logs/
    live state and event history

github/
    external data backup

services/
    process control
```

If files are moved, check both Python import paths and installed systemd `ExecStart` / `ExecStop` paths.

The external folders:

```text
drager_xam_8000/
h2s-rpi/
```

should generally remain recognizable as external codebases rather than being reorganized together with the project-specific modules.

# Detailed Project Documentation

## Contents

1. [main.py](#1-mainpy)
2. [dashboard.py](#2-dashboardpy)
3. [hardware](#3-hardware)
4. [csv_data](#4-csv_data)
5. [settings](#5-settings)
6. [system_logs](#6-system_logs)
7. [github](#7-github)
8. [services and systemd](#8-services-and-systemd)
9. [data](#9-data)
10. [External libraries](#10-external-libraries)
11. [How a measurement run works](#11-how-a-measurement-run-works)
12. [How the dashboard gets its information](#12-how-the-dashboard-gets-its-information)
13. [Battery monitoring and safe shutdown](#13-battery-monitoring-and-safe-shutdown)
14. [Automatic GitHub backup](#14-automatic-github-backup)
15. [Useful commands](#15-useful-commands)
16. [Checks after changing the code](#16-checks-after-changing-the-code)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. `main.py`

`main.py` is the central measurement program. It contains the sequence that is followed whenever a measurement is started. It does not contain all hardware details itself. Instead, it uses the smaller modules in the other folders. This keeps the measurement sequence readable and makes it easier to change one part of the system without having to rewrite everything else.

When `main.py` starts, it first loads the measurement settings from `settings/config.json`. It does not read the JSON file directly. The file `settings/config_storage.py` is responsible for loading and checking the settings. This means that both `main.py` and the dashboard use the same configuration handling.

The settings tell `main.py`, for example, which valves should be measured, which valve is used for flushing, how long a valve should be measured, how often a new sensor reading should be taken, how long the system should flush and whether the measurement should continue automatically with another cycle.

After loading the settings, `main.py` prepares the hardware. Valve control is handled through `hardware/valves.py`. The Dräger is handled through `hardware/drager_control.py`, and the additional H₂S sensor is handled through `hardware/h2s_control.py`. `main.py` therefore only needs to tell these modules what it wants to do, for example open a valve, start the pump or read the current sensor values.

The Dräger communication code in `hardware/drager_control.py` uses the external library in `drager_xam_8000/`. The additional H₂S sensor code in `hardware/h2s_control.py` uses the external package in `h2s-rpi/`. These external folders contain the lower-level communication code, while the files in `hardware/` provide a simpler interface for the rest of this project.

Once the hardware is ready, the Dräger pump is started. The system waits for the configured startup delay before the first valve is opened. This gives the pump time to establish the gas flow.

For each measurement valve, `main.py` opens the valve and repeatedly reads the sensors for the configured measurement duration. Each reading combines the Dräger measurements with the additional H₂S value and H₂S sensor temperature. The complete result is passed to `csv_data/csv_storage.py`, which writes it to a CSV file in the `data/` folder.

At the same time, `main.py` updates `system_logs/status.json` through `system_logs/status_storage.py`. This file contains the current state of the measurement system and the most recent sensor values. The dashboard reads this file to show live information. The dashboard does not communicate directly with the hardware.

After a measurement valve is finished, the valve is closed and Valve 6 is opened for flushing. Valve 6 is also measured and written to CSV. Recording the flush valve makes it possible to check later whether the gas concentrations actually decreased during the flushing period.

After flushing, the system continues with the next configured measurement valve. If continuous mode is enabled, the whole sequence starts again after the last valve.

`main.py` also contains the cleanup that is needed when the measurement is stopped or when an error occurs. The valves should be closed, the Dräger pump should be stopped, the sensor connections should be closed and the CSV file should be left in a valid state. This is important because the program controls physical hardware and may run unattended for long periods.

`main.py` is normally not started manually. It is started by `gasmonitor.service`. The dashboard tells Linux to start or stop this service, and the service then starts or stops `main.py`. This is explained in more detail in the section about `services/` and `systemd`.

---

## 2. `dashboard.py`

`dashboard.py` contains the Streamlit web interface. It is the part of the project that the user normally works with.

The dashboard is intentionally separated from the measurement process. It does not open valves, read the Dräger or access the H₂S sensor directly. Instead, it shows information that has already been written to files by the measurement and UPS processes.

The main measurement status comes from `system_logs/status.json`. While a measurement is running, `main.py` keeps this file updated. It contains information such as the current valve, the current cycle, the pump state, the latest Dräger values, the latest Mzuzu H₂S value, the H₂S sensor temperature and a status message. The dashboard reads this file repeatedly and uses it to update the live display.

The dashboard also reads the current measurement settings. These are stored in `settings/config.json`. The functions in `settings/config_storage.py` are used to load and save them. When the measurement is stopped, the user can change the settings in the dashboard. The new values are then written to `config.json` and will be used the next time `main.py` starts.

The file `settings/default_config.json` is used when the user selects Restore Defaults. It contains the standard values that should be restored. Keeping the default values in a separate file means that changing the active settings does not overwrite the original reference settings.

The dashboard reads the recorded measurement files from `data/`. These CSV files are used for the download section. Depending on the selected filter, the dashboard can include all recorded measurements, a recent time range or a custom date range. It can provide a combined download or individual source files.

Battery information is read from `system_logs/ups_status.json`. This file is updated by `hardware/ups_monitor.py`, not by the dashboard. It contains the current battery percentage, voltage and warning state.

The file `system_logs/ups_history.json` stores information about the most recent UPS-triggered shutdown. The dashboard uses this so that the last battery-related shutdown can still be seen after the Raspberry Pi has restarted.

The file `system_logs/system_state.json` contains information about system boot and shutdown state. The persistent event history is stored in `system_logs/system_events.csv`. The dashboard displays this event log and also makes it available for download.

The START and STOP buttons do not run `main.py` directly. They call functions in `services/service_controller.py`. That file uses `systemctl` to start and stop `gasmonitor.service`. This avoids having several measurement processes running at the same time and keeps the measurement process independent from Streamlit.

The dashboard itself is normally started by `gasmonitor-dashboard.service`. This means the web interface can become available automatically after the Raspberry Pi boots, even though the actual measurement still has to be started manually.

---

## 3. `hardware/`

The `hardware/` folder contains the project-specific code that communicates with physical hardware. The purpose of this folder is to keep device-specific code separate from the main measurement sequence.

### `hardware/valves.py`

`valves.py` is the interface used by `main.py` to control the gas valves.

`main.py` works with valve numbers such as Valve 1 or Valve 6. It should not need to know which Raspberry Pi pin belongs to which relay. `valves.py` handles this connection between logical valve numbers and the relay board.

It uses `hardware/PiRelay6.py` for the actual relay switching.

This separation is useful because the measurement sequence can simply request that a valve is opened or closed. The low-level GPIO details stay in the relay code.

### `hardware/PiRelay6.py`

`PiRelay6.py` is the low-level driver for the SB Components PiRelay 6-channel board.

The relay board connects the Raspberry Pi GPIO pins to the six gas valves. The current mapping uses physical Raspberry Pi header pins:

```text
Relay 1 → physical pin 29 → GPIO5
Relay 2 → physical pin 31 → GPIO6
Relay 3 → physical pin 33 → GPIO13
Relay 4 → physical pin 35 → GPIO19
Relay 5 → physical pin 37 → GPIO26
Relay 6 → physical pin 40 → GPIO21
```

This file is normally used through `hardware/valves.py` rather than directly from `main.py`.

One important detail is that GPIO6 is already used by Relay 2. Another device should therefore not use GPIO6 at the same time.

### `hardware/drager_control.py`

`drager_control.py` is the project-specific interface to the Dräger X-am 8000.

The actual Dräger communication is implemented in the external `drager_xam_8000/` library. `drager_control.py` sits between that library and `main.py`.

It provides the functions that the measurement program needs, such as connecting to the device, disconnecting, starting and stopping the pump and reading the current gas values.

This wrapper is useful because `main.py` does not need to know how the Dräger protocol works internally. If the external Dräger library changes later, most of the necessary changes should remain inside `drager_control.py`.

### `hardware/h2s_control.py`

`h2s_control.py` connects the main project to the separate Mzuzu H₂S sensor.

The sensor board uses two I²C devices:

```text
0x48  LMP91002 potentiostat
0x49  ADS1115 ADC
```

The lower-level sensor package is stored in `h2s-rpi/`. `h2s_control.py` opens the I²C connection, creates the sensor object, reads the H₂S concentration and sensor temperature and returns the values in a form that `main.py` can use.

This keeps sensor-specific setup and library imports out of `main.py`.

### `hardware/ups_control.py`

`ups_control.py` reads battery information from the X1205 UPS.

The X1205 fuel-gauge interface is available on I²C address:

```text
0x36
```

The file contains the low-level code required to read values such as battery percentage and battery voltage.

It is mainly used by `hardware/ups_monitor.py`.

### `hardware/ups_monitor.py`

`ups_monitor.py` is a separate long-running process that monitors the UPS.

It reads the battery values from `ups_control.py` at regular intervals and writes the current result to `system_logs/ups_status.json`. This is the file the dashboard reads.

The monitor also checks whether the battery has reached the warning or shutdown limits. The current production settings are approximately:

```text
Warning percentage: 25 %
Shutdown percentage: 15 %
Warning voltage: 3.40 V
Shutdown voltage: 3.25 V
```

The shutdown is not triggered by a single low reading. Several consecutive critical readings are required first. This reduces the risk of shutting down because of one temporary measurement fluctuation.

If a shutdown is necessary, `ups_monitor.py` first stops `gasmonitor.service`. This gives `main.py` time to close valves, stop the pump and finish writing data. After the measurement service has stopped, the UPS shutdown is recorded and the Raspberry Pi is powered off.

`ups_monitor.py` is started by `ups-monitor.service` and runs independently from the measurement process. Battery monitoring therefore continues even when no measurement is active.

---

## 4. `csv_data/`

The `csv_data/` folder contains the code used to store measurement data.

The main file is:

```text
csv_data/csv_storage.py
```

`main.py` sends every complete sensor reading to this module. `csv_storage.py` is responsible for selecting the correct folder, creating a CSV file and writing the measurement row.

A measurement row contains the timestamp, the active valve number, the Dräger gas values, the additional H₂S reading and the H₂S sensor temperature.

Typical columns are:

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

The files are stored below:

```text
data/YYYY-MM-DD/
```

The measurements are written continuously. They are not held in memory until the measurement is stopped. After a row is written, the file is flushed so that the data is already present on disk.

This is important for long unattended runs. If the process stops unexpectedly, most of the previously recorded data is still available.

When the date changes during a running measurement, the storage code switches to the folder for the new day and continues writing there.

The CSV files are later read by `dashboard.py` for downloads and copied by `github/github_backup.py` for the automatic data backup.

---

## 5. `settings/`

The `settings/` folder contains the measurement configuration.

It uses three files because they have different purposes.

### `settings/config.json`

`config.json` contains the settings that are currently selected by the user.

Examples are the list of measurement valves, the flush valve, measurement duration, measurement interval, flush time, pump startup delay, cycle pause, continuous mode and pump flow.

When a measurement is started, `main.py` loads these values and uses them for that run.

When the user changes a setting in the dashboard, the new value is saved to this file.

### `settings/default_config.json`

`default_config.json` contains the standard values for the system.

These are kept separately from the current settings so that the original reference values are not lost when the user changes `config.json`.

When Restore Defaults is selected in the dashboard, the values from `default_config.json` are used to rebuild the active configuration.

In simple terms:

- `config.json` is what the system should use now.
- `default_config.json` is the reference configuration that can be restored.

### `settings/config_storage.py`

`config_storage.py` contains the Python functions that read and write both JSON files.

It is used by `main.py` and `dashboard.py`.

Having one shared module for configuration handling avoids having one implementation in the dashboard and another implementation in the measurement code. It also gives one place to handle missing values, default values and safe file writing.

The dashboard disables the settings controls while a measurement is active. This is done because `main.py` loads its settings when it starts. Changing the file in the middle of a cycle would not necessarily change the values that the running process is already using.

---

## 6. `system_logs/`

The `system_logs/` folder contains two kinds of information: current system state and historical events.

Some files are updated regularly and describe what is happening right now. Other files keep a history that is useful after a restart or shutdown.

### `system_logs/status_storage.py`

`status_storage.py` is used by `main.py` to update the current measurement status.

Instead of `main.py` writing JSON by itself, the status-writing logic is kept in this file.

It writes to:

```text
system_logs/status.json
```

### `system_logs/status.json`

`status.json` contains the current state of the measurement process.

Typical information includes the active valve, pump state, current cycle, current mode, latest sensor measurements, the latest H₂S value and a status message.

The dashboard reads this file to display live information.

This file is not a measurement history. It represents the latest known state and is overwritten as the system runs.

### `system_logs/system_logger.py`

`system_logger.py` contains the functions used to write system events.

These events include boot, shutdown and UPS-related shutdown information.

The persistent events are written to:

```text
system_logs/system_events.csv
```

### `system_logs/system_events.csv`

This file is the persistent event history.

Unlike `status.json`, old entries remain in the file.

It is used by the dashboard and is also included in the automatic GitHub data backup.

### `system_logs/system_state.json`

`system_state.json` stores the latest known system lifecycle information, for example the latest boot and shutdown details.

The dashboard uses it to show system-state information without having to reconstruct it from the full event log every time.

### `system_logs/log_shutdown.py`

`log_shutdown.py` is a small script that is called during operating-system shutdown or reboot.

Its job is to pass the shutdown event to `system_logger.py`.

It is used by the shutdown systemd service.

### `system_logs/ups_status.json`

`ups_status.json` contains the latest UPS reading.

It is written by:

```text
hardware/ups_monitor.py
```

and read by:

```text
dashboard.py
```

The file typically contains battery percentage, voltage, warning state and update time.

### `system_logs/ups_history.json`

`ups_history.json` stores information about the most recent UPS-triggered shutdown.

This makes the last critical battery event available after the Raspberry Pi starts again.

It is written by `hardware/ups_monitor.py` and read by `dashboard.py`.

---

## 7. `github/`

The `github/` folder contains the automatic data-backup code.

The main file is:

```text
github/github_backup.py
```

This backup is separate from the normal source-code repository.

Its purpose is to save the measurement results and system event history regularly, even during a long-running experiment.

The script copies:

```text
data/
system_logs/system_events.csv
```

into a separate local Git repository:

```text
/home/valvescontroller/Desktop/gasmonitor-data-backup
```

The separate repository is then committed and pushed to GitHub.

Only these selected data files are included in this automatic backup. Runtime status JSON files, Python source files and settings are not part of this scheduled data backup.

If nothing has changed since the previous backup, the script does not create an unnecessary new commit.

The backup script is normally started by `gasmonitor-github-backup.service`. A systemd timer starts that service at the scheduled times.

---

## 8. `services/` and systemd

The `services/` folder contains code and reference files related to Linux service control.

The important idea is that the main programs are not normally kept running from open terminal windows. Raspberry Pi OS uses `systemd` to manage them.

A systemd service describes which program should be started, which working directory should be used, which Python interpreter should run it and what Linux should do if the process stops.

The active service definitions are installed under:

```text
/etc/systemd/system/
```

The copy of `gasmonitor.service` inside the project is a project/reference copy. Editing that file alone does not automatically change the installed service unless the installed service is updated as well.

### `services/service_controller.py`

This file is used by `dashboard.py`.

It contains the functions that send start, stop and restart commands to `gasmonitor.service`. It also checks whether the service is currently active.

This is what allows the dashboard to show either START or STOP depending on the current state.

### `gasmonitor.service`

`gasmonitor.service` is the service responsible for running `main.py`.

It is useful to think of it as the Linux wrapper around the measurement program.

When the dashboard starts the service, Linux starts `main.py` using the configured project directory and Python virtual environment.

When the dashboard stops the service, Linux sends the stop request to the measurement process so that cleanup can run.

The measurement service is intentionally not started automatically after every reboot. A measurement is started manually from the dashboard.

### `gasmonitor-dashboard.service`

This service runs the Streamlit dashboard.

Unlike the measurement service, it is intended to start automatically after boot so that the web interface becomes available without opening a terminal.

### `ups-monitor.service`

This service runs `hardware/ups_monitor.py`.

It stays active in the background and monitors the battery whether a measurement is running or not.

### `gasmonitor-github-backup.service`

This service runs one execution of `github/github_backup.py`.

It starts, performs the backup and exits.

### `gasmonitor-github-backup.timer`

This timer starts the backup service automatically.

The current schedule is:

```text
06:30
18:30
```

`Persistent=true` means that if a scheduled backup was missed because the Raspberry Pi was off, systemd can run the missed job after the system starts again.

### `system-event-boot.service`

This service records a boot event.

### `system-event-shutdown.service`

This service records an operating-system shutdown or reboot.

---

## 9. `data/`

The `data/` folder contains the recorded measurement files.

The files are grouped into folders by date.

For example:

```text
data/
├── 2026-08-17/
│   ├── 2026-08-17_15-23-11.csv
│   └── 2026-08-17_18-58-18.csv
└── 2026-08-18/
    └── 2026-08-18_07-02-44.csv
```

These files are created by `csv_data/csv_storage.py`.

The dashboard reads them for data downloads, and the GitHub backup script copies them into the separate data-backup repository.

This folder should only be used for measurement data. Unrelated CSV files or test files can otherwise appear in dashboard downloads or backups.

---

## 10. External libraries

Two folders contain code that did not originate as part of the main project structure.

### `drager_xam_8000/`

This folder contains the Dräger communication library.

The project uses it through:

```text
hardware/drager_control.py
```

This means most project code does not depend directly on the internal layout of the external library.

The folder should generally be kept intact so that the external code remains recognizable and easier to update or debug.

### `h2s-rpi/`

This folder contains the external reader package for the Mzuzu H₂S sensor.

The project uses it through:

```text
hardware/h2s_control.py
```

A standalone sensor self-test can be run with:

```bash
python -m h2s_reader --selftest
```

The expected I²C addresses are:

```text
0x48  LMP91002
0x49  ADS1115
```

Calibration values and sensor-specific settings remain part of this external package.

---

## 11. How a measurement run works

A measurement starts when the user presses START in the dashboard.

The dashboard asks `services/service_controller.py` to start `gasmonitor.service`. The service then starts `main.py`.

`main.py` loads the current configuration and prepares the valve controller, Dräger interface, H₂S interface, CSV storage and status storage.

The Dräger pump is started first. The program waits for the configured startup delay before opening the first measurement valve.

During a valve measurement, the program repeatedly reads the Dräger and the additional H₂S sensor. The values are combined into one measurement row and written to CSV. The most recent values are also written to `status.json` so they can be displayed in the dashboard.

When the configured time for that valve is finished, the valve is closed.

Valve 6 is then opened for flushing. The system continues to read and store measurements during this step. This is useful because the recorded values show whether the sample line is actually returning toward fresh-air conditions.

After flushing, Valve 6 is closed and the next measurement valve is opened.

Once all configured valves have been measured, the process either stops or begins another cycle, depending on the configuration.

When STOP is pressed in the dashboard, `gasmonitor.service` is stopped. `main.py` then performs its cleanup before exiting.

---

## 12. How the dashboard gets its information

The dashboard and the measurement program are separate processes. They do not exchange live values by directly calling each other's Python functions.

Instead, the project uses small status files.

While `main.py` is running, it updates `system_logs/status.json`. The dashboard reads that file and displays the latest values.

The UPS monitor works in the same way. `hardware/ups_monitor.py` updates `system_logs/ups_status.json`, and the dashboard reads it.

Recorded measurement history is different. It is stored permanently as CSV files under `data/`, and the dashboard reads those files when the user opens the download section.

This file-based approach keeps the components independent. For example, the dashboard can be restarted without stopping an active measurement, because `main.py` does not depend on the dashboard process.

---

## 13. Battery monitoring and safe shutdown

The UPS monitor runs separately from `main.py`.

This is important because battery protection must still work when the measurement system is idle or when the dashboard has a problem.

`hardware/ups_monitor.py` reads the battery percentage and voltage through `hardware/ups_control.py`.

The current values are written to `system_logs/ups_status.json`.

If the battery becomes low, a warning state is recorded. If it reaches the critical shutdown threshold for several consecutive readings, the monitor begins the shutdown sequence.

It first stops `gasmonitor.service`. This allows `main.py` to close the valves, stop the Dräger pump and finish writing files.

The UPS monitor then waits for the measurement service to stop. After that it stores the shutdown information in `ups_history.json`, writes an event to the system event log and requests operating-system poweroff.

This order is important because turning the Raspberry Pi off immediately could leave a valve open or interrupt a CSV write.

---

## 14. Automatic GitHub backup

The automatic backup is meant for measurement data rather than the full source-code project.

The backup script copies the complete `data/` folder and `system_logs/system_events.csv` into the separate repository at:

```text
/home/valvescontroller/Desktop/gasmonitor-data-backup
```

It then checks whether anything has changed.

If new or changed data exists, it creates a commit and pushes it to GitHub.

The scheduled service runs twice per day at 06:30 and 18:30.

Because measurement CSV files are written continuously, an experiment does not need to be stopped before the next backup. The next scheduled backup can copy data that has already been written to disk.

---

## 15. Useful commands

### Check whether measurement is running

```bash
sudo systemctl status gasmonitor --no-pager
```

This shows the state of `gasmonitor.service`.

During a measurement, the important line should contain:

```text
Active: active (running)
```

When no measurement is running, it should normally show:

```text
Active: inactive (dead)
```

### View recent measurement logs

```bash
sudo journalctl -u gasmonitor -n 100 --no-pager
```

This prints the most recent 100 log lines from the measurement service.

Use it if the measurement stops unexpectedly or if a hardware error appears.

### Check the dashboard service

```bash
sudo systemctl status gasmonitor-dashboard --no-pager
```

The expected normal state is:

```text
Active: active (running)
```

### Restart the dashboard

```bash
sudo systemctl restart gasmonitor-dashboard
```

Use this after changing `dashboard.py` or if the Streamlit page stops responding.

Restarting the dashboard does not normally require stopping the measurement service.

### Check the UPS monitor

```bash
sudo systemctl status ups-monitor --no-pager
```

The normal state is:

```text
Active: active (running)
```

### View UPS logs

```bash
sudo journalctl -u ups-monitor -n 100 --no-pager
```

This shows recent battery readings, warning messages and shutdown decisions.

### Check the GitHub backup timer

```bash
systemctl list-timers --all | grep gasmonitor-github
```

The output should contain `gasmonitor-github-backup.timer` together with the next scheduled execution time.

### Run the GitHub backup manually

```bash
cd ~/Desktop/Drager_XAM8000_valves
source .venv/bin/activate
python3 -m github.github_backup
```

If nothing changed, a normal result is similar to:

```text
Preparing GitHub data backup...
No new data to push.
```

If new data exists, the script should commit and push it.

### Check I²C devices

```bash
i2cdetect -y 1
```

The expected addresses are:

```text
0x36  X1205 UPS
0x48  LMP91002
0x49  ADS1115
```

---

## 16. Checks after changing the code

These checks are mainly useful after files are edited, renamed or moved.

They are not part of normal measurement operation.

### Check Python syntax

From the project folder:

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

This checks whether Python can compile the files.

If everything is correct, the command normally produces no output.

If there is a syntax problem, Python prints the file and line where the error was found.

### Check imports

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

This is useful after reorganizing folders.

The expected result is:

```text
All imports OK
```

If `ModuleNotFoundError` or `ImportError` appears, one of the Python import paths is no longer correct.

---

## 17. Troubleshooting

### `Remote I/O error 121`

A typical message is:

```text
OSError: [Errno 121] Remote I/O error
```

In this project, this usually means that one of the I²C devices is no longer responding.

The first check should be:

```bash
i2cdetect -y 1
```

Normally the scan should show:

```text
0x36  X1205
0x48  LMP91002
0x49  ADS1115
```

If `0x48` and `0x49` are missing, check the physical connection between the H₂S sensor and the Raspberry Pi.

The relevant wires are:

```text
5 V
GND
SDA
SCL
```

In this setup, Error 121 has normally happened when one of these sensor wires became loose or fell out of the connector.

Push all connections in firmly and run `i2cdetect -y 1` again.

The measurement should only be restarted once `0x48` and `0x49` are visible again.

### Dräger is not found

First check whether the USB adapter is visible:

```bash
lsusb
```

Then check whether a serial device exists:

```bash
ls /dev/ttyUSB*
```

The Dräger DIRA adapter must be available before the measurement program can connect to the Dräger.

If the USB device appears in `lsusb` but `/dev/ttyUSB0` is missing, the USB serial driver or device mapping should be checked.

### Measurement stops unexpectedly

Run:

```bash
sudo journalctl -u gasmonitor -n 100 --no-pager
```

The final log lines usually show where the failure occurred.

Typical causes include:

- H₂S I²C communication,
- Dräger communication,
- a disconnected cable,
- a Python exception,
- another hardware communication problem.

### Dashboard does not load

Check:

```bash
sudo systemctl status gasmonitor-dashboard --no-pager
```

If the service is not running, inspect the recent log:

```bash
sudo journalctl -u gasmonitor-dashboard -n 100 --no-pager
```

### UPS status is not updating

Check the service:

```bash
sudo systemctl status ups-monitor --no-pager
```

Then inspect its log:

```bash
sudo journalctl -u ups-monitor -n 100 --no-pager
```

The latest status file can also be viewed with:

```bash
cat ~/Desktop/Drager_XAM8000_valves/system_logs/ups_status.json
```

The update timestamp should change regularly while `ups-monitor.service` is running.

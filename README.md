# Dräger X-am 8000 Valve Monitoring System

## Contents

1. [Project overview](#1-project-overview)
2. [What the system does](#2-what-the-system-does)
3. [Project structure](#3-project-structure)
4. [Measurement cycle](#4-measurement-cycle)
5. [Data storage](#5-data-storage)
6. [Starting and stopping the system](#6-starting-and-stopping-the-system)
7. [Battery monitoring and safe shutdown](#7-battery-monitoring-and-safe-shutdown)
8. [GitHub backup](#8-github-backup)
9. [Useful checks](#9-useful-checks)
10. [Detailed documentation](#10-detailed-documentation)

---

## 1. Project overview

This project is an automated gas-monitoring system built around a Raspberry Pi 5.

Gas is sampled from several lines through six electrically controlled valves. A Dräger X-am 8000 measures the main gas components. A separate Mzuzu H₂S sensor provides an additional higher resolution H₂S measurement.

The Raspberry Pi controls the valves, collects the sensor values and stores the measurements as CSV files. A Streamlit dashboard is used to operate the system and view its current status.

The system is designed for long unattended measurements. It can run continuously for hours or days, stores data while the measurement is running, monitors the UPS battery and performs a controlled shutdown if the battery becomes critically low.

Measurement data and the system event log are also backed up automatically to GitHub.

---

## 2. What the system does

During a measurement run, the system:

- starts the Dräger pump,
- opens one measurement valve at a time,
- reads the Dräger values,
- reads the additional H₂S sensor,
- writes every reading to CSV,
- closes the measurement valve,
- opens Valve 6 to flush the sampling line,
- records the Valve 6 values as well,
- continues with the next valve,
- repeats the sequence in continuous mode.

The dashboard is the main operator interface. It is used to start and stop measurements, view live values, change settings while the system is stopped, download recorded data and check UPS and system information.

---

## 3. Project structure

```text
Drager_XAM8000_valves/
├── README.md
├── docs/
│   └── DOCUMENTATION.md
├── main.py
├── dashboard.py
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

### `main.py`
Runs the complete measurement sequence.

### `dashboard.py`
Provides the Streamlit web interface.

### `hardware/`
Contains the project-specific interfaces for valves, Dräger communication, the additional H₂S sensor and the UPS.

### `csv_data/`
Contains the CSV storage code.

### `settings/`
Contains the current configuration, the default configuration and the functions used to read and write them.

### `system_logs/`
Contains live status files and the persistent system event log.

### `github/`
Contains the automatic GitHub data-backup script.

### `services/`
Contains the Python service controller and local reference files for systemd services.

### `data/`
Contains recorded measurement CSV files, grouped by date.

### `drager_xam_8000/`
External Dräger communication library.

### `h2s-rpi/`
External reader package for the Mzuzu H₂S sensor.

### `.streamlit/`
Contains Streamlit configuration.

### `.venv/`
Python virtual environment used by the project.

For a file-by-file explanation, see [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md).

---

## 4. Measurement cycle

A normal cycle follows this sequence:

```text
START
  ↓
Load current settings
  ↓
Close all valves
  ↓
Connect Dräger and H₂S sensor
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
Write data to CSV
  ↓
Update live dashboard status
  ↓
Repeat until measurement time is complete
  ↓
Close measurement valve
  ↓
Open Valve 6
  ↓
Flush sampling line
  ↓
Record Valve 6 values
  ↓
Close Valve 6
  ↓
Continue with next measurement valve
  ↓
Repeat cycle if continuous mode is enabled
```

Valve 6 is stored in the CSV files as well. This makes it possible to check whether the flushing step is actually reducing the measured gas concentrations.

---

## 5. Data storage

Measurement data is stored below:

```text
data/YYYY-MM-DD/
```

Measurements are written while the system is running. The data is not kept in memory until the measurement is stopped.

The CSV file is flushed after writes, which reduces the amount of data that could be lost after an unexpected interruption.

If a measurement continues across midnight, the storage code automatically starts writing into the folder for the new date.

---

## 6. Starting and stopping the system

The normal way to operate the measurement system is through the dashboard.

When START is pressed:

```text
dashboard.py
   ↓
services/service_controller.py
   ↓
systemctl start gasmonitor.service
   ↓
main.py starts
```

When STOP is pressed:

```text
dashboard.py
   ↓
services/service_controller.py
   ↓
systemctl stop gasmonitor.service
   ↓
main.py performs cleanup and exits
```

The dashboard does not start `main.py` directly. Using `systemd` gives the measurement process one clear running state and makes its logs available through `journalctl`.

---

## 7. Battery monitoring and safe shutdown

The X1205 UPS is monitored separately from the measurement process.

The UPS monitor reads battery percentage and voltage. If the battery reaches the critical shutdown threshold, it first stops the measurement service, waits for the cleanup to finish, stores the shutdown information and then requests Raspberry Pi poweroff.

The UPS monitor runs independently so battery supervision continues even when no measurement is active.

---

## 8. GitHub backup

The automatic data backup intentionally includes only:

```text
data/
system_logs/system_events.csv
```

The backup script copies these files into a separate local Git repository and pushes that repository to GitHub.

The scheduled backup runs twice per day:

```text
06:30
18:30
```

The project source code and the measurement-data backup are therefore kept separate.

---

## 9. Useful checks

### Check whether measurement is running

```bash
sudo systemctl status gasmonitor --no-pager
```

Expected during an active measurement:

```text
Active: active (running)
```

### View recent measurement logs

```bash
sudo journalctl -u gasmonitor -n 100 --no-pager
```

Use this command when a measurement stops unexpectedly.

### Check the UPS monitor

```bash
sudo systemctl status ups-monitor --no-pager
```

Expected:

```text
Active: active (running)
```

### Check I²C devices

```bash
i2cdetect -y 1
```

Expected addresses:

```text
0x36  X1205 UPS
0x48  LMP91002
0x49  ADS1115
```

If `0x48` and `0x49` are missing, check the H₂S sensor cables between the sensor and the Raspberry Pi. In this setup, `Remote I/O error 121` has normally occurred when one of these cables became loose or disconnected.

---

## 10. Detailed documentation

A detailed explanation of the source files, inputs, outputs, services and troubleshooting is available here:

**[Detailed project documentation](docs/DOCUMENTATION.md)**

That document is intended for anyone who needs to understand, maintain or modify the code.

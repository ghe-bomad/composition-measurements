# CSV Data Storage

## Purpose
`csv_data/` contains the persistent measurement-storage code.

```text
csv_data/
├── __init__.py
└── csv_storage.py
```

## `csv_storage.py`
`CSVStorage` receives complete measurements from `main.py` and writes them to CSV.

Typical fields:
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

**Used by:** `main.py`

## Why it exists
Measurement data must survive dashboard restarts, service restarts, network failures and long unattended runs. It is therefore persisted locally rather than kept only in RAM.

## Output
```text
data/YYYY-MM-DD/*.csv
```

Data is written continuously and flushed after writes. It is not saved only when STOP is pressed.

At a date change, the storage layer closes the old file and creates a new daily location/file.

## Other code using these files
- `dashboard.py` scans them for download/filtering.
- `github/github_backup.py` copies the entire `data/` tree to the backup repository.

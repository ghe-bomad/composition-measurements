from datetime import datetime
from pathlib import Path
import shutil
import subprocess


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

BACKUP_DIR = Path(
    "/home/valvescontroller/Desktop/gasmonitor-data-backup"
)

SOURCE_DATA_DIR = (
    PROJECT_ROOT
    / "data"
)

SOURCE_EVENT_LOG = (
    PROJECT_ROOT
    / "system_logs"
    / "system_events.csv"
)

BACKUP_DATA_DIR = (
    BACKUP_DIR
    / "data"
)

BACKUP_EVENT_LOG = (
    BACKUP_DIR
    / "system_events.csv"
)


def run_git(*arguments):
    result = subprocess.run(
        [
            "git",
            *arguments,
        ],
        cwd=BACKUP_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or result.stdout.strip()
        )

    return result.stdout.strip()


def copy_measurement_data():
    if not SOURCE_DATA_DIR.exists():
        return

    BACKUP_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copytree(
        SOURCE_DATA_DIR,
        BACKUP_DATA_DIR,
        dirs_exist_ok=True,
    )


def copy_system_event_log():
    if not SOURCE_EVENT_LOG.exists():
        return

    shutil.copy2(
        SOURCE_EVENT_LOG,
        BACKUP_EVENT_LOG,
    )


def backup_to_github():
    print(
        "Preparing GitHub data backup...",
        flush=True,
    )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    copy_measurement_data()
    copy_system_event_log()

    paths_to_add = []

    if BACKUP_DATA_DIR.exists():
        paths_to_add.append(
            "data"
        )

    if BACKUP_EVENT_LOG.exists():
        paths_to_add.append(
            "system_events.csv"
        )

    if not paths_to_add:
        print(
            "No backup data available.",
            flush=True,
        )
        return

    run_git(
        "add",
        *paths_to_add,
    )

    status = run_git(
        "status",
        "--porcelain",
    )

    if not status:
        print(
            "No new data to push.",
            flush=True,
        )
        return

    timestamp = (
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    run_git(
        "commit",
        "-m",
        (
            "Automatic data backup "
            f"{timestamp}"
        ),
    )

    print(
        "Changes committed.",
        flush=True,
    )

    run_git(
        "push",
        "origin",
        "main",
    )

    print(
        "GitHub backup completed successfully.",
        flush=True,
    )


if __name__ == "__main__":
    try:
        backup_to_github()

    except Exception as error:
        print(
            "GitHub backup failed: "
            f"{error}",
            flush=True,
        )

        raise

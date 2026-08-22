import subprocess


SERVICE_NAME = "gasmonitor.service"


def _run_systemctl(command):
    result = subprocess.run(
        ["sudo", "systemctl", command, SERVICE_NAME],
        capture_output=True,
        text=True,
    )

    return {
        "success": result.returncode == 0,
        "output": result.stdout.strip(),
        "error": result.stderr.strip(),
    }


def start_service():
    return _run_systemctl("start")


def stop_service():
    return _run_systemctl("stop")


def restart_service():
    return _run_systemctl("restart")


def is_service_active():
    result = subprocess.run(
        ["systemctl", "is-active", SERVICE_NAME],
        capture_output=True,
        text=True,
    )

    return result.stdout.strip() == "active"

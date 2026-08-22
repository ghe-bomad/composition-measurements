import json
from pathlib import Path


SETTINGS_DIR = Path(__file__).resolve().parent

CONFIG_PATH = (
    SETTINGS_DIR
    / "config.json"
)

DEFAULT_CONFIG_PATH = (
    SETTINGS_DIR
    / "default_config.json"
)


def load_default_config():
    with open(
        DEFAULT_CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as default_file:
        return json.load(
            default_file
        )


def load_config():
    defaults = (
        load_default_config()
    )

    if not CONFIG_PATH.exists():
        return defaults.copy()

    try:
        with open(
            CONFIG_PATH,
            "r",
            encoding="utf-8",
        ) as config_file:
            current = json.load(
                config_file
            )

        return {
            **defaults,
            **current,
        }

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return defaults.copy()


def save_config(config):
    temporary_path = (
        CONFIG_PATH
        .with_suffix(
            ".json.tmp"
        )
    )

    with open(
        temporary_path,
        "w",
        encoding="utf-8",
    ) as config_file:
        json.dump(
            config,
            config_file,
            indent=4,
            ensure_ascii=False,
        )

    temporary_path.replace(
        CONFIG_PATH
    )


def reset_config_to_defaults():
    defaults = (
        load_default_config()
    )

    save_config(
        defaults
    )

    return defaults

import os

import yaml

DEFAULT_CONFIG_PATH = "config.yaml"
DEFAULT_DATA_DIR = os.path.expanduser("~/.autosome")


def get_default_config():
    return {
        "data_dir": DEFAULT_DATA_DIR,
        "platforms": {
            "xhs": {
                "browser_data_dir": os.path.join(
                    DEFAULT_DATA_DIR, "browser_data", "xhs"
                ),
            },
            "mp": {
                "browser_data_dir": os.path.join(
                    DEFAULT_DATA_DIR, "browser_data", "mp"
                ),
            },
        },
    }


def load_config(config_path=None):
    config = get_default_config()
    path = config_path or DEFAULT_CONFIG_PATH

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        _deep_merge(config, user_config)

    return config


def _deep_merge(base, override):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value

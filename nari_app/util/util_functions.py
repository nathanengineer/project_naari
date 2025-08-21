""" Modular contains the necessary functions for poll/GET specific info of devices using JSON/API calls. """

import time
import json
import os
from typing import Callable, ParamSpec, Any, Generator
from functools import wraps

from dash import ctx as callback_context
from dash.exceptions import PreventUpdate

from nari_app.util.config_builder import DeviceConfig

__all__ = [
    'FuncParms',
    'FuncReturn',
    'is_app_loaded',
    'function_time',
    'device_load',
    'save_configer'
]

FuncParms = ParamSpec("FuncParms")
FuncReturn = ParamSpec("FuncReturn")

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(MAINDIR, "nari_config.json")

def is_app_loaded() -> Callable[[Callable[FuncParms, FuncReturn]], Callable[FuncParms, FuncReturn]]:
    """
        Blocks a callback until the app's inizilize flag is consider True.
        Must ensure State('elements_initialized', 'data') is passed for it to work properly.
    """
    def decorator(func: Callable[FuncParms, FuncReturn]) -> Callable[FuncParms, FuncReturn]:
        @wraps(func)
        def wrapper(*args: FuncParms.args, **kwargs: FuncParms.kwargs) -> FuncReturn:
            if not callback_context.states['elements_initialized.data']:
                raise PreventUpdate
            return func(*args, **kwargs)  # exclude 'elements_initialized' from your actual callback logic
        return wrapper
    return decorator


def function_time(func: Callable[FuncParms, FuncReturn]) -> Callable[FuncParms, FuncReturn]:
    """ Print how long a function takes to run. Used primary in (debugging or tests only) """
    @wraps(func)
    def wrapper(*args: FuncParms.args, **kwargs: FuncParms.kwargs) -> FuncReturn:
        start_time = time.perf_counter()
        results = func(*args, **kwargs)
        total_time = time.perf_counter() - start_time
        print(f"Function: {func.__name__} took {total_time:.4f} seconds to run")
        return results  # exclude 'elements_initialized' from your actual callback logic
    return wrapper


def device_load(file_path: str = CONFIG_PATH):
    """
    Load and return the device configuration from JSON.

    Args:
        file_path: Absolute or relative path to the JSON config file.

    Returns:
        Parsed configuration as a dictionary.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        ValueError: If the loaded configuration is empty.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config_file = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # TODO: Replace with equivalent Logger
        print(f"[device_load] Failed to load config from {file_path}: {e}") # Temporary
        raise

    if not config_file:
        print(f"[device_load] Config file {file_path} is empty.")  # temporary
        raise ValueError(f"Config file {CONFIG_PATH} is empty")

    return config_file


def save_configer(config: dict, file_path: str = CONFIG_PATH):
    """
        Save the given configuration dictionary to a JSON file.

       Args:
           config: The configuration data to save.
           file_path: Absolute or relative path to the JSON config file.

       Raises:
           ValueError: If the provided configuration is empty.
           OSError: If the file cannot be written.
       """
    if not config:
        # TODO: Replace with equivalent Logger
        print(f"[save_configer] Attempted to save empty config to {file_path}")  # temporary
        raise ValueError(f"Attempted to save empty config to {file_path}")

    try:
        with open(file_path, "w", encoding="utf-8") as cfile:
            json.dump(config, cfile, indent=4, ensure_ascii=False)
    except OSError as e:
        # TODO: Replace with equivalent Logger
        print(f"[save_configer] Failed to save config to {file_path}: {e}")  # temporary
        raise

# TODO: make decorator?
def get_devices_ip(nari_settings: dict[str, Any] | None = None) -> list[str]:
    """ Extract a list of device IP addresses from config settings dict """
    if not nari_settings or not isinstance(nari_settings, dict):
        nari_settings = device_load()

    return [ info['address'] for info in nari_settings['devices'] ]


def get_device(devices: list[DeviceConfig], device_id: int) -> Generator[DeviceConfig, None, None]:
    for device in devices:
        if device['id'] == device_id:
            yield device

def is_device_active(device_id: int, devices: list[DeviceConfig]) -> Generator[bool, None, None]:
    for device in devices:
        if device['id'] == device_id:
            yield device['active']
            return

def device_presets_mapping(cach_presets: list[dict], devices: list[DeviceConfig]):
    """Map active devices to cached presets by matching IP addresses."""
    # build a map of address → id for active devices
    devices = {device["address"]: device["id"] for device in devices}
    for device_preset in cach_presets:
        if device_preset['ip'] in devices:
            device_preset['device_id'] = devices[device_preset['ip']]  # adds device ID key into polled device presets
    return cach_presets
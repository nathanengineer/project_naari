""" Modular contains the necessary functions for poll/GET specific info of devices using JSON/API calls. """
import logging
import time
import json
import os
from typing import Callable, ParamSpec
from functools import wraps

from dotenv import load_dotenv
from dash import ctx as callback_context
from dash.exceptions import PreventUpdate

from naari_logging.naari_logger import LogManager
from naari_app.util.config_builder import DeviceConfig

FuncParms = ParamSpec("FuncParms")
FuncReturn = ParamSpec("FuncReturn")

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(MAINDIR, "naari_config.json")

load_dotenv(os.path.join(MAINDIR, ".env"))
TO_LOG = int(os.getenv("LOGGING", "0")) == 1

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


def naari_config_load(file_path: str = CONFIG_PATH):
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
        LogManager.print_message(
            "[device_load] Failed to load config from %s: %s",
            file_path, e,
            to_log=TO_LOG,
            log_level=logging.ERROR
        )
        raise

    if not config_file:
        LogManager.print_message(
            "[device_load] Config file %s is empty.",
            file_path,
            to_log=TO_LOG,
            log_level=logging.ERROR
        )
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
        LogManager.print_message(
            "[save_configer] Attempted to save empty config to %s",
            file_path,
            to_log=TO_LOG,
            log_level=logging.ERROR
        )
        raise ValueError(f"Attempted to save empty config to {file_path}")

    try:
        with open(file_path, "w", encoding="utf-8") as cfile:
            json.dump(config, cfile, indent=4, ensure_ascii=False)
    except OSError as e:
        LogManager.print_message(
            "[save_configer] Failed to save config to %s: %s",
            file_path, e,
            to_log=TO_LOG,
            log_level=logging.ERROR
        )
        raise OSError from e


def get_devices_ip(naari_devices: list[DeviceConfig], get_inactive: bool = True) -> list[str]:
    """ Extract a list of device IP addresses from config settings dict """
    if not naari_devices or not isinstance(naari_devices, list):
        naari_devices = naari_config_load().get('devices')

    if get_inactive:
        return [device['address'] for device in naari_devices]
    return [device['address'] for device in naari_devices if device['active']]


def get_device(devices: list[DeviceConfig], device_id: int) -> DeviceConfig | None:
    """ Takes list of devices in config file and returns config info based on device_id. """
    return next((device for device in devices if device['id'] == device_id), None)


def is_device_active(device_id: int, devices: list[DeviceConfig]) -> bool:
    """ Determines if provided device_id is active. """
    return next((device['active'] for device in devices if device['id'] == device_id), False )


def device_polled_data_mapping(cach_data: list[dict], devices: list[DeviceConfig]):
    """Map active devices to cached presets by matching IP addresses."""
    # build a map of address → id for active devices
    devices = {device["address"]: device["id"] for device in devices}
    for device_preset in cach_data:
        if device_preset['ip'] in devices:
            device_preset['device_id'] = devices[device_preset['ip']]  # adds device ID key into polled device presets
    return cach_data


def get_master_device(devices: list[DeviceConfig]):
    """Return the (single) master device or None if not found."""
    return next((device for device in devices if device.get('master_sync')), None)

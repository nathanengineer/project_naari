"""
Modulare provides schema design for the Config File used by N.A.R.I

As well as  builders and Validations
"""

from typing import TypedDict, NotRequired, Literal
import json
import os


#-------------------------------------- Schema---------------------------------------------------------#

class DeviceConfig(TypedDict):
    """ Single device definition. """

    id: int                                 # device ID #
    address: str                            # IP/DNS address.
    instance_name: str                      # name that will be shown on the UI Labels
    master_sync: bool                       # Master Sync Device
    active: bool                            # 0 = Inactive / 1 = Active


class UISettingsInput(TypedDict):
    """ Internal Structure of the specific UI Setting. """
    value: str | int | float | bool
    type: str


class UISettings(TypedDict):
    """ General environment / app settings (seconds recommended). """

    app_name: UISettingsInput               # (str) Name that will show on the Navbar
    polling_rate: UISettingsInput           # (int) Given interval rate device polling in (sec)
    connect_timeout: UISettingsInput        # (int) Time set to establish TCP in (sec)
    read_timeout: UISettingsInput           # (int) Time set to read request from device
    max_concurrency: UISettingsInput        # (int) Set # of active request
    retries: UISettingsInput                # (int) Number of attempts a Get or POST action takes
    retry_backoff: UISettingsInput          # (float) Time set added to specific Timeout time in (sec)
    request_timeout: UISettingsInput        # (int) TIme set to end connection to possible dead or hang device
    ui_theme:  UISettingsInput


class DevicePreset(TypedDict):
    """ Preset selection for a specific device. """

    device_id: int                         # Unique device id key
    device_address: str                    # IP/DNS address of a specific device. Ex: 42:42:42:42 / the_answer_to_everyting
    preset_name: str                       # Preset of that given device writen as (preset_id: name) Ex: "4: Warm-White"


class ThemeSelectionConfig(TypedDict):
    """ A theme bundles per-device presets. """

    id: int                               # ID # of the theme
    name: str                             # Given name of the Theme
    presets: list[DevicePreset]           # List of Devices Preset to Set


class NaariSettingsConfig(TypedDict):
    """ Full configuration file schema """

    devices: list[DeviceConfig]
    ui_settings: UISettings
    themes: list[ThemeSelectionConfig]


#-------------------------- Configer Functions -------------------------------#

def make_empty_config(app_name: str = "WLED Controller") -> NaariSettingsConfig:
    """ Return a brand-new, valid empty Naari config (type-safe) """
    return {
        "devices": [],
        "ui_settings": {
            "app_name": {
                "value": app_name,
                "type": "str"
            },
            "polling_rate": {
                "value": 3,
                "type": "int"
            },
            "connect_timeout": {
                "value": 2,
                "type": "int"
            },
            "read_timeout": {
                "value":5,
                "type": "int"
            },
            "request_timeout": {
                "value":3,
                "type": "int"
            },
            "max_concurrency": {
                "value": 10,
                "type": "int"
            },
            "retries": {
                "value": 2,
                "type": "int"
            },
            "retry_backoff": {
                "value": 0.25,
                "type": "float"
            },
            "ui_theme": {
                "value": 0,
                "type": "bool"
            }
        },
        "themes": [],
    }


def write_empty_config(path: str) -> NaariSettingsConfig:
    """
    Create an empty config file on disk and return it.

    - Ensures parent directory exists.
    - Overwrites existing file only if it's missing or unreadable/invalid at the caller's discretion.

    Parameters:
        path: Destination JSON file path (e.g., CONFIG_PATH).

    Returns:
        The written NaariConfig.

    Raises:
        OSError: if the directory or file cannot be written.
    """
    config = make_empty_config()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    return config

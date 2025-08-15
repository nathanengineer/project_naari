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

    name: str                               # chosen id name
    address: str                            # IP/DNS address.
    instance_name: str                      # name that will be shown on the UI Labels
    active: bool                            # 0 = Inactive / 1 = Active


class MasterDeviceConfig(TypedDict):
    """ Designated master (sync source) device. """

    name: str                               # chosen id name
    address: str                            # IP/DNS address
    instance_name: str                      # name that will be shown on the UI Labels


class UISettings(TypedDict):
    """ General environment / app settings (seconds recommended). """

    app_name: str                           # Name that will show on the Navbar
    polling_rate: int                       # Given interval rate device polling in (sec)
    connect_timeout: int                    # Time set to establish TCP in (sec)
    read_timeout: int                       # Time set to read request from device
    max_concurrency: int                    # Set # of active request
    retries: int                            # Number of attempts a Get or POST action takes
    retry_backoff: float                    # Time set added to specific Timeout time in (sec)
    request_timeout: int                    # TIme set to end connection to possible dead or hang device
    ui_theme:  NotRequired[Literal["dark", 'light']]


class DevicePreset(TypedDict):
    """ Preset selection for a specific device. """

    device_address: str                    # IP/DNS address of a specific device. Ex: 42:42:42:42 / the_answer_to_everyting
    preset_name: str                       # Preset of that given device writen as (preset_id: name) Ex: "4: Warm-White"


class ThemeSelectionConfig(TypedDict):
    """ A theme bundles per-device presets. """

    name: str                             # Given name of the Theme
    presets: list[DevicePreset]           # List of Devices Preset to Set


class NariSettingsConfig(TypedDict):
    """ Full configuration file schema """

    devices: list[DeviceConfig]
    master_device: MasterDeviceConfig
    ui_settings: UISettings
    themes: list[ThemeSelectionConfig]


#-------------------------- Configer Functions -------------------------------#

def make_empty_config(app_name: str = "WLED Controller") -> NariSettingsConfig:
    """ Return a brand-new, valid empty Nari config (type-safe) """
    return {
        "devices": [],
        "master_device": {
            "name": "",
            "address": "",
            "instance_name": ""
        },
        "ui_settings": {
            "app_name": app_name,
            "polling_rate": 3,
            "connect_timeout": 2,
            "read_timeout": 5,
            "request_timeout": 3,
            "max_concurrency": 10,
            "retries": 2,
            "retry_backoff": 0.25,
            "ui_theme": "dark"
        },
        "themes": [],
    }


def write_empty_config(path: str) -> NariSettingsConfig:
    """
    Create an empty config file on disk and return it.

    - Ensures parent directory exists.
    - Overwrites existing file only if it's missing or unreadable/invalid at the caller's discretion.

    Parameters:
        path: Destination JSON file path (e.g., CONFIG_PATH).

    Returns:
        The written NariConfig.

    Raises:
        OSError: if the directory or file cannot be written.
    """
    cfg = make_empty_config()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    return cfg

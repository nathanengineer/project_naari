import asyncio
from threading import Lock
import time

from naari_app.util.config_builder import DeviceConfig
from naari_app.util.wled_device_status import get_devices_ip, run_status, get_presets

_load_lock = Lock()

INITIAL_DEVICES = None
INITIAL_PRESETS = None

def get_initial_load(naari_devices: list[DeviceConfig]):

    global INITIAL_DEVICES, INITIAL_PRESETS
    if INITIAL_DEVICES is not None and INITIAL_PRESETS is not None:
        return INITIAL_DEVICES, INITIAL_PRESETS

    with _load_lock:
        if INITIAL_DEVICES is None or INITIAL_PRESETS is None:
            devices_ip = get_devices_ip(naari_devices)

            try:
                INITIAL_DEVICES = asyncio.run(run_status(devices_ip))
                time.sleep(.5)   # throttles loading to allow for devices to catch up
                INITIAL_PRESETS = asyncio.run(get_presets(devices_ip))
            except:
                INITIAL_DEVICES = {}
                INITIAL_PRESETS = {}

    return INITIAL_DEVICES, INITIAL_PRESETS

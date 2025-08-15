import asyncio
from threading import Lock

from nari_app.util.util_functions import device_load
from nari_app.util.wled_device_status import get_devices_ip, run_status, get_presets

_load_lock = Lock()

INITIAL_DEVICES = None
INITIAL_PRESETS = None

def get_initial_load(nari_settings = device_load()):

    global INITIAL_DEVICES, INITIAL_PRESETS
    if INITIAL_DEVICES is not None and INITIAL_PRESETS is not None:
        return INITIAL_DEVICES, INITIAL_PRESETS

    with _load_lock:
        if INITIAL_DEVICES is None or INITIAL_PRESETS is None:
            devices_ip = get_devices_ip(nari_settings)

            try:
                INITIAL_DEVICES = asyncio.run(run_status(devices_ip))
                INITIAL_PRESETS = asyncio.run(get_presets(devices_ip))
            except:
                INITIAL_DEVICES = {}
                INITIAL_PRESETS = {}

    return INITIAL_DEVICES, INITIAL_PRESETS

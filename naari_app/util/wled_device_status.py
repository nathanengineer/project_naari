import asyncio, httpx
import json
from typing import Any, Iterable, Optional
from threading import Lock
import os
import logging
import time

from dotenv import load_dotenv

from naari_logging.naari_logger import LogManager
from naari_app.util.util_functions import naari_config_load, get_devices_ip

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ",,"))
load_dotenv(os.path.join(MAINDIR, ".env"))
TO_LOG = int(os.getenv("LOGGING", 0)) == 1

# Adds lock onto App polling events, preventing an accidental flooding of calls
_POLL_LOCK = Lock()

# TODO: PULL dynamic values from config file.
CONNECT_TIMEOUT = 2.0         # seconds to establish TCP
READ_TIMEOUT = 3.0            # seconds to read response
MAX_CONCURRENCY = 10.0        # cap active requests
RETRIES = 2
RETRY_BACKOFF = 0.25        # slows down retry in seconds

# For Initial Load, and use during Testing
DEVICES_LOADED = naari_config_load()
DEVICEs_IP = [info['address'] for info in DEVICES_LOADED['devices']]


class PollingThreadLock(RuntimeError):
    def __init__(self):
        super().__init__("Polling Fail. Poling lock active")
        time.sleep(1)   # giving it time for devices to catch up


def _timeout() -> httpx.Timeout:
    """ Adds a Timeout parameter to Client connections by httpx. """
    return httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=None, pool=None)


async def _fetch_json( client: httpx.AsyncClient, ip: str, path: str, retries: int = RETRIES, simultaneous_ops : Optional[asyncio.Semaphore] = None,) -> dict[str, Any]:
    """Generic GET->JSON with small retry/backoff and consistent result shape."""
    for attempt in range(retries + 1):
        try:
            if simultaneous_ops is None:
                response_data = await client.get(f"http://{ip}{path}")
            else:
                async with simultaneous_ops:
                    response_data = await client.get(f"http://{ip}{path}")

            response_data.raise_for_status()  # treat 4xx/5xx as failures
            try:
                return {
                    "ip": ip,
                    "data": response_data.json()
                }
            except ValueError as e:  # invalid JSON
                return {
                    "ip": ip,
                    "error": True,
                    "error_reason": f"invalid_json: {e}"
                }

        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
            # TODO: Log Error event here
            # Decide to retry or fail
            if attempt >= retries:
                return {
                    "ip": ip,
                    "error": True,
                    "error_reason": f"{e.__class__.__name__}: {e}"
                }
            # exponential backoff: base * 2**attempt
            await asyncio.sleep(RETRY_BACKOFF * (2 ** attempt))

    # TODO: Error event if for loop fails or has an outside issue? or Move it up top.


async def fetch_status(ip: str) -> dict[str, Any]:
    """ Fetch /json API object for a single WLED device (standalone). """
    async with httpx.AsyncClient(timeout= _timeout()) as client:
        return await _fetch_json(
            client=client,
            ip=ip,
            path="/json"
        )


async def fetch_presets(ip: str) -> dict[str, Any]:
    """ Fetch Presets for a signal WLED device (standalone). """
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        return await _fetch_json(
            client=client,
            ip=ip,
            path="/presets.json"
        )


async def run_status(device_address_list: Iterable[str], max_concurrency: int = MAX_CONCURRENCY) -> list[dict[str, Any]]:
    """ Fetches /json status from all devices concurrently """
    simultaneous_ops = asyncio.Semaphore(max_concurrency) if max_concurrency > 0 else None

    async with httpx.AsyncClient(timeout=_timeout()) as client:
        tasks = [
            _fetch_json(client=client, ip=ip, path="/json", simultaneous_ops=simultaneous_ops)
            for ip in device_address_list
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)


async def get_presets(device_address_list: Iterable[str], max_concurrency: int = MAX_CONCURRENCY) -> list[dict[str, Any]]:
    """ Fetch /preset.json from all devices concurrently """
    simultaneous_ops = asyncio.Semaphore(max_concurrency) if max_concurrency > 0 else None

    async with httpx.AsyncClient(timeout=_timeout()) as client:
        tasks = [
            _fetch_json(client=client, ip=ip, path="/presets.json", simultaneous_ops=simultaneous_ops)
            for ip in device_address_list
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)


def poll_all_devices(device_address_list: Iterable[str] | None = None):
    # Lock prevents multi connections to be polled and thus clogging up the pipeline
    if not device_address_list:
        # TODO: add logging here for error
        device_address_list = get_devices_ip()

    if not _POLL_LOCK.acquire_lock(blocking=False):     # pylint: disable=no-member
        raise PollingThreadLock

    #async with lock:
    try:
        return asyncio.run(run_status(device_address_list))
    finally:
        _POLL_LOCK.release()


def poll_device_presets(device_address_list: Iterable[str] | None = None):
    if not device_address_list:
        LogManager.print_message(
            "No list of IP supplied. Possible Config or supplied error. Need to correct. Reading from file.",
            to_log=TO_LOG,
            log_level=logging.ERROR
        )
        device_address_list = get_devices_ip()
    return asyncio.run(get_presets(device_address_list))



#---------------Test Dev Only Use Functions------------------------------#
def save_state():
    data = poll_all_devices()
    with open('../../data.json', 'w') as f:
        json.dump(data, f, indent=4)


def save_presets():
    data = poll_device_presets()
    with open('../../presets.json', "w") as f:
        json.dump(data, f, indent=4)

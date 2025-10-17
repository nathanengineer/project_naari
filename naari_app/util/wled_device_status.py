"""
Handles all status and preset polling operations for WLED devices.

This module performs asynchronous GET requests to fetch /json and /presets.json
data from one or more WLED devices. It includes timeout handling, retry logic,
concurrency limiting, and polling lock control to avoid conflicts or flooding
the network.

Features:
    - Device polling with async concurrency and retry backoff
    - Fetching WLED status (/json) and preset (/presets.json) data
    - Polling lock to prevent overlapping calls
    - Error shaping and nested data traversal helper (get_status)
    - Dev/test functions for saving and reading mock poll data
"""

import asyncio
import json
from typing import Any, Iterable, Optional, Union
from threading import Lock
import os
import logging
import time

import httpx
from dotenv import load_dotenv

from naari_logging.naari_logger import LogManager
from naari_app.util.util_functions import naari_config_load, get_devices_ip


MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ",,"))
load_dotenv(os.path.join(MAINDIR, ".env"))
TO_LOG = int(os.getenv("LOGGING")) == 1
TEST_RUN = int(os.getenv("TEST_RUN", 0)) == 1   # pylint: disable=invalid-envvar-default

# Adds lock onto App polling events, preventing an accidental flooding of calls
_POLL_LOCK = Lock()

# TODO: PULL dynamic values from config file.
CONNECT_TIMEOUT = 2.0         # seconds to establish TCP
READ_TIMEOUT = 2.0            # seconds to read response
MAX_CONCURRENCY = 10.0        # cap active requests
RETRIES = 2
RETRY_BACKOFF = 1        # slows down retry in seconds

# For Initial Load, and use during Testing
DEVICES_LOADED = naari_config_load()
DEVICEs_IP = [info['address'] for info in DEVICES_LOADED['devices']]


class PollingThreadLock(RuntimeError):
    """ Raised when a polling operation is blocked due to an active polling lock. """
    def __init__(self):
        super().__init__("Polling Fail. Poling lock active")
        time.sleep(1)   # giving it time for devices to catch up


def _timeout() -> httpx.Timeout:
    """ Adds a Timeout parameter to Client connections by httpx. """
    return httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=None, pool=None)


async def _fetch_json( client: httpx.AsyncClient, ip: str, path: str, retries: int = RETRIES, simultaneous_ops : Optional[asyncio.Semaphore] = None,) -> dict[str, Any]:
    """Generic GET->JSON with small retry/backoff and consistent result shape."""
    for attempt in range(retries):
        #print(f"Polling {ip}")
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
                LogManager.print_message(
                    "ValueError [GET] occurred with ip:[%s], path:[%s] >> %s",
                    ip, path, str(e),
                    to_log=TO_LOG,
                    log_level=logging.ERROR
                )
                return {
                    "ip": ip,
                    "error": True,
                    "error_type": "invalid_json",
                    "error_message": str(e)
                }

        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError, httpx.RemoteProtocolError, httpx.RequestError) as err:
            LogManager.print_message(
                "a GET error occurred with ip:[%s], path:[%s] >> %r",
                ip, path, err,
                to_log=TO_LOG,
                log_level=logging.ERROR
            )
            # Decide to retry or fail
            if attempt >= retries - 1:
                LogManager.print_message(
                    "multiple attempts for GET occurred with ip:[%s], path:[%s] >> %r",
                    ip, path, err,
                    to_log=TO_LOG,
                    log_level=logging.ERROR
                )
                return {
                    "ip": ip,
                    "error": True,
                    "error_type": err.__class__.__name__,
                    "error_message": str(err)
                }
            # exponential backoff: base * 2**attempt
            await asyncio.sleep(RETRY_BACKOFF * (2 * attempt))


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


def poll_all_devices(device_address_list: Iterable[str]) -> tuple[list[dict[str, Any]], float]:     #pylint: disable=missing-function-docstring
    # Lock prevents multi connections to be polled and thus clogging up the pipeline
    if not _POLL_LOCK.acquire_lock(blocking=False):     # pylint: disable=no-member
        LogManager.print_message(
            "Polling Getter Lock Triggered. Preventing overload",
            to_log=TO_LOG,
            log_level=logging.ERROR
        )
        raise PollingThreadLock

    # async with lock:
    try:
        if TEST_RUN:
            return read_state_data(), 0
        # Time determine here to push forward interval adjustment settings if needed
        # Aids in app constantly polling if a devices has an error or times out.
        start_time = time.perf_counter()
        results = asyncio.run(run_status(device_address_list))
        total_time = time.perf_counter() - start_time
        return results, total_time
    finally:
        _POLL_LOCK.release()


def poll_device_presets(device_address_list: Iterable[str]):        #pylint: disable=missing-function-docstring
    if TEST_RUN:
        return read_preset_data()
    if not device_address_list:
        LogManager.print_message(
            "No list of IP supplied. Possible Config or supplied error. Need to correct. Reading from file.",
            to_log=TO_LOG,
            log_level=logging.ERROR
        )
        device_address_list = get_devices_ip()
    return asyncio.run(get_presets(device_address_list))


def get_status(entry: dict, path: list[str], default: Any, return_error: bool = False) -> Union[Any, list[str]]:
    """
        A helper function.
        Return device status or traverse a nested dict path.

        - If "error" is set, returns [error_type, error_message].
        - Otherwise, walks the given path of keys and returns the value.
        - If traversal fails, returns the default.
    """
    def deep_get():
        dic_entry = entry
        for key in path:
            if isinstance(dic_entry, dict):
                dic_entry = dic_entry.get(key, default)
            else:
                return default
        return dic_entry

    # if there is no field or entry is empty
    if not entry:
        return {"error": {
            "error_type": "no entry",
            "error_message": "no entry in field"
        }}

    if entry.get("error"):
        if return_error:
            return {"error":{
                "error_type": entry['error_type'],
                "error_message": entry['error_message']
            }}
        return default

    return deep_get()


#---------------Test Dev Only Use Functions------------------------------#
def save_state():
    config = naari_config_load()
    devices_ip = get_devices_ip(config['devices'])
    data, run_time = poll_all_devices(devices_ip)
    with open('../../data.json', 'w') as f:
        return json.dump(data, f, indent=4)


def read_state_data():
    with open('../../data.json', 'r') as file:
        return json.load(file)


def save_presets():
    config = naari_config_load()
    devices_ip = get_devices_ip(config['devices'])
    data = poll_device_presets(devices_ip)
    with open('../../presets.json', "w") as f:
        return json.dump(data, f, indent=4)


def read_preset_data():
    with open('../../presets.json', "r") as file:
        return json.load(file)

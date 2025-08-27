""" Modular contains 'POST' JSON API calls to the WLED devices. """

import time
from typing import Any, Dict

import requests

from naari_app.util.config_builder import DeviceConfig, UISettings

__all__ =[
    'send_device_power_update',
    'brightness_adjustment',
    'send_preset'
]

# Hard coded default values. Here if nothing in config_file to reference.
# Tested and currently safe.
REQUEST_TIMEOUT = 2         # Timeout default so a dead device or device in general doesn't hang up the app
RETRIES = 2
RETRY_BACKOFF = 0.25        # slows down retry in seconds


class PayloadRetryError(RuntimeError):
    """Raised when sending a payload fails after all retry attempts."""
    def __init__(self, url: str, attempts: int, last_exception: BaseException | None = None):
        super().__init__(f"Failed to POST to {url} after {attempts} attempts")
        self.url = url
        self.attempts = attempts
        self.last_exception = last_exception


def _post_with_retries(url: str, json_body: Dict[str, Any], timeout: int = REQUEST_TIMEOUT, retries: int = RETRIES,     # pylint: disable=inconsistent-return-statements
    backoff: float = RETRY_BACKOFF) -> requests.Response:
    """
    POST with small retry/backoff. Retries only on RequestException.

    Raises PayloadRetryError if all attempts fail due to network/timeout errors.
    """
    #last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1, 1):      # starting at 1
        try:
            request_data = requests.post(
                url,
                json=json_body,
                timeout=timeout
            )
            return request_data  # leave status handling to caller
        except requests.RequestException as e:
           # last_exc = e
            if attempt == retries:
                # TODO: replace print with logger when ready
                print(f"[send_payload] POST failed after {attempt} attempts: {e}")
                raise PayloadRetryError(url, attempt, e) from e
            time.sleep(backoff * (2 ** attempt))


def send_payload(device_ip: str, json_body: Dict[str, Any], timeout: int = REQUEST_TIMEOUT, retries: int = RETRIES, backoff: float = RETRY_BACKOFF) -> requests.Response:

    """
    A POST JSON payload to a device's /json/state endpoint

    Parameters:
        device_ip: Target device IP or DNS hostname.
        json_body: JSON API body to send.
        timeout: sets time in seconds on when to trigger POST timeout.
        retries: sets number of attempts request.POST will retry request.
        backoff: sets offset time to add in between retries.

    Returns:
        requests.Response (200, 400, 500)

    Raises:
        PayloadRetryError: If all retry attempts fail due to RequestException.

    """
    url = f"http://{device_ip}/json/state"
    return _post_with_retries(
        url,
        json_body,
        timeout,
        retries,
        backoff
    )


def send_device_update(payload: Dict[str, Any], device_info: DeviceConfig, payload_settings: UISettings) -> requests.Response:
    """
    Send a device update with temporary UDP notification suppression.

    Parameters:
    payload : dict
        JSON body to apply (e.g., {"on": True}, {"bri": 128}).
    device_info : DeviceConfig
        Device configuration, must include the target IP address and optional
        master_sync flag.
    payload_settings : UISettings
        UI-level request settings such as request timeout, retry count,
        and retry backoff.

    Returns:
        requests.Response (200, 400, 500)
    """
    # Desyncs device even if not master. Ensure only one device gets updated
    json_body = {**payload, "udpn": {"send": False}}

    # Zero set to force safe defaults to hard coded values.
    timeout = payload_settings.get('request_timeout', 0)
    retries = payload_settings.get('retries', 0)
    backoff = payload_settings.get('retry_backoff', 0)

    response = send_payload(
        device_ip=device_info.get('address') ,
        json_body=json_body,
        timeout=timeout if isinstance(timeout, int) and timeout > 0 else REQUEST_TIMEOUT,
        retries=retries if isinstance(retries, int) and retries > 0 else RETRIES,
        backoff=backoff if isinstance(backoff, float) and backoff > 0 else RETRY_BACKOFF
    )

    if device_info.get('master_sync', False):
        time.sleep(1)   # Allow Master device to complete the change before re-enabling sync
        response = send_payload(
            device_ip=device_info.get('address'),
            json_body={"udpn": {"send": True}},
            timeout=timeout if isinstance(timeout, int) and timeout > 0 else REQUEST_TIMEOUT,
            retries=retries if isinstance(retries, int) and retries > 0 else RETRIES,
            backoff=backoff if isinstance(backoff, float) and backoff > 0 else RETRY_BACKOFF
        )

    return response


def send_device_power_update(status_update: bool, device_info: DeviceConfig, ui_settings: UISettings ) -> requests.Response:
    """ Turns device power on/off. """
    return send_device_update(
        {"on": status_update},
        device_info,
        ui_settings
    )


def brightness_adjustment(change_value: int, device_info: DeviceConfig, ui_settings: UISettings ) -> requests.Response:
    """ Set device brightness to value set (0-255). """
    return send_device_update(
        {"bri": change_value},
        device_info,
        ui_settings
    )


def send_preset(preset_value: int, device_info: DeviceConfig, ui_settings: UISettings ) -> requests.Response:
    """ Load a given Preset by index number supplied. """
    return send_device_update(
        {"ps": preset_value},
        device_info,
        ui_settings
    )


def test_response():
    """Manual test helper for a single POST to a device (dev-only)."""
    wled_ip = ""
    preset_number = 0

    url = f"http://{wled_ip}/json/state"
    payload = {
        "on": True
    }

    response = requests.post(url, json=payload)

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

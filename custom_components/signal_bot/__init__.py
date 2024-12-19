"""Integration to connect Signal messaging with Home Assistant."""

import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_URL
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    ATTR_GROUP_ID,
    CONF_PHONE_NUMBER,
    DEBUG_DETAILED,
    DEFAULT_API_URL,
    DEFAULT_PHONE_NUMBER,
    DEFAULT_TIMEOUT,
    DOMAIN,
    LOG_PREFIX_SEND,
    LOG_PREFIX_SETUP,
    MESSAGE_TYPE_GROUP,
    MESSAGE_TYPE_INDIVIDUAL,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): cv.string,
                vol.Optional(
                    CONF_PHONE_NUMBER, default=DEFAULT_PHONE_NUMBER
                ): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Signal Bot integration."""
    _LOGGER.debug(f"{LOG_PREFIX_SETUP} Signal Bot integration setup initialized.")
    return True


def prepare_payload(
    message: str, phone_number: str, recipient: str, is_group: bool
) -> dict[str, Any]:
    """Prepare the message payload."""
    if is_group:
        return {
            "message": message,
            "number": phone_number,
            ATTR_GROUP_ID: recipient,
        }
    return {
        "message": message,
        "number": phone_number,
        "recipients": [recipient],
    }


def handle_attachments(payload: dict[str, Any], call_data: dict[str, Any]) -> None:
    """Handle attachment data in the payload."""
    attachments = call_data.get("attachments")
    if attachments and isinstance(attachments, list):
        payload["attachments"] = attachments
    elif attachments:
        _LOGGER.warning(f"{LOG_PREFIX_SEND} 'attachments' must be a list. Ignoring.")

    base64_attachments = call_data.get("base64_attachments")
    if base64_attachments and isinstance(base64_attachments, list):
        payload["base64_attachments"] = base64_attachments
    elif base64_attachments:
        _LOGGER.warning(
            f"{LOG_PREFIX_SEND} 'base64_attachments' must be a list. Ignoring."
        )


async def send_signal_message(
    url: str, payload: dict[str, Any], message_type: str, recipient: str
) -> None:
    """Send message to Signal API."""
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, timeout=DEFAULT_TIMEOUT) as response,
        ):
            if response.status == 201:
                _LOGGER.info(
                    f"{LOG_PREFIX_SEND} %s message sent successfully to %s",
                    message_type,
                    recipient,
                )
            else:
                error_text = await response.text()
                _LOGGER.error(
                    f"{LOG_PREFIX_SEND} Failed to send %s message to %s: %s "
                    f"(HTTP %s)",
                    message_type,
                    recipient,
                    error_text,
                    response.status,
                )
    except TimeoutError:
        _LOGGER.exception(
            f"{LOG_PREFIX_SEND} Timeout occurred while sending %s message to %s",
            message_type,
            recipient,
        )
    except aiohttp.ClientConnectionError:
        _LOGGER.exception(
            f"{LOG_PREFIX_SEND} Connection error to Signal Bot API (%s)",
            url,
        )
    except Exception:
        _LOGGER.exception(
            f"{LOG_PREFIX_SEND} Unexpected error while sending %s message",
            message_type,
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Signal Bot from a config entry."""
    _LOGGER.info(f"{LOG_PREFIX_SETUP} Setting up Signal Bot integration entry.")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    async def handle_send_message(call: ServiceCall) -> None:
        """Handle sending a Signal message."""
        api_url = entry.data.get(CONF_API_URL, DEFAULT_API_URL)
        phone_number = entry.data.get(CONF_PHONE_NUMBER, DEFAULT_PHONE_NUMBER)
        recipient = call.data.get("recipient")
        message = call.data.get("message")
        is_group = call.data.get("is_group", False)

        # Validate required parameters
        if not recipient or not message:
            _LOGGER.error(f"{LOG_PREFIX_SEND} Missing required parameters.")
            return

        # Prepare API URL and payload
        url = f"{api_url.rstrip('/')}/v2/send"
        payload = prepare_payload(message, phone_number, recipient, is_group)
        message_type = MESSAGE_TYPE_GROUP if is_group else MESSAGE_TYPE_INDIVIDUAL

        # Handle attachments
        handle_attachments(payload, call.data)

        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SEND} Sending {message_type} message with payload: %s",
                payload,
            )

        await send_signal_message(url, payload, message_type, recipient)

    # Register the service to send messages
    hass.services.async_register(DOMAIN, "send_message", handle_send_message)

    # Forward the setup to the sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    if DEBUG_DETAILED:
        _LOGGER.debug(f"{LOG_PREFIX_SETUP} Signal Bot setup completed.")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info(f"{LOG_PREFIX_SETUP} Unloading Signal Bot integration entry.")
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SETUP} Signal Bot integration entry "
                "unloaded successfully."
            )
    else:
        _LOGGER.error(
            f"{LOG_PREFIX_SETUP} Failed to unload Signal Bot integration entry."
        )

    return unload_ok

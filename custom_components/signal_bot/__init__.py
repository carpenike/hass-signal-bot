"""Integration to connect Signal messaging with Home Assistant."""

import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    API_ENDPOINT_SEND,
    ATTR_GROUP_ID,
    CONF_API_URL,
    CONF_PHONE_NUMBER,
    DEBUG_DETAILED,
    DEFAULT_API_URL,
    DEFAULT_PHONE_NUMBER,
    DEFAULT_TIMEOUT,
    DOMAIN,
    HTTP_OK,
    LOG_PREFIX_SEND,
    LOG_PREFIX_SETUP,
    MESSAGE_TYPE_GROUP,
    MESSAGE_TYPE_INDIVIDUAL,
)

_LOGGER = logging.getLogger(__name__)

# Service call schema
SEND_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required("recipient"): cv.string,
        vol.Required("message"): cv.string,
        vol.Optional("is_group", default=False): cv.boolean,
        vol.Optional("attachments"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("base64_attachments"): vol.All(cv.ensure_list, [cv.string]),
    }
)

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
    for attachment_type in ["attachments", "base64_attachments"]:
        attachments = call_data.get(attachment_type)
        if attachments:
            if isinstance(attachments, list):
                payload[attachment_type] = attachments
            else:
                _LOGGER.warning(
                    f"{LOG_PREFIX_SEND} '{attachment_type}' must be a list. Ignoring."
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
            if response.status == HTTP_OK:
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

        try:
            call.data = SEND_MESSAGE_SCHEMA(call.data)
        except vol.Invalid:  # Removed 'as err'
            _LOGGER.exception(
                f"{LOG_PREFIX_SEND} Invalid service call parameters"  # Removed: {err}
            )
            return

        recipient = call.data["recipient"]
        message = call.data["message"]
        is_group = call.data["is_group"]

        # Prepare API URL and payload
        url = f"{api_url.rstrip('/')}{API_ENDPOINT_SEND}"
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
    hass.services.async_register(
        DOMAIN, "send_message", handle_send_message, schema=SEND_MESSAGE_SCHEMA
    )

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    if DEBUG_DETAILED:
        _LOGGER.debug(f"{LOG_PREFIX_SETUP} Signal Bot setup completed.")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info(f"{LOG_PREFIX_SETUP} Unloading Signal Bot integration entry.")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])

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

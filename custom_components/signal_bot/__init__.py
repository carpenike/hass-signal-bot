import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_PHONE_NUMBER,
    DEFAULT_API_URL,
    DEFAULT_PHONE_NUMBER,
    LOG_PREFIX_SEND,
)
import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Signal Bot integration."""
    _LOGGER.debug("Signal Bot integration setup initialized.")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Signal Bot from a config entry."""
    _LOGGER.info(f"{LOG_PREFIX_SEND} Setting up Signal Bot integration entry.")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    async def handle_send_message(call: ServiceCall):
        """Handle sending a Signal message."""
        api_url = entry.data.get(CONF_API_URL, DEFAULT_API_URL)
        phone_number = entry.data.get(CONF_PHONE_NUMBER, DEFAULT_PHONE_NUMBER)
        recipient = call.data.get("recipient")
        message = call.data.get("message")
        attachments = call.data.get("attachments")  # List of URLs for attachments
        base64_attachments = call.data.get("base64_attachments")  # Base64 file content

        # Validate required parameters
        if not recipient:
            _LOGGER.error(f"{LOG_PREFIX_SEND} 'recipient' parameter is missing.")
            return
        if not message:
            _LOGGER.error(f"{LOG_PREFIX_SEND} 'message' parameter is missing.")
            return

        # Prepare API URL and payload
        url = f"{api_url.rstrip('/')}/v2/send"
        payload = {
            "recipients": [recipient],  # Recipients must be a list
            "message": message,
            "number": phone_number,
        }

        # Include optional fields if provided
        if attachments:
            if isinstance(attachments, list):
                payload["attachments"] = attachments
            else:
                _LOGGER.warning(
                    f"{LOG_PREFIX_SEND} 'attachments' must be a list. Ignoring."
                )

        if base64_attachments:
            if isinstance(base64_attachments, list):
                payload["base64_attachments"] = base64_attachments
            else:
                _LOGGER.warning(
                    f"{LOG_PREFIX_SEND} 'base64_attachments' must be a list. Ignoring."
                )

        _LOGGER.debug(f"{LOG_PREFIX_SEND} Sending message with payload: %s", payload)

        # Send the message using aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 201:
                        _LOGGER.info(
                            f"{LOG_PREFIX_SEND} Message sent successfully to %s",
                            recipient,
                        )
                    else:
                        error_text = await response.text()
                        _LOGGER.error(
                            f"{LOG_PREFIX_SEND} Failed to send message to %s: %s "
                            f"(HTTP %s)",
                            recipient,
                            error_text,
                            response.status,
                        )
        except asyncio.TimeoutError:
            _LOGGER.error(
                f"{LOG_PREFIX_SEND} Timeout occurred while sending message to %s",
                recipient,
            )
        except aiohttp.ClientConnectionError as conn_err:
            _LOGGER.error(
                f"{LOG_PREFIX_SEND} Connection error to Signal Bot API (%s): %s",
                url,
                conn_err,
            )
        except Exception as e:
            _LOGGER.exception(
                f"{LOG_PREFIX_SEND} Unexpected error while sending message: %s", e
            )

    # Register the service to send messages
    hass.services.async_register(DOMAIN, "send_message", handle_send_message)

    # Forward the setup to the sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    _LOGGER.debug(f"{LOG_PREFIX_SEND} Signal Bot setup completed.")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info(f"{LOG_PREFIX_SEND} Unloading Signal Bot integration entry.")
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    if unload_ok:
        # Remove entry data from hass.data
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.debug(
            f"{LOG_PREFIX_SEND} Signal Bot integration entry unloaded successfully."
        )
    else:
        _LOGGER.error(
            f"{LOG_PREFIX_SEND} Failed to unload Signal Bot integration entry."
        )

    return unload_ok

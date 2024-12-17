import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, CONF_API_URL, CONF_PHONE_NUMBER
import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Signal Bot integration."""
    _LOGGER.debug("Signal Bot integration setup initialized.")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Signal Bot from a config entry."""
    _LOGGER.info("Setting up Signal Bot integration entry.")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    async def handle_send_message(call: ServiceCall):
        """Handle sending a Signal message."""
        api_url = entry.data[CONF_API_URL]
        phone_number = entry.data[CONF_PHONE_NUMBER]
        recipient = call.data.get("recipient")
        message = call.data.get("message")

        # Validate service call parameters
        if not recipient:
            _LOGGER.error("Service call failed: 'recipient' parameter is missing.")
            return
        if not message:
            _LOGGER.error("Service call failed: 'message' parameter is missing.")
            return

        # Update API URL and payload for v2 endpoint
        url = f"{api_url.rstrip('/')}/v2/send"
        payload = {
            "recipients": [recipient],  # Recipients must be a list
            "message": message,
            "number": phone_number,
        }

        _LOGGER.debug("Sending message to %s with payload: %s", recipient, payload)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 201:
                        _LOGGER.info("Message sent successfully to %s", recipient)
                    else:
                        error_text = await response.text()
                        _LOGGER.error(
                            "Failed to send message to %s: %s (HTTP %s)",
                            recipient,
                            error_text,
                            response.status,
                        )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout occurred while sending message to %s", recipient)
        except aiohttp.ClientConnectionError as conn_err:
            _LOGGER.error("Connection error to Signal Bot API (%s): %s", url, conn_err)
        except Exception as e:
            _LOGGER.exception("Unexpected error while sending message: %s", e)

    # Register the service to send messages
    hass.services.async_register(DOMAIN, "send_message", handle_send_message)

    # Forward the setup to the sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    _LOGGER.debug("Signal Bot setup completed.")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Signal Bot integration entry.")
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    if unload_ok:
        # Remove entry data from hass.data
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.debug("Signal Bot integration entry unloaded successfully.")
    else:
        _LOGGER.error("Failed to unload Signal Bot integration entry.")

    return unload_ok

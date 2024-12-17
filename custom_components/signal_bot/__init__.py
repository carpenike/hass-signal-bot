import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN, CONF_API_URL, CONF_PHONE_NUMBER
import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Signal Bot integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Signal Bot from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    async def handle_send_message(call: ServiceCall):
        """Handle sending a Signal message."""
        api_url = entry.data[CONF_API_URL]
        phone_number = entry.data[CONF_PHONE_NUMBER]
        recipient = call.data.get("recipient")
        message = call.data.get("message")

        if not recipient or not message:
            _LOGGER.error("Recipient and message cannot be empty.")
            return

        url = f"{api_url.rstrip('/')}/v1/send"
        payload = {
            "recipient": recipient,
            "message": message,
            "number": phone_number,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 201:
                        _LOGGER.info("Message sent successfully to %s", recipient)
                    else:
                        error_text = await response.text()
                        _LOGGER.error("Failed to send message: %s", error_text)
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout while trying to send message to %s", recipient)
        except aiohttp.ClientConnectionError:
            _LOGGER.error("Failed to connect to the API endpoint: %s", url)
        except Exception as e:
            _LOGGER.error("Unexpected error while sending message: %s", e)

    # Register the service
    hass.services.async_register(DOMAIN, "send_message", handle_send_message)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True

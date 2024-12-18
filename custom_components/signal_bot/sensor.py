from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.network import get_url
from .const import (
    DOMAIN,
    ATTR_LATEST_MESSAGE,
    ATTR_ALL_MESSAGES,
    ATTR_TYPING_STATUS,
    ATTR_FULL_MESSAGE,
    ATTACHMENTS_DIR,
    LOCAL_PATH_PREFIX,
)
from .signal_websocket import SignalWebSocket
from .utils import convert_epoch_to_iso
import aiohttp
import asyncio
import os
import logging

_LOGGER = logging.getLogger(__name__)


async def download_attachment(api_url, attachment_id, filename, hass):
    """Download the attachment from the Signal API and construct a full URL."""
    url = f"{api_url.rstrip('/')}/v1/attachments/{attachment_id}"
    save_dir = hass.config.path(ATTACHMENTS_DIR)  # Use hass.config.path
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    instance_url = get_url(hass, prefer_external=True)
    full_url = f"{instance_url.rstrip('/')}{LOCAL_PATH_PREFIX}/{filename}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(save_path, "wb") as file:
                        file.write(await response.read())
                    _LOGGER.info("Downloaded attachment: %s", save_path)
                    return full_url
                else:
                    _LOGGER.error(
                        "Failed to download attachment: HTTP %s", response.status
                    )
    except Exception as e:
        _LOGGER.error("Error downloading attachment: %s", e)
    return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Signal Bot sensor."""
    api_url = entry.data["api_url"]
    phone_number = entry.data["phone_number"]

    sensor = SignalBotSensor(hass, api_url, phone_number, entry.entry_id)
    async_add_entities([sensor])


class SignalBotSensor(SensorEntity):
    """Sensor to display unread Signal messages and content."""

    def __init__(self, hass, api_url, phone_number, entry_id):
        self._attr_name = "Signal Bot Messages"
        self._attr_state = "No messages yet"
        self._messages = []
        self._api_url = api_url
        self._hass = hass
        self._entry_id = entry_id
        self._ws_manager = SignalWebSocket(api_url, phone_number, self._handle_message)

        self._attr_extra_state_attributes = {
            ATTR_LATEST_MESSAGE: {
                "source": None,
                "message": "No messages yet",
                "timestamp": None,
                "attachments": [],
            },
            ATTR_ALL_MESSAGES: [],
            ATTR_TYPING_STATUS: {},
            ATTR_FULL_MESSAGE: None,
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Signal Bot Hub",
            manufacturer="Signal Bot",
            model="WebSocket Integration",
            entry_type="service",
            configuration_url="https://github.com/carpenike/hass-signal-bot",
        )

    def _handle_message(self, message):
        """Handle incoming WebSocket messages."""
        _LOGGER.info("New message received: %s", message)

        # Store the raw message
        self._attr_extra_state_attributes[ATTR_FULL_MESSAGE] = message

        envelope = message.get("envelope", {})
        data_message = envelope.get("dataMessage")
        typing_message = envelope.get("typingMessage")

        # Handle typing message
        if typing_message:
            self._attr_extra_state_attributes[ATTR_TYPING_STATUS] = {
                "source": envelope.get("source", "unknown"),
                "action": typing_message.get("action", "UNKNOWN"),
                "timestamp": convert_epoch_to_iso(envelope.get("timestamp")),
            }
            self._attr_state = f"Typing: {typing_message.get('action', 'UNKNOWN')}"
            self.schedule_update_ha_state()
            return

        # Handle attachments
        attachments = []
        if data_message and "attachments" in data_message:
            for attachment in data_message["attachments"]:
                attachment_id = attachment.get("id")
                filename = attachment.get("filename", f"attachment_{attachment_id}")
                if attachment_id:
                    full_url = asyncio.run(
                        download_attachment(
                            self._api_url, attachment_id, filename, self._hass
                        )
                    )
                    if full_url:
                        attachments.append({"filename": filename, "url": full_url})

        # Extract message content
        content = (
            data_message.get("message", "").strip() if data_message else ""
        )
        source = envelope.get("source", "unknown")
        timestamp = convert_epoch_to_iso(envelope.get("timestamp"))

        # Set state to the timestamp to ensure uniqueness
        state_content = timestamp

        # Add new message
        new_message = {
            "source": source,
            "message": content if content else "Attachment received",
            "timestamp": timestamp,
            "attachments": attachments,
        }
        self._messages.append(new_message)

        # Update state and attributes
        self._attr_state = state_content
        self._attr_extra_state_attributes[ATTR_LATEST_MESSAGE] = new_message
        self._attr_extra_state_attributes[ATTR_ALL_MESSAGES] = list(self._messages)

        self.schedule_update_ha_state()

    async def async_added_to_hass(self):
        """Start WebSocket connection."""
        _LOGGER.info("Starting Signal WebSocket connection")
        self._ws_manager.connect()

    async def async_will_remove_from_hass(self):
        """Stop WebSocket connection."""
        _LOGGER.info("Stopping Signal WebSocket connection")
        self._ws_manager.stop()

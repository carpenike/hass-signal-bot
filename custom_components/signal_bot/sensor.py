from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import ATTR_LATEST_MESSAGE, ATTR_ALL_MESSAGES
from .signal_websocket import SignalWebSocket
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Signal Bot sensor."""
    api_url = entry.data["api_url"]
    phone_number = entry.data["phone_number"]

    sensor = SignalBotSensor(api_url, phone_number)
    async_add_entities([sensor])


class SignalBotSensor(SensorEntity):
    """Sensor to display unread Signal messages and content."""

    def __init__(self, api_url, phone_number):
        self._attr_name = "Signal Bot Messages"
        self._attr_state = 0  # Initial state: number of messages
        self._messages = []  # List to store messages
        self._attr_extra_state_attributes = {}  # Dictionary for full message content
        self._ws_manager = SignalWebSocket(api_url, phone_number, self._handle_message)

    def _handle_message(self, message):
        """Handle incoming WebSocket messages."""
        _LOGGER.info("New message received: %s", message)

        # Determine message type and extract meaningful content
        message_type = (
            message.get("envelope", {}).get("dataMessage", {}).get("type", "unknown")
        )
        source = message.get("envelope", {}).get("source", "unknown")
        content = (
            message.get("envelope", {})
            .get("dataMessage", {})
            .get("message", "No content")
        )
        timestamp = message.get("envelope", {}).get("timestamp", "unknown")

        # Add new message to list
        new_message = {
            "type": message_type,
            "source": source,
            "message": content,
            "timestamp": timestamp,
        }
        self._messages.append(new_message)

        # Update the state and attributes
        self._attr_state = len(self._messages)  # State: Total number of messages
        self._attr_extra_state_attributes = {
            ATTR_LATEST_MESSAGE: new_message,
            ATTR_ALL_MESSAGES: self._messages,
        }

        self.schedule_update_ha_state()

    async def async_added_to_hass(self):
        """Start WebSocket connection when the entity is added."""
        _LOGGER.info("Starting Signal WebSocket connection")
        self._ws_manager.connect()

    async def async_will_remove_from_hass(self):
        """Stop WebSocket connection when the entity is removed."""
        _LOGGER.info("Stopping WebSocket connection")
        self._ws_manager.stop()

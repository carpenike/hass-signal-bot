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
        self._attr_state = 0  # Number of unread messages
        self._messages = []  # List to store parsed messages
        self._attr_extra_state_attributes = {}  # Dictionary for full message content
        self._ws_manager = SignalWebSocket(api_url, phone_number, self._handle_message)

    def _handle_message(self, message):
        """Handle incoming WebSocket messages."""
        _LOGGER.debug("New raw message received: %s", message)

        # Safely parse the envelope
        envelope = message.get("envelope", {})
        source = envelope.get("source", "Unknown source")
        timestamp = envelope.get("timestamp", None)

        # Handle dataMessage
        if "dataMessage" in envelope:
            data_message = envelope["dataMessage"]
            parsed_message = {
                "type": "dataMessage",
                "source": source,
                "message": data_message.get("message", "No content"),
                "timestamp": timestamp,
            }
            self._messages.append(parsed_message)
            _LOGGER.info(
                "Data message received from %s: %s", source, parsed_message["message"]
            )

        # Handle typingMessage
        elif "typingMessage" in envelope:
            typing_message = envelope["typingMessage"]
            parsed_message = {
                "type": "typingMessage",
                "source": source,
                "action": typing_message.get("action", "UNKNOWN"),
                "timestamp": typing_message.get("timestamp", timestamp),
            }
            self._messages.append(parsed_message)
            _LOGGER.info(
                "Typing message received from %s: %s", source, parsed_message["action"]
            )

        else:
            _LOGGER.debug("Unknown message type received: %s", envelope)

        # Update state and attributes
        self._attr_state = len(self._messages)
        self._attr_extra_state_attributes = {
            ATTR_LATEST_MESSAGE: (
                self._messages[-1] if self._messages else "No messages"
            ),
            ATTR_ALL_MESSAGES: self._messages,
        }
        self.schedule_update_ha_state()

    async def async_added_to_hass(self):
        """Start WebSocket connection when the entity is added."""
        _LOGGER.info("Starting Signal WebSocket connection")
        self._ws_manager.connect()

    async def async_will_remove_from_hass(self):
        """Stop WebSocket connection when the entity is removed."""
        _LOGGER.info("Stopping Signal WebSocket connection")
        self._ws_manager.stop()

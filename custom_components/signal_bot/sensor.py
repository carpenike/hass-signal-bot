from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from .const import (
    DOMAIN,
    ATTR_LATEST_MESSAGE,
    ATTR_ALL_MESSAGES,
    ATTR_TYPING_STATUS,
)
from .signal_websocket import SignalWebSocket
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Signal Bot sensor."""
    api_url = entry.data["api_url"]
    phone_number = entry.data["phone_number"]

    sensor = SignalBotSensor(api_url, phone_number, entry.entry_id)
    async_add_entities([sensor])


class SignalBotSensor(SensorEntity):
    """Sensor to display unread Signal messages and content."""

    def __init__(self, api_url, phone_number, entry_id):
        self._attr_name = "Signal Bot Messages"
        self._attr_state = 0  # Initial state: number of messages
        self._messages = []  # List to store messages
        self._attr_extra_state_attributes = {}  # Dictionary for full message content
        self._entry_id = entry_id  # Link to config entry for device info
        self._ws_manager = SignalWebSocket(api_url, phone_number, self._handle_message)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link this entity to the Signal Bot hub."""
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

        # Extract message details
        envelope = message.get("envelope", {})
        data_message = envelope.get("dataMessage")
        typing_message = envelope.get("typingMessage")

        # If it's a typing message, store it in a dedicated attribute
        if typing_message:
            typing_action = typing_message.get("action", "UNKNOWN")
            source = envelope.get("source", "unknown")
            self._attr_extra_state_attributes[ATTR_TYPING_STATUS] = {
                "source": source,
                "action": typing_action,
                "timestamp": envelope.get("timestamp", "unknown"),
            }
            _LOGGER.debug(
                "Typing status updated: %s",
                self._attr_extra_state_attributes[ATTR_TYPING_STATUS],
            )
            self.schedule_update_ha_state()
            return  # Exit early, don't add to all_messages

        # Otherwise, handle as a data message
        if data_message:
            message_type = "dataMessage"
            content = data_message.get("message", "No content")
        else:
            message_type = "unknown"
            content = "No content"

        source = envelope.get("source", "unknown")
        timestamp = envelope.get("timestamp", "unknown")

        # Add new message to list
        new_message = {
            "type": message_type,
            "source": source,
            "message": content,
            "timestamp": timestamp,
        }
        self._messages.append(new_message)

        # Update state and attributes
        self._attr_state = content  # State will reflect the latest message content
        self._attr_extra_state_attributes = {
            ATTR_LATEST_MESSAGE: new_message,
            ATTR_ALL_MESSAGES: self._messages,
            ATTR_TYPING_STATUS: self._attr_extra_state_attributes.get(
                ATTR_TYPING_STATUS, {}
            ),
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

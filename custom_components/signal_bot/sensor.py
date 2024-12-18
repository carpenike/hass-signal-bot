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
    ATTR_MESSAGE_TYPE,
    ATTR_GROUP_ID,
    ATTR_GROUP_NAME,
    ATTACHMENTS_DIR,
    LOCAL_PATH_PREFIX,
    LOG_PREFIX_SENSOR,
    SIGNAL_STATE_UNKNOWN,
    SIGNAL_STATE_CONNECTED,
    SIGNAL_STATE_DISCONNECTED,
    SIGNAL_STATE_ERROR,
    MESSAGE_TYPE_TEXT,
    MESSAGE_TYPE_ATTACHMENT,
    MESSAGE_TYPE_TYPING,
    MESSAGE_TYPE_GROUP,
    MESSAGE_TYPE_INDIVIDUAL,
    DEBUG_DETAILED,
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
    save_dir = hass.config.path(ATTACHMENTS_DIR)
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
                    if DEBUG_DETAILED:
                        _LOGGER.debug(
                            f"{LOG_PREFIX_SENSOR} Downloaded attachment: %s", save_path
                        )
                    return full_url
                else:
                    _LOGGER.error(
                        f"{LOG_PREFIX_SENSOR} Failed to download attachment: HTTP %s",
                        response.status,
                    )
    except Exception as e:
        _LOGGER.error(f"{LOG_PREFIX_SENSOR} Error downloading attachment: %s", e)
    return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Signal Bot sensor."""
    _LOGGER.debug(f"{LOG_PREFIX_SENSOR} Setting up Signal Bot sensor")
    api_url = entry.data["api_url"]
    phone_number = entry.data["phone_number"]

    sensor = SignalBotSensor(hass, api_url, phone_number, entry.entry_id)
    async_add_entities([sensor])


class SignalBotSensor(SensorEntity):
    """Sensor to display Signal messages and content."""

    def __init__(self, hass, api_url, phone_number, entry_id):
        """Initialize the sensor."""
        super().__init__()
        self._attr_unique_id = f"signal_bot_{entry_id}"
        self._attr_name = "Signal Bot Messages"
        self._attr_state = SIGNAL_STATE_UNKNOWN
        self._messages = []
        self._api_url = api_url
        self._hass = hass
        self._entry_id = entry_id
        self._available = False
        self._ws_manager = SignalWebSocket(
            api_url, phone_number, self._handle_message, self._handle_status
        )

        self._attr_extra_state_attributes = {
            ATTR_LATEST_MESSAGE: {
                "source": None,
                "message": "No messages yet",
                "timestamp": None,
                "attachments": [],
                "type": MESSAGE_TYPE_TEXT,
            },
            ATTR_ALL_MESSAGES: [],
            ATTR_TYPING_STATUS: {},
            ATTR_FULL_MESSAGE: None,
        }

        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} Sensor initialized with ID: %s", entry_id
            )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        if DEBUG_DETAILED:
            _LOGGER.debug(f"{LOG_PREFIX_SENSOR} Current state: %s", self._attr_state)
        return self._attr_state

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

    def _handle_status(self, status: str):
        """Handle WebSocket connection status changes."""
        status_map = {
            "connected": SIGNAL_STATE_CONNECTED,
            "disconnected": SIGNAL_STATE_DISCONNECTED,
            "error": SIGNAL_STATE_ERROR,
        }
        mapped_status = status_map.get(status, SIGNAL_STATE_UNKNOWN)
        self._available = mapped_status == SIGNAL_STATE_CONNECTED
        self._attr_state = mapped_status

        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} WebSocket status changed to: %s (mapped to: %s)",
                status,
                mapped_status,
            )
        self.schedule_update_ha_state()

    def _handle_message(self, message):
        """Handle incoming WebSocket messages."""
        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} Processing new message, current state: %s",
                self._attr_state,
            )

        # Store the raw message
        self._attr_extra_state_attributes[ATTR_FULL_MESSAGE] = message

        envelope = message.get("envelope", {})
        data_message = envelope.get("dataMessage")
        typing_message = envelope.get("typingMessage")
        receipt_message = envelope.get("receiptMessage")
        timestamp = convert_epoch_to_iso(envelope.get("timestamp"))

        if DEBUG_DETAILED:
            _LOGGER.debug(f"{LOG_PREFIX_SENSOR} Processed timestamp: %s", timestamp)

        # Skip processing if it's a receipt message
        if receipt_message:
            if DEBUG_DETAILED:
                _LOGGER.debug(f"{LOG_PREFIX_SENSOR} Skipping receipt message")
            return

        # Handle typing message
        if typing_message:
            self._attr_extra_state_attributes[ATTR_TYPING_STATUS] = {
                "source": envelope.get("source", "unknown"),
                "action": typing_message.get("action", "UNKNOWN"),
                "timestamp": timestamp,
                "type": MESSAGE_TYPE_TYPING,
            }
            if DEBUG_DETAILED:
                _LOGGER.debug(
                    f"{LOG_PREFIX_SENSOR} Updated typing status without state change"
                )
            self.schedule_update_ha_state()
            return

        # Only process if we have a data message (actual message content)
        if not data_message:
            if DEBUG_DETAILED:
                _LOGGER.debug(f"{LOG_PREFIX_SENSOR} Skipping non-data message")
            return

        # Check if it's a group message
        group_info = data_message.get("groupInfo", {})
        is_group_message = bool(group_info)
        group_id = group_info.get("groupId") if is_group_message else None
        group_name = group_info.get("name") if is_group_message else None

        # Handle attachments
        attachments = []
        has_attachments = False
        if "attachments" in data_message:
            has_attachments = True
            for attachment in data_message["attachments"]:
                attachment_id = attachment.get("id")
                filename = attachment.get("filename", f"attachment_{attachment_id}")
                if attachment_id:
                    full_url = asyncio.create_task(
                        download_attachment(
                            self._api_url, attachment_id, filename, self._hass
                        )
                    )
                    asyncio.get_event_loop().run_until_complete(full_url)
                    if full_url.result():
                        attachments.append(
                            {"filename": filename, "url": full_url.result()}
                        )

        # Extract message content
        content = data_message.get("message", "").strip()
        source = envelope.get("source", "unknown")

        # Add new message with group information
        new_message = {
            "source": source,
            "message": content if content else "Attachment received",
            "timestamp": timestamp,
            "attachments": attachments,
            "type": MESSAGE_TYPE_ATTACHMENT if has_attachments else MESSAGE_TYPE_TEXT,
            ATTR_MESSAGE_TYPE: MESSAGE_TYPE_GROUP if is_group_message else MESSAGE_TYPE_INDIVIDUAL,
        }

        # Add group information if it's a group message
        if is_group_message:
            new_message[ATTR_GROUP_ID] = group_id
            if group_name:
                new_message[ATTR_GROUP_NAME] = group_name

        self._messages.append(new_message)

        # Update state and attributes
        self._attr_state = timestamp
        self._attr_extra_state_attributes[ATTR_LATEST_MESSAGE] = new_message
        self._attr_extra_state_attributes[ATTR_ALL_MESSAGES] = list(self._messages)

        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} Final state update: %s", self._attr_state
            )
        self.schedule_update_ha_state()

    async def async_added_to_hass(self):
        """Start WebSocket connection when added to hass."""
        _LOGGER.info(f"{LOG_PREFIX_SENSOR} Starting Signal WebSocket connection")
        try:
            await self._hass.async_add_executor_job(self._ws_manager.connect)
            if DEBUG_DETAILED:
                _LOGGER.debug(f"{LOG_PREFIX_SENSOR} WebSocket connection established")
        except Exception as e:
            _LOGGER.error(
                f"{LOG_PREFIX_SENSOR} Failed to establish WebSocket connection: %s", e
            )

    async def async_will_remove_from_hass(self):
        """Stop WebSocket connection when removed from hass."""
        _LOGGER.info(f"{LOG_PREFIX_SENSOR} Stopping Signal WebSocket connection")
        await self._hass.async_add_executor_job(self._ws_manager.stop)

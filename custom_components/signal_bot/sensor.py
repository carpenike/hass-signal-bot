"""Manages a sensor entity that displays Signal messages in Home Assistant."""

import logging
from pathlib import Path

import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.network import get_url

from .const import (
    ATTACHMENTS_DIR,
    ATTR_ALL_MESSAGES,
    ATTR_FULL_MESSAGE,
    ATTR_GROUP_ADMINS,
    ATTR_GROUP_BANNED_MEMBERS,
    ATTR_GROUP_BLOCKED,
    ATTR_GROUP_ID,
    ATTR_GROUP_MEMBERS,
    ATTR_GROUP_NAME,
    ATTR_GROUP_PENDING_ADMINS,
    ATTR_GROUP_PENDING_MEMBERS,
    ATTR_LATEST_MESSAGE,
    ATTR_MESSAGE_TYPE,
    ATTR_TYPING_STATUS,
    DEBUG_DETAILED,
    DEFAULT_TIMEOUT,
    DOMAIN,
    LOCAL_PATH_PREFIX,
    LOG_PREFIX_SENSOR,
    MESSAGE_TYPE_ATTACHMENT,
    MESSAGE_TYPE_GROUP,
    MESSAGE_TYPE_INDIVIDUAL,
    MESSAGE_TYPE_TEXT,
    MESSAGE_TYPE_TYPING,
    SIGNAL_STATE_CONNECTED,
    SIGNAL_STATE_DISCONNECTED,
    SIGNAL_STATE_ERROR,
    SIGNAL_STATE_UNKNOWN,
)
from .signal_websocket import SignalWebSocket
from .utils import convert_epoch_to_iso

_LOGGER = logging.getLogger(__name__)


async def download_attachment(api_url, attachment_id, filename, hass):
    """Download the attachment from the Signal API and construct a full URL."""
    url = f"{api_url.rstrip('/')}/v1/attachments/{attachment_id}"
    save_dir = Path(hass.config.path(ATTACHMENTS_DIR))
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename

    instance_url = get_url(hass, prefer_external=True)
    full_url = f"{instance_url.rstrip('/')}{LOCAL_PATH_PREFIX}/{filename}"

    try:
        async with aiohttp.ClientSession() as session, session.get(url) as response:
            if response.status == 200:
                save_path.write_bytes(await response.read())
                if DEBUG_DETAILED:
                    _LOGGER.debug(
                        f"{LOG_PREFIX_SENSOR} Downloaded attachment: %s",
                        save_path,
                    )
                return full_url

            _LOGGER.error(
                f"{LOG_PREFIX_SENSOR} Failed to download attachment: HTTP %s",
                response.status,
            )
    except Exception:
        _LOGGER.exception(f"{LOG_PREFIX_SENSOR} Error downloading attachment")
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
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
            api_url,
            phone_number,
            self.async_handle_message,
            self._handle_status,
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
                f"{LOG_PREFIX_SENSOR} Sensor initialized with ID: %s",
                entry_id,
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
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} Current state: %s",
                self._attr_state,
            )
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

    async def get_group_details(self, group_id: str) -> dict:
        """Fetch group details from Signal API."""
        url = f"{self._api_url.rstrip('/')}/v1/groups/{group_id}"

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(url, timeout=DEFAULT_TIMEOUT) as response,
            ):
                if response.status == 200:
                    group_data = await response.json()
                    if DEBUG_DETAILED:
                        _LOGGER.debug(
                            f"{LOG_PREFIX_SENSOR} Retrieved group details for %s: %s",
                            group_id,
                            group_data,
                        )

                    # Transform the API response into our desired format
                    return {
                        "name": group_data.get("name", ""),
                        "members": [
                            member.get("number")
                            for member in group_data.get("members", [])
                        ],
                        "admins": [
                            admin.get("number")
                            for admin in group_data.get("admins", [])
                        ],
                        "blocked": group_data.get("blocked", []),
                        "pendingMembers": [
                            member.get("number")
                            for member in group_data.get("pendingMembers", [])
                        ],
                        "pendingAdmins": [
                            admin.get("number")
                            for admin in group_data.get("pendingAdmins", [])
                        ],
                        "bannedMembers": group_data.get("banned", []),
                    }

                _LOGGER.error(
                    f"{LOG_PREFIX_SENSOR} Failed to get group details for %s: HTTP %s",
                    group_id,
                    response.status,
                )
                return None

        except TimeoutError:
            _LOGGER.exception(
                f"{LOG_PREFIX_SENSOR} Timeout while fetching group details for %s",
                group_id,
            )
        except Exception:
            _LOGGER.exception(
                f"{LOG_PREFIX_SENSOR} Error fetching group details for %s",
                group_id,
            )
        return None

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
                f"{LOG_PREFIX_SENSOR} WebSocket status changed to: "
                f"%s (mapped to: %s)",
                status,
                mapped_status,
            )
        self.schedule_update_ha_state()

    async def _process_group_message(self, data_message, group_info):
        """Process group message details."""
        group_id = group_info.get("groupId")
        group_details = await self.get_group_details(group_id) if group_id else None
        return group_id, group_details

    async def _process_attachments(self, data_message):
        """Process message attachments."""
        attachments = []
        if "attachments" in data_message:
            for attachment in data_message["attachments"]:
                attachment_id = attachment.get("id")
                filename = attachment.get("filename", f"attachment_{attachment_id}")
                if attachment_id:
                    full_url = await download_attachment(
                        self._api_url,
                        attachment_id,
                        filename,
                        self._hass,
                    )
                    if full_url:
                        attachments.append(
                            {
                                "filename": filename,
                                "url": full_url,
                            }
                        )
        return attachments, bool(attachments)

    def _handle_typing_message(self, envelope, timestamp):
        """Handle typing message updates."""
        typing_message = envelope.get("typingMessage")
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
            return True
        return False

    def _create_message_object(
        self,
        envelope,
        data_message,
        timestamp,
        attachments,
        has_attachments,
        group_id,
        group_details,
    ):
        """Create message object with all details."""
        content = data_message.get("message", "").strip()
        source = envelope.get("source", "unknown")
        is_group_message = bool(group_id)

        new_message = {
            "source": source,
            "message": content if content else "Attachment received",
            "timestamp": timestamp,
            "attachments": attachments,
            "type": MESSAGE_TYPE_ATTACHMENT if has_attachments else MESSAGE_TYPE_TEXT,
            ATTR_MESSAGE_TYPE: (
                MESSAGE_TYPE_GROUP if is_group_message else MESSAGE_TYPE_INDIVIDUAL
            ),
        }

        if is_group_message:
            new_message[ATTR_GROUP_ID] = group_id
            if group_details:
                new_message[ATTR_GROUP_NAME] = group_details.get("name", "")
                new_message[ATTR_GROUP_MEMBERS] = group_details.get("members", [])
                new_message[ATTR_GROUP_ADMINS] = group_details.get("admins", [])
                new_message[ATTR_GROUP_BLOCKED] = group_details.get("blocked", [])
                new_message[ATTR_GROUP_PENDING_MEMBERS] = group_details.get(
                    "pendingMembers", []
                )
                new_message[ATTR_GROUP_PENDING_ADMINS] = group_details.get(
                    "pendingAdmins", []
                )
                new_message[ATTR_GROUP_BANNED_MEMBERS] = group_details.get(
                    "bannedMembers", []
                )

        return new_message

    def _update_state(self, new_message, timestamp):
        """Update sensor state with new message."""
        self._messages.append(new_message)
        self._attr_state = timestamp
        self._attr_extra_state_attributes[ATTR_LATEST_MESSAGE] = new_message
        self._attr_extra_state_attributes[ATTR_ALL_MESSAGES] = list(self._messages)

        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} Final state update: %s",
                self._attr_state,
            )
        self.schedule_update_ha_state()

    async def async_handle_message(self, message):
        """Handle incoming WebSocket messages."""
        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} Processing new message, current state: %s",
                self._attr_state,
            )

        envelope = message.get("envelope", {})
        self._attr_extra_state_attributes[ATTR_FULL_MESSAGE] = message

        # Skip processing if it's a receipt message
        if envelope.get("receiptMessage"):
            if DEBUG_DETAILED:
                _LOGGER.debug(f"{LOG_PREFIX_SENSOR} Skipping receipt message")
            return

        timestamp = convert_epoch_to_iso(envelope.get("timestamp"))
        if self._handle_typing_message(envelope, timestamp):
            return

        data_message = envelope.get("dataMessage")
        if not data_message:
            if DEBUG_DETAILED:
                _LOGGER.debug(f"{LOG_PREFIX_SENSOR} Skipping non-data message")
            return

        group_info = data_message.get("groupInfo", {})
        group_id, group_details = await self._process_group_message(
            data_message, group_info
        )
        attachments, has_attachments = await self._process_attachments(data_message)

        new_message = self._create_message_object(
            envelope,
            data_message,
            timestamp,
            attachments,
            has_attachments,
            group_id,
            group_details,
        )

        self._update_state(new_message, timestamp)

    async def async_added_to_hass(self):
        """Start WebSocket connection when added to hass."""
        _LOGGER.info(f"{LOG_PREFIX_SENSOR} Starting Signal WebSocket connection")
        try:
            await self._hass.async_add_executor_job(self._ws_manager.connect)
            if DEBUG_DETAILED:
                _LOGGER.debug(f"{LOG_PREFIX_SENSOR} WebSocket connection established")
        except Exception:
            _LOGGER.exception(
                f"{LOG_PREFIX_SENSOR} Failed to establish WebSocket connection"
            )

    async def async_will_remove_from_hass(self):
        """Stop WebSocket connection when removed from hass."""
        _LOGGER.info(f"{LOG_PREFIX_SENSOR} Stopping Signal WebSocket connection")
        await self._hass.async_add_executor_job(self._ws_manager.stop)

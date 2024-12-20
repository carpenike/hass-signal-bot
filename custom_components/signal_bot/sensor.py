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
    API_ENDPOINT_ATTACHMENTS,
    API_ENDPOINT_GROUPS,
    ATTACHMENTS_DIR,
    ATTR_ALL_MESSAGES,
    ATTR_FULL_MESSAGE,
    ATTR_LATEST_MESSAGE,
    ATTR_MESSAGE_TYPE,
    ATTR_TYPING_STATUS,
    CONF_API_URL,
    CONF_PHONE_NUMBER,
    DEBUG_DETAILED,
    DEFAULT_TIMEOUT,
    DOMAIN,
    HTTP_OK,
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


async def download_attachment(
    api_url: str, attachment_id: str, filename: str, hass: HomeAssistant
) -> str | None:
    """Download the attachment from the Signal API and construct a full URL."""
    url = f"{api_url.rstrip('/')}{API_ENDPOINT_ATTACHMENTS.format(attachment_id=attachment_id)}"
    save_dir = Path(hass.config.path(ATTACHMENTS_DIR))
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename

    instance_url = get_url(hass, prefer_external=True)
    full_url = f"{instance_url.rstrip('/')}{LOCAL_PATH_PREFIX}/{filename}"

    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(url, timeout=DEFAULT_TIMEOUT) as response,
        ):
            if response.status == HTTP_OK:
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
) -> None:
    """Set up Signal Bot sensor."""
    _LOGGER.debug(f"{LOG_PREFIX_SENSOR} Setting up Signal Bot sensor")
    api_url = entry.data[CONF_API_URL]
    phone_number = entry.data[CONF_PHONE_NUMBER]

    sensor = SignalBotSensor(hass, api_url, phone_number, entry.entry_id)
    async_add_entities([sensor])


class SignalBotSensor(SensorEntity):
    """Sensor to display Signal messages and content."""

    def __init__(
        self, hass: HomeAssistant, api_url: str, phone_number: str, entry_id: str
    ) -> None:
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
                "message_type": MESSAGE_TYPE_INDIVIDUAL,
                "group_id": None,
                "group_name": None,
                "group_members": [],
                "group_admins": [],
                "group_blocked": False,
                "group_pending_invites": [],
                "group_pending_requests": [],
                "group_invite_link": "",
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
    def state(self) -> str:
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

    async def get_group_details(self, group_id: str) -> dict | None:
        """Fetch group details from Signal API."""
        url = f"{self._api_url.rstrip('/')}{API_ENDPOINT_GROUPS.format(phone_number=self._ws_manager.phone_number, group_id=group_id)}"

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(url, timeout=DEFAULT_TIMEOUT) as response,
            ):
                if response.status == HTTP_OK:
                    group_data = await response.json()
                    if DEBUG_DETAILED:
                        _LOGGER.debug(
                            f"{LOG_PREFIX_SENSOR} Retrieved group details for %s: %s",
                            group_id,
                            group_data,
                        )
                    return group_data

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

    def _handle_status(self, status: str) -> None:
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

    async def _process_group_message(
        self, data_message: dict, group_info: dict
    ) -> tuple[str | None, dict | None]:
        """Process group message details."""
        group_id = group_info.get("id")  # This should be the "group.*" formatted ID
        if group_id:
            url = f"{self._api_url.rstrip('/')}/v1/groups/{self._ws_manager.phone_number}/{group_id}"
            try:
                async with (
                    aiohttp.ClientSession() as session,
                    session.get(url, timeout=DEFAULT_TIMEOUT) as response,
                ):
                    if response.status == HTTP_OK:
                        group_details = await response.json()
                        if DEBUG_DETAILED:
                            _LOGGER.debug(
                                f"{LOG_PREFIX_SENSOR} Retrieved group details for %s: %s",
                                group_id,
                                group_details,
                            )
                        return group_id, group_details

                    _LOGGER.error(
                        f"{LOG_PREFIX_SENSOR} Failed to get group details for %s: HTTP %s",
                        group_id,
                        response.status,
                    )
                    return None, None

            except Exception:
                _LOGGER.exception(
                    f"{LOG_PREFIX_SENSOR} Error fetching group details for %s",
                    group_id,
                )
                return None, None

        return None, None

    async def _process_attachments(self, data_message: dict) -> tuple[list, bool]:
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

    def _handle_typing_message(self, envelope: dict, timestamp: str) -> bool:
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
        envelope: dict,
        data_message: dict,
        timestamp: str,
        attachments: list,
        has_attachments: bool,
        group_id: str | None,
        group_details: dict | None,
    ) -> dict:
        """Create message object with all details."""
        content = data_message.get("message", "").strip()
        source = envelope.get("source", "unknown")
        is_group_message = bool(group_id)

        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} Creating message object with group_id: %s, group_details: %s",
                group_id,
                group_details,
            )

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

        # Add group information if it's a group message
        if is_group_message and group_details:
            group_info = {
                "group_id": group_id,
                "group_name": group_details.get("name"),
                "group_members": group_details.get("members", []),
                "group_admins": group_details.get("admins", []),
                "group_blocked": group_details.get("blocked", False),
                "group_pending_invites": group_details.get("pending_invites", []),
                "group_pending_requests": group_details.get("pending_requests", []),
                "group_invite_link": group_details.get("invite_link", ""),
            }
            new_message.update(group_info)

            if DEBUG_DETAILED:
                _LOGGER.debug(
                    f"{LOG_PREFIX_SENSOR} Added group details to message: %s",
                    new_message,
                )

        return new_message

    def _update_state(self, new_message: dict, timestamp: str) -> None:
        """Update sensor state with new message."""
        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} Updating state with message: %s",
                new_message,
            )

        self._messages.append(new_message)
        self._attr_state = timestamp
        self._attr_extra_state_attributes[ATTR_LATEST_MESSAGE] = new_message
        self._attr_extra_state_attributes[ATTR_ALL_MESSAGES] = list(self._messages)

        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_SENSOR} Updated state attributes: %s",
                self._attr_extra_state_attributes,
            )
        self.schedule_update_ha_state()

    async def async_handle_message(self, message: dict) -> None:
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

    async def async_added_to_hass(self) -> None:
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

    async def async_will_remove_from_hass(self) -> None:
        """Stop WebSocket connection when removed from hass."""
        _LOGGER.info(f"{LOG_PREFIX_SENSOR} Stopping Signal WebSocket connection")
        await self._hass.async_add_executor_job(self._ws_manager.stop)

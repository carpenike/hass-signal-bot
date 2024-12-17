"""Constants for the Signal Bot integration."""

# Integration domain
DOMAIN = "signal_bot"

# Configuration keys (used to access user-provided values in ConfigEntry)
CONF_API_URL = "api_url"
CONF_PHONE_NUMBER = "phone_number"

# Sensor attribute names
ATTR_LATEST_MESSAGE = "latest_message"
ATTR_ALL_MESSAGES = "all_messages"
ATTR_TYPING_STATUS = "typing_status"  # New constant for typing messages

# Event names (reserved for future use)
EVENT_SIGNAL_MESSAGE = "signal_message_received"

# Log message prefixes
LOG_PREFIX_WS = "[SignalBot WebSocket]"
LOG_PREFIX_SEND = "[SignalBot SendMessage]"

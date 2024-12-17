"""Constants for the Signal Bot integration."""

# Integration domain
DOMAIN = "signal_bot"

# Configuration keys (used to access user-provided values in ConfigEntry)
CONF_API_URL = "api_url"           # Key for WebSocket API URI
CONF_PHONE_NUMBER = "phone_number" # Key for Signal phone number

# Sensor attribute names
ATTR_LATEST_MESSAGE = "latest_message"  # Attribute to hold the latest message
ATTR_ALL_MESSAGES = "all_messages"      # Attribute to store all received messages

# Default values (optional, for testing or fallback purposes)
DEFAULT_API_URL = "http://localhost:8080/"   # Default API URL
DEFAULT_PHONE_NUMBER = "+0000000000"         # Default phone number for testing

# Event names (if needed for later use)
EVENT_SIGNAL_MESSAGE = "signal_message_received"

# Log message prefixes
LOG_PREFIX_WS = "[SignalBot WebSocket]"
LOG_PREFIX_SEND = "[SignalBot SendMessage]"

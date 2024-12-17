"""Constants for the Signal Bot integration."""

# Integration domain
DOMAIN = "signal_bot"

# Configuration keys (used to access user-provided values in ConfigEntry)
CONF_API_URL = "api_url"
CONF_PHONE_NUMBER = "phone_number"

# Sensor attribute names
ATTR_LATEST_MESSAGE = "latest_message"  # Stores the most recent message
ATTR_ALL_MESSAGES = "all_messages"  # List of all received messages
ATTR_TYPING_STATUS = "typing_status"  # Tracks typing actions (STARTED/STOPPED)
ATTR_FULL_MESSAGE = "full_message"  # Stores the entire raw message payload

# WebSocket-related constants
WS_RECEIVE_ENDPOINT = "/v1/receive/{phone_number}"  # WebSocket receive path
WS_HEALTH_ENDPOINT = "/v1/health"  # Health check path
DEFAULT_RECONNECT_INTERVAL = 5  # Default time in seconds for reconnection backoff

# Attachment paths
ATTACHMENTS_DIR = "www/signal_bot"
LOCAL_PATH_PREFIX = "/local/signal_bot"

# Event names (reserved for future use)
EVENT_SIGNAL_MESSAGE = "signal_message_received"

# Default values (used as fallbacks where necessary)
DEFAULT_API_URL = "http://localhost:8080"  # Default API URL for local Signal CLI
DEFAULT_PHONE_NUMBER = "+0000000000"  # Placeholder phone number

# Log message prefixes
LOG_PREFIX_WS = "[SignalBot WebSocket]"
LOG_PREFIX_SEND = "[SignalBot SendMessage]"
LOG_PREFIX_UTILS = "[SignalBot Utils]"

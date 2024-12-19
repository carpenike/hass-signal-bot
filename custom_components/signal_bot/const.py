"""Constants for the Signal Bot integration."""

# Integration domain
DOMAIN = "signal_bot"

# Configuration and default values
CONF_API_URL = "api_url"
CONF_PHONE_NUMBER = "phone_number"
DEFAULT_API_URL = "http://localhost:8080"
DEFAULT_PHONE_NUMBER = "+0000000000"

# API endpoints and routes
API_ENDPOINT_RECEIVE = "/v1/receive/{phone_number}"  # Updated format
API_ENDPOINT_HEALTH = "/v1/health"
API_ENDPOINT_GROUPS = "/v1/groups/{phone_number}/{group_id}"
API_ENDPOINT_ATTACHMENTS = "/v1/attachments/{attachment_id}"
API_ENDPOINT_SEND = "/v1/send"

# HTTP Response codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400

# Sensor attribute names
ATTR_LATEST_MESSAGE = "latest_message"
ATTR_ALL_MESSAGES = "all_messages"
ATTR_TYPING_STATUS = "typing_status"
ATTR_FULL_MESSAGE = "full_message"
ATTR_MESSAGE_TYPE = "message_type"
ATTR_GROUP_ID = "group_id"
ATTR_GROUP_NAME = "group_name"
ATTR_GROUP_MEMBERS = "group_members"
ATTR_GROUP_ADMINS = "group_admins"
ATTR_GROUP_BLOCKED = "group_blocked"
ATTR_GROUP_PENDING_MEMBERS = "group_pending_members"
ATTR_GROUP_PENDING_ADMINS = "group_pending_admins"
ATTR_GROUP_BANNED_MEMBERS = "group_banned_members"

# Message types
MESSAGE_TYPE_GROUP = "group"
MESSAGE_TYPE_INDIVIDUAL = "individual"
MESSAGE_TYPE_TEXT = "text"
MESSAGE_TYPE_ATTACHMENT = "attachment"
MESSAGE_TYPE_TYPING = "typing"

# WebSocket-related constants
DEFAULT_RECONNECT_INTERVAL = 5  # seconds
MAX_RECONNECT_DELAY = 300  # seconds
WS_TIMEOUT = 10  # seconds for WebSocket operations

# Attachment paths
ATTACHMENTS_DIR = "www/signal_bot"
LOCAL_PATH_PREFIX = "/local/signal_bot"

# Event names
EVENT_SIGNAL_MESSAGE = "signal_message_received"

# Log message prefixes
LOG_PREFIX_WS = "[SignalBot WebSocket]"
LOG_PREFIX_SEND = "[SignalBot SendMessage]"
LOG_PREFIX_UTILS = "[SignalBot Utils]"
LOG_PREFIX_SENSOR = "[SignalBot Sensor]"
LOG_PREFIX_SETUP = "[SignalBot Setup]"

# State-related constants
SIGNAL_STATE_UNKNOWN = "unknown"
SIGNAL_STATE_CONNECTED = "connected"
SIGNAL_STATE_DISCONNECTED = "disconnected"
SIGNAL_STATE_ERROR = "error"

# Update intervals and timeouts
DEFAULT_UPDATE_INTERVAL = 60  # seconds
DEFAULT_TIMEOUT = 10  # seconds

# Debug levels
DEBUG_DETAILED = False  # Set to True to enable very detailed debug logging

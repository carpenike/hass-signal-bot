from datetime import datetime, timezone
from .const import LOG_PREFIX_UTILS
import logging

_LOGGER = logging.getLogger(__name__)


def convert_epoch_to_iso(timestamp_ms):
    """Convert epoch timestamp in milliseconds to ISO 8601 format."""
    if not timestamp_ms:
        return None
    try:
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        return timestamp.isoformat()
    except Exception as e:
        _LOGGER.error(
            f"{LOG_PREFIX_UTILS} Failed to convert timestamp %s: %s",
            timestamp_ms,
            e,
        )
        return None

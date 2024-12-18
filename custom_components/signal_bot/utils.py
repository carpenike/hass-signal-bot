from datetime import datetime, timezone
from .const import (
    LOG_PREFIX_UTILS,
    DEBUG_DETAILED,
)
import logging

_LOGGER = logging.getLogger(__name__)


def convert_epoch_to_iso(timestamp_ms):
    """Convert epoch timestamp in milliseconds to ISO 8601 format."""
    if not timestamp_ms:
        _LOGGER.warning(f"{LOG_PREFIX_UTILS} Received empty timestamp")
        return None
    try:
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        iso_timestamp = timestamp.isoformat()
        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_UTILS} Converting timestamp %s to %s",
                timestamp_ms,
                iso_timestamp,
            )
        return iso_timestamp
    except (TypeError, ValueError) as e:
        _LOGGER.error(
            f"{LOG_PREFIX_UTILS} Failed to convert timestamp %s: %s",
            timestamp_ms,
            str(e),
        )
        return None
    except Exception as e:
        _LOGGER.error(
            f"{LOG_PREFIX_UTILS} Unexpected error converting timestamp %s: %s",
            timestamp_ms,
            str(e),
        )
        return None

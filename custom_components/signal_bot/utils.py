"""Utility functions for Signal Bot integration."""

from datetime import UTC, datetime
import logging

from .const import DEBUG_DETAILED, LOG_PREFIX_UTILS

_LOGGER = logging.getLogger(__name__)


def convert_epoch_to_iso(timestamp_ms: int | float | None) -> str | None:
    """Convert epoch timestamp in milliseconds to ISO 8601 format.

    Args:
        timestamp_ms: Unix epoch timestamp in milliseconds.

    Returns:
        ISO 8601 formatted timestamp string or None if conversion fails.

    """
    if timestamp_ms is None:
        _LOGGER.warning(f"{LOG_PREFIX_UTILS} Received None timestamp")
        return None

    if not isinstance(timestamp_ms, int | float):
        _LOGGER.error(
            f"{LOG_PREFIX_UTILS} Invalid timestamp type: %s, expected int or float",
            type(timestamp_ms),
        )
        return None

    try:
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC)
        iso_timestamp = timestamp.isoformat()

        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_UTILS} Converting timestamp %s to %s",
                timestamp_ms,
                iso_timestamp,
            )
    except (TypeError, ValueError):
        _LOGGER.exception(
            f"{LOG_PREFIX_UTILS} Failed to convert timestamp: %s",
            timestamp_ms,
        )
        return None
    except Exception:
        _LOGGER.exception(
            f"{LOG_PREFIX_UTILS} Unexpected error converting timestamp: %s",
            timestamp_ms,
        )
        return None
    else:
        return iso_timestamp

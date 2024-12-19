"""Config flow handlers for setting up Signal Bot integration in Home Assistant UI."""

import logging
import re
from typing import Any

import aiohttp
from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN, WS_HEALTH_ENDPOINT

_LOGGER = logging.getLogger(__name__)

# Schema for the setup form
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("api_url"): str,  # WebSocket API URL input
        vol.Required("phone_number"): str,  # Signal phone number input
    }
)

# Regular expression to validate phone numbers with country code
PHONE_NUMBER_REGEX = re.compile(r"^\+\d{1,15}$")  # + followed by 1-15 digits


class SignalBotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Signal Bot integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the setup form."""
        errors = {}

        if user_input is not None:
            api_url = user_input["api_url"].rstrip("/")  # Remove trailing slash
            phone_number = user_input["phone_number"]
            health_endpoint = f"{api_url}{WS_HEALTH_ENDPOINT}"

            # Validate API URL format
            if not (api_url.startswith("http://") or api_url.startswith("https://")):
                errors["api_url"] = "invalid_api_url"
                _LOGGER.error("API URL must start with http:// or https://")

            # Validate phone number format
            if not PHONE_NUMBER_REGEX.match(phone_number):
                errors["phone_number"] = "invalid_phone_number"
                _LOGGER.error("Invalid phone number format: %s", phone_number)

            # Test the health endpoint
            if not errors:
                _LOGGER.debug("Testing Signal Bot health endpoint: %s", health_endpoint)
                try:
                    async with (
                        aiohttp.ClientSession() as session,
                        session.get(health_endpoint, timeout=5) as response,
                    ):
                        if response.status in (200, 204):
                            _LOGGER.info(
                                "Successfully connected to Signal Bot health "
                                "endpoint: %s",
                                health_endpoint,
                            )
                        else:
                            _LOGGER.error(
                                "Unexpected HTTP response: %s", response.status
                            )
                            errors["base"] = "invalid_response"
                except TimeoutError:
                    _LOGGER.exception("Connection to %s timed out.", health_endpoint)
                    errors["base"] = "timeout"
                except aiohttp.ClientConnectionError:
                    _LOGGER.exception(
                        "Failed to connect to %s. Connection refused",
                        health_endpoint,
                    )
                    errors["base"] = "connection_refused"
                except Exception:
                    _LOGGER.exception(
                        "An unexpected error occurred during health check"
                    )
                    errors["base"] = "unknown_error"

            if not errors:
                # Proceed with successful setup
                _LOGGER.info("Signal Bot setup completed successfully.")
                return self.async_create_entry(
                    title="Signal Bot",
                    data={"api_url": api_url, "phone_number": phone_number},
                )

        # Return form with errors if validation or health check fails
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )

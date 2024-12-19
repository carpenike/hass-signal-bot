"""Config flow handlers for setting up Signal Bot integration in Home Assistant UI."""

import logging
import re
from typing import Any

import aiohttp
from homeassistant import config_entries
import voluptuous as vol

from .const import (
    API_ENDPOINT_HEALTH,
    CONF_API_URL,
    CONF_PHONE_NUMBER,
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    HTTP_OK,
    LOG_PREFIX_SETUP,
)

_LOGGER = logging.getLogger(__name__)

# Schema for the setup form
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
        vol.Required(CONF_PHONE_NUMBER): str,
    }
)

# Regular expression to validate phone numbers with country code
PHONE_NUMBER_REGEX = re.compile(r"^\+\d{1,15}$")  # + followed by 1-15 digits


class SignalBotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Signal Bot integration."""

    VERSION = 1

    async def validate_input(self, api_url: str, phone_number: str) -> dict[str, str]:
        """Validate the user input."""
        errors = {}

        # Validate API URL format
        if not (api_url.startswith("http://") or api_url.startswith("https://")):
            errors[CONF_API_URL] = "invalid_api_url"
            _LOGGER.error(
                f"{LOG_PREFIX_SETUP} API URL must start with http:// or https://"
            )

        # Validate phone number format
        if not PHONE_NUMBER_REGEX.match(phone_number):
            errors[CONF_PHONE_NUMBER] = "invalid_phone_number"
            _LOGGER.error(
                f"{LOG_PREFIX_SETUP} Invalid phone number format: %s", phone_number
            )

        return errors

    async def check_api_health(self, api_url: str) -> dict[str, str]:
        """Test the health endpoint."""
        errors = {}
        health_endpoint = f"{api_url}{API_ENDPOINT_HEALTH}"

        _LOGGER.debug(
            f"{LOG_PREFIX_SETUP} Testing Signal Bot health endpoint: %s",
            health_endpoint,
        )

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(health_endpoint, timeout=DEFAULT_TIMEOUT) as response,
            ):
                if response.status in (HTTP_OK, 204):
                    _LOGGER.info(
                        f"{LOG_PREFIX_SETUP} Successfully connected to Signal Bot "
                        "health endpoint: %s",
                        health_endpoint,
                    )
                else:
                    _LOGGER.error(
                        f"{LOG_PREFIX_SETUP} Unexpected HTTP response: %s",
                        response.status,
                    )
                    errors["base"] = "invalid_response"
        except TimeoutError:
            _LOGGER.exception(
                f"{LOG_PREFIX_SETUP} Connection to %s timed out.", health_endpoint
            )
            errors["base"] = "timeout"
        except aiohttp.ClientConnectionError:
            _LOGGER.exception(
                f"{LOG_PREFIX_SETUP} Failed to connect to %s. Connection refused",
                health_endpoint,
            )
            errors["base"] = "connection_refused"
        except Exception:
            _LOGGER.exception(
                f"{LOG_PREFIX_SETUP} An unexpected error occurred during health check"
            )
            errors["base"] = "unknown_error"

        return errors

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the setup form."""
        errors = {}

        if user_input is not None:
            api_url = user_input[CONF_API_URL].rstrip("/")
            phone_number = user_input[CONF_PHONE_NUMBER]

            # Validate input format
            errors.update(await self.validate_input(api_url, phone_number))

            # Test the health endpoint if basic validation passed
            if not errors:
                errors.update(await self.check_api_health(api_url))

            if not errors:
                # Proceed with successful setup
                _LOGGER.info(
                    f"{LOG_PREFIX_SETUP} Signal Bot setup completed successfully."
                )
                return self.async_create_entry(
                    title="Signal Bot",
                    data={
                        CONF_API_URL: api_url,
                        CONF_PHONE_NUMBER: phone_number,
                    },
                )

        # Return form with errors if validation or health check fails
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )

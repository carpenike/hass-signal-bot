import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN
import logging
import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)

# Schema for the setup form
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("api_url"): str,  # WebSocket URL input
        vol.Required("phone_number"): str,  # Phone number input
    }
)


class SignalBotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Signal Bot integration."""

    async def async_step_user(self, user_input=None):
        """Handle the setup form."""
        errors = {}

        if user_input is not None:
            api_url = user_input["api_url"].rstrip("/")  # Remove trailing slash if any
            phone_number = user_input["phone_number"]
            health_endpoint = f"{api_url}/v1/health"

            # Test the health endpoint using aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(health_endpoint, timeout=5) as response:
                        if response.status in (
                            200,
                            204,
                        ):  # Accept 200 and 204 as healthy
                            _LOGGER.info(
                                "Successfully connected to Signal API health "
                                "endpoint: %s",
                                health_endpoint,
                            )
                        else:
                            _LOGGER.error(
                                "Unexpected HTTP response: %s", response.status
                            )
                            errors["base"] = "invalid_response"
            except asyncio.TimeoutError:
                _LOGGER.error(
                    "Connection to %s timed out.",
                    health_endpoint,
                )
                errors["base"] = "timeout"
            except aiohttp.ClientConnectionError:
                _LOGGER.error(
                    "Failed to connect to %s. Connection refused.",
                    health_endpoint,
                )
                errors["base"] = "connection_refused"
            except Exception as e:
                _LOGGER.error(
                    "An unexpected error occurred: %s",
                    e,
                )
                errors["base"] = "unknown_error"

            if not errors:
                # Proceed with successful setup
                return self.async_create_entry(
                    title="Signal Bot",
                    data={"api_url": api_url, "phone_number": phone_number},
                )

        # Return form with errors if health check fails
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )

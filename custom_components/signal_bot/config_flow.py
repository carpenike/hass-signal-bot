import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

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
            api_url = user_input["api_url"]
            phone_number = user_input["phone_number"]

            # Test the WebSocket connection (optional)
            try:
                import websocket

                ws = websocket.create_connection(api_url)
                ws.close()
                return self.async_create_entry(title="Signal Bot", data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )

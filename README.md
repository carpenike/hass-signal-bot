# Signal Bot Integration for Home Assistant

The **Signal Bot Integration** enables Home Assistant to interact with a Signal CLI REST API instance. This integration uses WebSockets to receive real-time messages and exposes services to send Signal messages with optional attachments.

---

## Features

- **Real-Time Message Reception**: Receive Signal messages via WebSocket and display them as a sensor in Home Assistant.
- **Message State Tracking**: Track the latest message, typing indicators, and maintain a history of messages.
- **Send Messages**: Send messages, including optional attachments (base64-encoded data), directly from Home Assistant.
- **Fully Configurable**: Input the Signal API URL and phone number during setup.

---

## Prerequisites

Before installing this integration, ensure the following:

1. **Signal CLI REST API** is up and running.

   - Documentation: [Signal CLI REST API](https://bbernhard.github.io/signal-cli-rest-api/)
   - Example Docker command to run it locally:
     ```bash
     docker run -d --name signal-cli-rest-api -p 8080:8080 bbernhard/signal-cli-rest-api:latest
     ```

2. **Home Assistant** is installed and running.

3. **`homeassistant.external_url`** is configured in your `configuration.yaml`. This is required for generating valid attachment URLs when sending messages.

   Example:

   ```yaml
   homeassistant:
     external_url: "https://your-homeassistant-domain.com"
   ```

   Replace `https://your-homeassistant-domain.com` with the actual external URL for your Home Assistant instance.

4. The Signal CLI REST API endpoint must be accessible from the Home Assistant server.

---

## Installation

### Via HACS (Recommended)

1. Go to **HACS** in your Home Assistant UI.
2. Navigate to **Integrations** > **Custom Repositories**.
3. Add the following repository URL as a custom repository:
   ```
   https://github.com/carpenike/hass-signal-bot
   ```
   - Set the category as **Integration**.
4. After adding the repository, go to **Explore & Download Repositories**.
5. Search for `Signal Bot` and install it.
6. Restart Home Assistant after installation.

---

### Manual Installation

1. Download the repository as a ZIP file.
2. Extract the contents into:
   ```
   /config/custom_components/signal_bot/
   ```
3. Restart Home Assistant.

---

## Configuration

### 1. Add the Integration

1. In Home Assistant, navigate to:
   ```
   Settings > Devices & Services > Add Integration
   ```
2. Search for **Signal Bot** and select it.
3. Enter the following details:

   - **API URL**: WebSocket-enabled Signal REST API endpoint (e.g., `http://signal-cli:8080`).
   - **Phone Number**: Your registered Signal phone number, including the country code (e.g., `+1234567890`).

4. Click **Submit**.

---

### 2. Sending Messages

The integration registers a `send_message` service under `signal_bot`. You can call this service in automations or scripts.

#### **Service Example: Sending a Simple Message**

```yaml
service: signal_bot.send_message
data:
  recipient: "+1234567890"
  message: "Hello, this is a test message!"
```

#### **Service Example: Sending Attachments**

You can send attachments via base64.

- **Using Base64 Attachments**:

```yaml
service: signal_bot.send_message
data:
  recipient: "+1234567890"
  message: "Here's an image!"
  base64_attachments:
    - "data:image/png;filename=test.png;base64,<BASE64_ENCODED_STRING>"
```

---

## Entities

Once configured, this integration creates the following entities:

| **Entity ID**                | **Description**                                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| `sensor.signal_bot_messages` | Displays the content of the latest message. Tracks typing indicators and maintains a message history. |

### **State Attributes**

| **Attribute**    | **Description**                          |
| ---------------- | ---------------------------------------- |
| `latest_message` | Details of the most recent message.      |
| `all_messages`   | A list of all received messages.         |
| `typing_status`  | Displays typing actions (e.g., STARTED). |
| `full_message`   | The raw WebSocket payload for debugging. |

---

## Example Automation

This example sends an alert via Signal when a door sensor triggers:

```yaml
automation:
  - alias: "Send Signal Alert on Door Open"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    action:
      - service: signal_bot.send_message
        data:
          recipient: "+1234567890"
          message: "Alert! The front door has been opened."
```

---

## Development

### Set up development environment

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - Unix/macOS: `source venv/bin/activate`
4. Install development dependencies: `pip install -r requirements-dev.txt`
5. Install pre-commit hooks: `pre-commit install`

### VS Code Development

This repository includes recommended VS Code settings and extensions. When you open this repository in VS Code, you should be prompted to install the recommended extensions. If not, you can:

1. Open the Extensions view (`Ctrl+Shift+X` or `Cmd+Shift+X`)
2. Search for `@recommended`
3. Install "Workspace Recommended Extensions"

#### Recommended Extensions

- **Python Essentials**

  - Python (`ms-python.python`)
  - Black Formatter (`ms-python.black-formatter`)
  - Ruff (`charliermarsh.ruff`)
  - Pylance (`ms-python.vscode-pylance`)
  - Python Debugger (`ms-python.debugpy`)

- **File Format Support**

  - YAML (`redhat.vscode-yaml`)
  - Prettier (`esbenp.prettier-vscode`)
  - Even Better TOML (`tamasfe.even-better-toml`)

- **GitHub Integration**

  - GitHub Actions (`github.vscode-github-actions`)
  - GitHub Pull Requests (`GitHub.vscode-pull-request-github`)
  - GitHub Copilot (`GitHub.copilot`) - Optional, if you use Copilot

- **Development Helpers**
  - Code Spell Checker (`streetsidesoftware.code-spell-checker`)
  - GitLens (`eamodio.gitlens`)
  - Home Assistant (`keesschollaart.vscode-home-assistant`)

#### VS Code Settings

The repository includes workspace-specific VS Code settings that:

- Enable format on save
- Configure Black as the Python formatter
- Enable Ruff for linting and import sorting
- Set up consistent file formatting (final newline, trim trailing whitespace)

These settings are automatically applied when you open the repository in VS Code.

### Pre-commit Hooks

This repository uses pre-commit hooks to ensure code quality and consistency. The following hooks are configured:

- Black: Python code formatting
- Ruff: Python linting and import sorting
- Various file checks (YAML, JSON, TOML)
- Trailing whitespace removal
- End of file fixing
- Spell checking
- Prettier for YAML, JSON, and Markdown formatting

The hooks will run automatically on every commit. You can also run them manually:

````bash
pre-commit run --all-files

---

## Troubleshooting

### Common Errors

1. **`cannot_connect`**:
   - Verify the Signal CLI REST API URL is correct and accessible from the Home Assistant server.
   - Test the health endpoint:
     ```
     curl http://signal-cli:8080/v1/health
     ```

2. **`invalid_phone_number`**:
   - Ensure the phone number includes the country code (e.g., `+1234567890`).

3. **WebSocket Errors**:
   - Check Signal CLI REST API logs for connection issues.

4. **Attachments Not Accessible**:
   - Ensure `homeassistant.external_url` is configured and accessible.

---

## Known Issues

- Sending large base64 attachments may fail due to API limits.
- Ensure the Signal CLI REST API is configured with sufficient memory and storage for attachments.

---

## Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.signal_bot: debug
````

---

## Credits

- **Signal CLI REST API** by [bbernhard](https://bbernhard.github.io/signal-cli-rest-api/)
- Integration developed and maintained by [@carpenike](https://github.com/carpenike).

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support

For issues, questions, or feature requests, please visit the [GitHub Issues](https://github.com/carpenike/hass-signal-bot/issues) page.

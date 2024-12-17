import threading
import websocket
import json
import time
import logging

_LOGGER = logging.getLogger(__name__)

class SignalWebSocket:
    """Manage WebSocket connection to Signal CLI REST API."""

    def __init__(self, api_url, phone_number, message_callback):
        self._ws_url = f"{api_url.rstrip('/')}/v1/receive/{phone_number}"
        self._message_callback = message_callback  # Function to handle incoming messages
        self._thread = None
        self._stop_event = threading.Event()

    def connect(self):
        """Start the WebSocket connection."""
        _LOGGER.info("Connecting to Signal WebSocket: %s", self._ws_url)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """WebSocket connection loop."""
        while not self._stop_event.is_set():
            try:
                ws = websocket.WebSocketApp(
                    self._ws_url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                ws.run_forever()
            except Exception as e:
                _LOGGER.error("WebSocket error: %s. Reconnecting in 5 seconds...", e)
                time.sleep(5)  # Reconnect delay

    def _on_message(self, ws, message):
        """Handle incoming WebSocket message."""
        _LOGGER.debug("Received WebSocket message: %s", message)
        try:
            data = json.loads(message)
            self._message_callback(data)
        except json.JSONDecodeError:
            _LOGGER.error("Failed to decode message: %s", message)

    def _on_error(self, ws, error):
        _LOGGER.error("WebSocket error: %s", error)

    def _on_close(self, ws, close_status_code, close_msg):
        _LOGGER.warning("WebSocket connection closed")

    def stop(self):
        """Stop the WebSocket connection."""
        _LOGGER.info("Stopping WebSocket connection")
        self._stop_event.set()

import threading
import websocket
import json
import logging
import time
from .const import WS_RECEIVE_ENDPOINT, LOG_PREFIX_WS

_LOGGER = logging.getLogger(__name__)

RECONNECT_INTERVAL = 5  # Time in seconds between reconnection attempts


class SignalWebSocket:
    """Manage WebSocket connection to Signal CLI REST API."""

    def __init__(self, api_url, phone_number, message_callback):
        """Initialize the WebSocket manager."""
        # Ensure the API URL uses ws:// or wss://
        ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")
        self._ws_url = f"{ws_url.rstrip('/')}{WS_RECEIVE_ENDPOINT.format(phone_number=phone_number)}"
        self._message_callback = message_callback  # Callback to handle incoming messages
        self._thread = None
        self._stop_event = threading.Event()
        self._ws = None  # Store WebSocketApp instance for clean shutdown

    def connect(self):
        """Start the WebSocket connection."""
        if self._thread and self._thread.is_alive():
            _LOGGER.warning(f"{LOG_PREFIX_WS} WebSocket thread is already running.")
            return

        _LOGGER.info(f"{LOG_PREFIX_WS} Connecting to Signal WebSocket: %s", self._ws_url)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """WebSocket connection loop."""
        while not self._stop_event.is_set():
            try:
                self._ws = websocket.WebSocketApp(
                    self._ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self._ws.run_forever()
            except Exception as e:
                _LOGGER.exception(
                    f"{LOG_PREFIX_WS} Unhandled exception in WebSocket connection loop: %s", e
                )
            if not self._stop_event.is_set():
                _LOGGER.info(f"{LOG_PREFIX_WS} Reconnecting in %s seconds...", RECONNECT_INTERVAL)
                time.sleep(RECONNECT_INTERVAL)

    def _on_open(self, ws):
        """Handle WebSocket connection open."""
        _LOGGER.info(f"{LOG_PREFIX_WS} WebSocket connection established: %s", self._ws_url)

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        _LOGGER.debug(f"{LOG_PREFIX_WS} Received WebSocket message: %s", message)
        try:
            data = json.loads(message)
            self._message_callback(data)
        except json.JSONDecodeError:
            _LOGGER.error(f"{LOG_PREFIX_WS} Failed to decode message: %s", message)

    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        _LOGGER.error(f"{LOG_PREFIX_WS} WebSocket error: %s", error)

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket disconnections."""
        _LOGGER.warning(
            f"{LOG_PREFIX_WS} WebSocket connection closed: code=%s, message=%s",
            close_status_code,
            close_msg,
        )

    def stop(self):
        """Stop the WebSocket connection."""
        _LOGGER.info(f"{LOG_PREFIX_WS} Stopping WebSocket connection")
        self._stop_event.set()
        if self._ws:
            try:
                self._ws.close()
            except Exception as e:
                _LOGGER.warning(f"{LOG_PREFIX_WS} Failed to close WebSocket cleanly: %s", e)
        if self._thread:
            self._thread.join()
            _LOGGER.info(f"{LOG_PREFIX_WS} WebSocket thread stopped")

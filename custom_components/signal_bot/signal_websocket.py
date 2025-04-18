"""WebSocket client implementation for Signal Bot integration."""

import asyncio
from collections.abc import Callable, Coroutine
import json
import logging
import threading
import time
from typing import Any

import websocket

from .const import (
    API_ENDPOINT_RECEIVE,
    DEBUG_DETAILED,
    DEFAULT_RECONNECT_INTERVAL,
    LOG_PREFIX_WS,
    MAX_RECONNECT_DELAY,
    SIGNAL_STATE_CONNECTED,
    SIGNAL_STATE_DISCONNECTED,
    SIGNAL_STATE_ERROR,
    WS_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

MessageCallback = (
    Callable[[dict[str, Any]], Coroutine[Any, Any, None]]
    | Callable[[dict[str, Any]], None]
)
StatusCallback = Callable[[str], None]


class SignalWebSocket:
    """Manage WebSocket connection to Signal CLI REST API."""

    def __init__(
        self,
        api_url: str,
        phone_number: str,
        message_callback: MessageCallback,
        status_callback: StatusCallback | None = None,
    ) -> None:
        """Initialize the WebSocket manager."""
        ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")
        self._ws_url = (
            f"{ws_url.rstrip('/')}"
            f"{API_ENDPOINT_RECEIVE.format(phone_number=phone_number)}"
        )
        self._message_callback = message_callback
        self._status_callback = status_callback
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._ws: websocket.WebSocketApp | None = None
        self._reconnect_interval = DEFAULT_RECONNECT_INTERVAL
        self._event_loop = asyncio.get_event_loop()
        self.phone_number = phone_number  # Store for use in sensor.py

        if DEBUG_DETAILED:
            _LOGGER.debug(
                f"{LOG_PREFIX_WS} Initialized with URL: %s",
                self._ws_url,
            )

    def connect(self) -> None:
        """Start the WebSocket connection."""
        if self._thread and self._thread.is_alive():
            _LOGGER.warning(f"{LOG_PREFIX_WS} WebSocket thread is already running.")
            return

        _LOGGER.info(
            f"{LOG_PREFIX_WS} Connecting to Signal WebSocket: %s",
            self._ws_url,
        )
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        """WebSocket connection loop with exponential backoff."""
        backoff = self._reconnect_interval
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
                if self._stop_event.is_set():
                    break
            except websocket.WebSocketException:
                _LOGGER.exception(f"{LOG_PREFIX_WS} WebSocket error")
            except Exception:
                _LOGGER.exception(
                    f"{LOG_PREFIX_WS} Unhandled exception in WebSocket connection"
                )

            if not self._stop_event.is_set():
                _LOGGER.warning(
                    f"{LOG_PREFIX_WS} Reconnecting in %s seconds...",
                    backoff,
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_RECONNECT_DELAY)

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        """Handle WebSocket connection open."""
        _LOGGER.info(f"{LOG_PREFIX_WS} WebSocket connection established")
        if self._status_callback:
            self._status_callback(SIGNAL_STATE_CONNECTED)

    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            if DEBUG_DETAILED:
                _LOGGER.debug(f"{LOG_PREFIX_WS} Raw message received: %s", message)
            data = json.loads(message)

            # Handle async message callback
            if asyncio.iscoroutinefunction(self._message_callback):
                future = asyncio.run_coroutine_threadsafe(
                    self._message_callback(data), self._event_loop
                )
                try:
                    future.result(timeout=WS_TIMEOUT)
                except TimeoutError:
                    _LOGGER.exception(
                        f"{LOG_PREFIX_WS} Async callback timed out after %s seconds",
                        WS_TIMEOUT,
                    )
                except Exception:
                    _LOGGER.exception(f"{LOG_PREFIX_WS} Error in async callback")
            else:
                self._message_callback(data)

        except json.JSONDecodeError:
            _LOGGER.exception(f"{LOG_PREFIX_WS} Failed to decode message: %s", message)
        except Exception:
            _LOGGER.exception(f"{LOG_PREFIX_WS} Error processing message")

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        """Handle WebSocket errors."""
        _LOGGER.error(f"{LOG_PREFIX_WS} WebSocket error: %s", str(error))
        if self._status_callback:
            self._status_callback(SIGNAL_STATE_ERROR)

    def _on_close(
        self,
        ws: websocket.WebSocketApp,
        close_status_code: int | None,
        close_msg: str | None,
    ) -> None:
        """Handle WebSocket disconnections."""
        _LOGGER.warning(
            f"{LOG_PREFIX_WS} WebSocket connection closed: code=%s, message=%s",
            close_status_code,
            close_msg,
        )
        if self._status_callback:
            self._status_callback(SIGNAL_STATE_DISCONNECTED)

    def stop(self) -> None:
        """Stop the WebSocket connection."""
        _LOGGER.info(f"{LOG_PREFIX_WS} Stopping WebSocket connection")
        self._stop_event.set()
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                _LOGGER.exception(f"{LOG_PREFIX_WS} Failed to close WebSocket cleanly")
        if self._thread:
            self._thread.join()
            _LOGGER.info(f"{LOG_PREFIX_WS} WebSocket thread stopped")

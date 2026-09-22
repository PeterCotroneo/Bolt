"""Blitzortung real-time lightning provider.

Connects to the Blitzortung.org volunteer lightning-detection network over a
WebSocket and emits each detected strike. Data © Blitzortung.org and its
contributors — free for non-commercial use; please keep the attribution.

The message payload is packed with a small LZW-style scheme (the same one the
Blitzortung map uses); ``_decompress`` unpacks it back to JSON. QtWebSockets is
not exposed through qgis.PyQt, so QWebSocket is loaded from whichever Qt binding
qgis.PyQt is using (no hard-coded PyQt).
"""

import importlib
import json
import time

from qgis.PyQt.QtCore import QUrl, QTimer, QObject

from .base import StrikeProvider
from .._debug import dbg


def _load_qwebsocket():
    binding = QObject.__module__.split(".")[0]
    try:
        return importlib.import_module(binding + ".QtWebSockets").QWebSocket
    except ImportError:
        return None


QWebSocket = _load_qwebsocket()

HOSTS = ["wss://ws1.blitzortung.org/", "wss://ws7.blitzortung.org/",
         "wss://ws8.blitzortung.org/"]
RECONNECT_MS = 3000
WATCHDOG_MS = 30000
SILENCE_LIMIT_S = 60       # no strike for this long => reconnect
EMIT_MS = 700             # flush collected strikes to the map this often


def _decompress(text):
    """Blitzortung LZW-style unpack -> original JSON string."""
    if not text:
        return text
    table = {}
    result = [text[0]]
    prev = curr = text[0]
    code = 256
    for ch in text[1:]:
        val = ord(ch)
        entry = ch if val < 256 else (table[val] if val in table else prev + curr)
        result.append(entry)
        curr = entry[0]
        table[code] = prev + curr
        code += 1
        prev = entry
    return "".join(result)


class BlitzortungProvider(StrikeProvider):
    id = "blitzortung"
    label = "Blitzortung (lightning)"
    help_text = ("Live lightning from the Blitzortung.org volunteer network — "
                 "free and keyless, for non-commercial use, with global "
                 "coverage. Data © Blitzortung.org contributors.")

    def __init__(self, settings=None, parent=None):
        super().__init__(settings, parent)
        self._want = False
        self._host_i = 0
        self._batch = []
        self._last_rx = 0.0
        self._ws = None
        self._reconnect = None
        self._watchdog = None
        self._emit = None
        if QWebSocket is None:
            return
        self._ws = QWebSocket()
        self._ws.connected.connect(self._on_connected)
        self._ws.disconnected.connect(self._on_disconnected)
        self._ws.textMessageReceived.connect(self._on_text)
        self._ws.binaryMessageReceived.connect(self._on_binary)
        self._ws.errorOccurred.connect(self._on_error)
        self._reconnect = QTimer(self)
        self._reconnect.setSingleShot(True)
        self._reconnect.timeout.connect(self._open)
        self._watchdog = QTimer(self)
        self._watchdog.setInterval(WATCHDOG_MS)
        self._watchdog.timeout.connect(self._check_alive)
        self._emit = QTimer(self)
        self._emit.setInterval(EMIT_MS)
        self._emit.timeout.connect(self._emit_batch)

    # --- interface -------------------------------------------------------
    def start(self, bboxes):
        if self._ws is None:
            self.error.emit("QtWebSockets is not available in this QGIS build.")
            return
        self._want = True
        self.status_changed.emit("Connecting…")
        self._open()
        self._watchdog.start()
        self._emit.start()

    def stop(self):
        self._want = False
        for timer in (self._reconnect, self._watchdog, self._emit):
            if timer is not None:
                timer.stop()
        if self._ws is not None:
            self._ws.close()

    # --- socket lifecycle -----------------------------------------------
    def _open(self):
        if not self._want:
            return
        host = HOSTS[self._host_i % len(HOSTS)]
        self._host_i += 1
        self._ws.abort()
        self._last_rx = time.monotonic()
        self.status_changed.emit("Connecting…")
        self._ws.open(QUrl(host))

    def _on_connected(self):
        self._last_rx = time.monotonic()
        dbg("Connected to Blitzortung")
        self._ws.sendTextMessage('{"a":111}')
        self._ws.flush()
        self.status_changed.emit("Connected")

    def _on_disconnected(self):
        self.status_changed.emit("Disconnected")
        if self._want:
            self._reconnect.start(RECONNECT_MS)

    def _on_error(self, _err):
        dbg(f"Connection error: {self._ws.errorString()}")
        if self._want and not self._reconnect.isActive():
            self._reconnect.start(RECONNECT_MS)

    def _check_alive(self):
        if not self._want or self._reconnect.isActive():
            return
        if time.monotonic() - self._last_rx > SILENCE_LIMIT_S:
            dbg("No strikes for a while — reconnecting…")
            self._open()

    # --- messages --------------------------------------------------------
    def _on_text(self, text):
        self._handle(text)

    def _on_binary(self, data):
        try:
            self._handle(bytes(data).decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            dbg(f"decode error: {exc}")

    def _handle(self, raw):
        self._last_rx = time.monotonic()
        try:
            msg = json.loads(_decompress(raw))
        except Exception:  # noqa: BLE001 - malformed / non-strike frame
            return
        lat, lon, t = msg.get("lat"), msg.get("lon"), msg.get("time")
        if lat is None or lon is None:
            return
        self._batch.append({
            "id": f"{t}_{lat:.4f}_{lon:.4f}",
            "lat": lat, "lon": lon, "time": t,
            "stations": len(msg.get("sig") or []),
        })

    def _emit_batch(self):
        if self._batch:
            self.strikes_update.emit(self._batch)
            self._batch = []

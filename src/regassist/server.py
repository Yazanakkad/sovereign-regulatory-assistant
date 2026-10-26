"""Placeholder HTTP service: one health endpoint, JSON logs, graceful shutdown.

Standard library only, so it runs on the server's system Python without a
virtual environment. Replaced by the FastAPI service in Stage 2.
"""

import json
import logging
import os
import signal
import sys
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import FrameType

from regassist import __version__

log = logging.getLogger("regassist.server")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

# Python logging level -> syslog priority (0 emerg ... 7 debug), stored by journald as PRIORITY.
SYSLOG_PRIORITY = {
    logging.CRITICAL: 2,
    logging.ERROR: 3,
    logging.WARNING: 4,
    logging.INFO: 6,
    logging.DEBUG: 7,
}


@dataclass(frozen=True)
class Config:
    """Runtime settings, read from the environment."""

    host: str
    port: int


def load_config(env: Mapping[str, str]) -> Config:
    """Build the config from environment variables; raise ValueError if invalid."""
    host = env.get("REGASSIST_HOST", DEFAULT_HOST)
    raw_port = env.get("REGASSIST_PORT", str(DEFAULT_PORT))
    try:
        port = int(raw_port)
    except ValueError:
        raise ValueError(f"REGASSIST_PORT must be an integer, got {raw_port!r}") from None
    if not 1 <= port <= 65535:
        raise ValueError(f"REGASSIST_PORT must be between 1 and 65535, got {port}")
    return Config(host=host, port=port)


class JsonFormatter(logging.Formatter):
    """One JSON object per line; extra fields come from `extra={"fields": {...}}`.

    With syslog_prefix=True each line starts with "<N>" (the syslog priority).
    journald strips the prefix and stores N as the entry's PRIORITY field.
    """

    def __init__(self, *, syslog_prefix: bool = False) -> None:
        super().__init__()
        self._syslog_prefix = syslog_prefix

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            entry.update(fields)
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        line = json.dumps(entry, ensure_ascii=False)
        if self._syslog_prefix:
            return f"<{SYSLOG_PRIORITY.get(record.levelno, 6)}>{line}"
        return line


class HealthHandler(BaseHTTPRequestHandler):
    """Serves GET /health; everything else is a JSON 404."""

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "version": __version__})
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def version_string(self) -> str:
        # Default header leaks the Python version ("BaseHTTP/0.6 Python/3.14.4").
        return "regassist"

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        log.info(
            "request",
            extra={
                "fields": {
                    "method": self.command,
                    "path": self.path,
                    "status": int(code) if isinstance(code, int) else code,
                    "client": self.client_address[0],
                }
            },
        )

    def log_message(self, format: str, *args: object) -> None:
        # Base-class messages (malformed requests, errors) go through logging, not stderr.
        log.warning(format, *args)

    def _send_json(self, status: HTTPStatus, body: dict[str, str]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def make_server(config: Config) -> ThreadingHTTPServer:
    """Bind the listening socket; raises OSError if the address is unavailable."""
    return ThreadingHTTPServer((config.host, config.port), HealthHandler)


def serve(server: ThreadingHTTPServer, config: Config) -> None:
    """Serve until SIGTERM or SIGINT, then stop accepting and close the socket."""
    received: list[str] = []

    def request_stop(signum: int, _frame: FrameType | None) -> None:
        # Keep the handler tiny: record the signal and ask the loop to stop.
        # shutdown() waits for serve_forever() to return, so it must run in another thread.
        received.append(signal.Signals(signum).name)
        threading.Thread(target=server.shutdown, name="shutdown", daemon=True).start()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    log.info(
        "listening",
        extra={
            "fields": {
                "host": config.host,
                "port": server.server_port,
                "version": __version__,
                "pid": os.getpid(),
            }
        },
    )
    server.serve_forever()
    server.server_close()
    log.info("stopped", extra={"fields": {"signal": received[0] if received else None}})


def journal_stream_attached(env: Mapping[str, str]) -> bool:
    """True when systemd connected stdout to journald (it sets JOURNAL_STREAM)."""
    return "JOURNAL_STREAM" in env


def configure_logging(env: Mapping[str, str]) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(syslog_prefix=journal_stream_attached(env)))
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


def main() -> int:
    """Exit codes: 0 clean stop, 1 cannot bind, 2 invalid configuration."""
    configure_logging(os.environ)
    try:
        config = load_config(os.environ)
    except ValueError as exc:
        log.error("invalid configuration", extra={"fields": {"error": str(exc)}})
        return 2
    try:
        server = make_server(config)
    except OSError as exc:
        log.error(
            "cannot bind",
            extra={"fields": {"host": config.host, "port": config.port, "error": str(exc)}},
        )
        return 1
    serve(server, config)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Tests for the placeholder HTTP server."""

import json
import logging
import socket
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from urllib.parse import urlsplit

import pytest

from regassist.server import (
    Config,
    JsonFormatter,
    journal_stream_attached,
    load_config,
    make_server,
)

ARABIC = "\u0645\u0631\u062d\u0628\u0627"  # "marhaba"


def test_load_config_defaults() -> None:
    assert load_config({}) == Config(host="127.0.0.1", port=8000)


def test_load_config_reads_environment() -> None:
    env = {"REGASSIST_HOST": "::1", "REGASSIST_PORT": "9000"}
    assert load_config(env) == Config(host="::1", port=9000)


@pytest.mark.parametrize("raw", ["abc", "0", "65536"])
def test_load_config_rejects_bad_port(raw: str) -> None:
    with pytest.raises(ValueError, match="REGASSIST_PORT"):
        load_config({"REGASSIST_PORT": raw})


def test_json_formatter_keeps_fields_and_arabic() -> None:
    record = logging.makeLogRecord(
        {"name": "regassist", "levelname": "INFO", "msg": ARABIC, "fields": {"port": 8000}}
    )
    line = JsonFormatter().format(record)
    data = json.loads(line)
    assert data["msg"] == ARABIC
    assert data["port"] == 8000
    assert data["level"] == "info"
    assert ARABIC in line  # written as UTF-8, not \u escapes


@pytest.fixture
def base_url() -> Iterator[str]:
    server = make_server(Config(host="127.0.0.1", port=0))  # port 0: the OS picks a free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join()


def test_health_returns_ok(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/health", timeout=5) as resp:  # noqa: S310
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "application/json"
        assert resp.headers["Server"] == "regassist"
        assert json.loads(resp.read())["status"] == "ok"


def test_unknown_path_returns_404(base_url: str) -> None:
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(f"{base_url}/nope", timeout=5)  # noqa: S310
    assert excinfo.value.code == 404
    excinfo.value.close()


def test_json_formatter_syslog_prefix_maps_level() -> None:
    record = logging.makeLogRecord(
        {"name": "regassist", "levelno": logging.ERROR, "levelname": "ERROR", "msg": "boom"}
    )
    assert JsonFormatter(syslog_prefix=True).format(record).startswith("<3>{")
    assert JsonFormatter().format(record).startswith("{")


@pytest.mark.parametrize(("env", "expected"), [({"JOURNAL_STREAM": "8:1234"}, True), ({}, False)])
def test_journal_stream_detection(env: dict[str, str], expected: bool) -> None:
    assert journal_stream_attached(env) is expected


QUERY_WITH_PERSONAL_DATA = "national_id=1234567890"


def test_health_ignores_query_string(base_url: str) -> None:
    url = f"{base_url}/health?{QUERY_WITH_PERSONAL_DATA}"
    with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310
        assert resp.status == 200
        assert json.loads(resp.read())["status"] == "ok"


def test_request_log_omits_query_string(base_url: str, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="regassist.server")
    url = f"{base_url}/health?{QUERY_WITH_PERSONAL_DATA}"
    with urllib.request.urlopen(url, timeout=5):  # noqa: S310
        pass
    requests = [r for r in caplog.records if r.getMessage() == "request"]
    assert requests, "no request log record captured"
    line = JsonFormatter().format(requests[-1])
    assert json.loads(line)["path"] == "/health"
    assert "1234567890" not in line


def test_malformed_request_line_gets_400_and_is_logged(
    base_url: str, caplog: pytest.LogCaptureFixture
) -> None:
    # Too many words: the base class rejects it before it sets self.path.
    caplog.set_level(logging.INFO, logger="regassist.server")
    parts = urlsplit(base_url)
    assert parts.hostname is not None
    assert parts.port is not None
    with socket.create_connection((parts.hostname, parts.port), timeout=5) as sock:
        sock.sendall(b"GET /a /b HTTP/1.0\r\n\r\n")
        response = sock.recv(1024)
    assert response.startswith(b"HTTP/1.0 400")
    requests = [r for r in caplog.records if r.getMessage() == "request"]
    assert requests, "no request log record captured"
    assert json.loads(JsonFormatter().format(requests[-1]))["path"] == ""

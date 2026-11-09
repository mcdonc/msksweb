"""The proxy contract tests: every failure shape the CLI
guarantees (:mod:`msks.client.rest`), carried across the web
boundary — plus the listing's happy path and the UI gate.

The mock daemon (:mod:`tests.mock_daemon`) serves the daemon's
wire shapes on both transports (TCP with the token gate, unix
socket with peer-credential exemption).
"""

import os
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient

import mock_daemon  # type: ignore[import-not-found]


def _serve_tcp(port: int, token: str | None) -> tuple[threading.Thread, uvicorn.Server]:
    mock_daemon.APP.state.token = token
    config = uvicorn.Config(
        mock_daemon.APP, host="127.0.0.1", port=port, log_level="error"
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    return thread, server


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture()
def app_client(monkeypatch):
    """A client whose settings each test arranges before the
    lifespan opens the transport."""
    os.environ.pop("MSKSC_URL", None)
    os.environ.pop("MSKSC_SOCKET", None)
    os.environ.pop("MSKSC_TOKEN", None)
    import app.main as main

    main.app.state._fresh = True
    # Each test rebuilds the app so settings resolve from the
    # environment it arranged.
    monkeypatch.setattr(main, "app", main.create_app())
    return main.app


def _get(app, path, headers=None):
    with TestClient(app) as client:
        return client.get(path, headers=headers or {})


class TestUnconfigured:
    def test_health_names_it(self, app_client):
        r = _get(app_client, "/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "unconfigured"

    def test_listing_refuses(self, app_client):
        r = _get(app_client, "/api/workspaces")
        assert r.status_code == 503
        assert "no daemon configured" in r.json()["detail"]


class TestUnixSocket:
    @pytest.fixture()
    def sock(self, tmp_path):
        path = str(tmp_path / "msksd-mock.sock")
        mock_daemon.APP.state.token = None
        config = uvicorn.Config(mock_daemon.APP, uds=path, log_level="error")
        server = uvicorn.Server(config)
        threading.Thread(target=server.run, daemon=True).start()
        for _ in range(50):
            if Path(path).exists():
                break
            time.sleep(0.1)
        return path

    def test_health_and_listing(self, app_client, sock, monkeypatch):
        monkeypatch.setenv("MSKSWEB_DAEMON_SOCKET", sock)
        app_client.state.daemon.settings.daemon_socket = sock
        app_client.state.daemon.address = app_client.state.daemon.settings.address
        r = _get(app_client, "/api/health")
        assert r.json()["status"] == "ok"
        # the socket path displayed decoded, not percent-encoded
        assert r.json()["daemon_address"] == sock
        rows = _get(app_client, "/api/workspaces").json()
        assert [row["status"] for row in rows] == ["running", "starting", "stopped"]
        # the listing's derived fields ride each row
        assert rows[0]["image_ref"] == "debian-12:1.3.0"
        assert rows[1]["mount_issues"][0]["kind"] == "pending"

    def test_skew_notice_warns_never_refuses(self, app_client, sock, monkeypatch):
        monkeypatch.setenv("MSKSWEB_DAEMON_SOCKET", sock)
        monkeypatch.setenv("MSKSWEB_EXPECTED_DAEMON_VERSION", "0.8.0")
        app_client.state.daemon.settings.daemon_socket = sock
        app_client.state.daemon.settings.expected_daemon_version = "0.8.0"
        app_client.state.daemon.address = app_client.state.daemon.settings.address
        r = _get(app_client, "/api/health")
        assert r.status_code == 200
        assert "daemon runs 0.9.0.dev0" in r.json()["skew_notice"]


class TestTcpDaemon:
    def test_token_forwarded_and_detail_verbatim(self, app_client, monkeypatch):
        port = _free_port()
        _, server = _serve_tcp(port, token="sekrit")
        try:
            monkeypatch.setenv("MSKSWEB_DAEMON_URL", f"http://127.0.0.1:{port}")
            monkeypatch.setenv("MSKSWEB_DAEMON_TOKEN", "WRONG")
            app_client.state.daemon.settings.daemon_url = f"http://127.0.0.1:{port}"
            app_client.state.daemon.settings.daemon_token = "WRONG"
            app_client.state.daemon.address = app_client.state.daemon.settings.address
            r = _get(app_client, "/api/workspaces")
            # the daemon's own refusal, verbatim
            assert r.status_code == 401
            assert r.json()["detail"] == "invalid or missing token"

            app_client.state.daemon.settings.daemon_token = "sekrit"
            app_client.state.daemon._client = None  # rebuilt on next start
            r = _get(app_client, "/api/workspaces")
            assert r.status_code == 200
            assert len(r.json()) == 3
        finally:
            server.should_exit = True

    def test_dead_daemon_detail_and_health(self, app_client, monkeypatch):
        port = _free_port()
        monkeypatch.setenv("MSKSWEB_DAEMON_URL", f"http://127.0.0.1:{port}")
        app_client.state.daemon.settings.daemon_url = f"http://127.0.0.1:{port}"
        app_client.state.daemon.address = app_client.state.daemon.settings.address
        r = _get(app_client, "/api/workspaces")
        assert r.status_code == 502
        assert r.json()["detail"].startswith(
            f"cannot reach http://127.0.0.1:{port}"
        )
        # the probe never fails the page
        h = _get(app_client, "/api/health")
        assert h.status_code == 200
        assert h.json()["status"] == "unreachable"


class TestUiGate:
    def test_gate(self, app_client, monkeypatch):
        port = _free_port()
        _, server = _serve_tcp(port, token=None)
        try:
            monkeypatch.setenv("MSKSWEB_DAEMON_URL", f"http://127.0.0.1:{port}")
            monkeypatch.setenv("MSKSWEB_UI_TOKEN", "webgate")
            app_client.state.daemon.settings.daemon_url = f"http://127.0.0.1:{port}"
            app_client.state.daemon.address = app_client.state.daemon.settings.address
            app_client.state.settings.ui_token = "webgate"
            # without the token: refused, health stays open
            assert _get(app_client, "/api/workspaces").status_code == 401
            assert _get(app_client, "/api/health").status_code == 200
            # with the token: through
            ok = _get(
                app_client,
                "/api/workspaces",
                headers={"Authorization": "Bearer webgate"},
            )
            assert ok.status_code == 200
        finally:
            server.should_exit = True


class TestUi:
    def test_index_serves(self, app_client):
        with TestClient(app_client) as client:
            r = client.get("/")
            assert r.status_code == 200
            assert "msksweb" in r.text
            for asset in ("/static/styles.css", "/static/app.js", "/favicon.svg"):
                assert client.get(asset).status_code == 200

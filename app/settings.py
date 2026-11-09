"""Pydantic settings: where msksweb listens and which daemon it
proxies.

The daemon connection honors the msks client's conventions
(``MSKSC_URL``, ``MSKSC_SOCKET``, ``MSKSC_TOKEN``, ``MSKSC_CAFILE``
— see ``msks/client/env.py``) with ``MSKSWEB_*`` spellings that
win when both are set, so one environment can hold a CLI client
and this web client side by side:

===================  ===================================================
daemon address       ``MSKSWEB_DAEMON_URL`` / ``MSKSC_URL`` — an
                     ``https://host:port`` URL, or
                     ``http+unix://<percent-encoded path>`` for the
                     daemon's local unix listener
local socket         ``MSKSWEB_DAEMON_SOCKET`` / ``MSKSC_SOCKET`` —
                     a plain filesystem path; peer credentials
                     authenticate (no token, no TLS). When no
                     address is configured, the default socket
                     under ``$XDG_RUNTIME_DIR`` is tried, the same
                     candidate the CLI dials
bearer token         ``MSKSWEB_DAEMON_TOKEN`` / ``MSKSC_TOKEN``
CA bundle            ``MSKSWEB_CAFILE`` / ``MSKSC_CAFILE`` — pins
                     the daemon's certificate
listen host          ``MSKSWEB_BIND_HOST`` (default ``0.0.0.0`` —
                     the point is remote testing)
listen port          ``MSKSWEB_BIND_PORT`` (default ``8400``)
UI gate              ``MSKSWEB_UI_TOKEN`` — when set, browsers must
                     present this bearer token before the proxy
                     answers; a remote listener without it exposes
                     workspace control to the network
expected version     ``MSKSWEB_EXPECTED_DAEMON_VERSION`` — when set,
                     a daemon ``/health`` version that differs
                     raises the amber skew banner (warn, never
                     refuse — the CLI's #706 posture)
===================  ===================================================
"""

import os
from pathlib import Path
from urllib.parse import quote, unquote

from pydantic_settings import BaseSettings, SettingsConfigDict

#: The URL scheme that carries a unix socket path (the curl
#: convention, the same one the CLI uses).
UNIX_SCHEME = "http+unix://"

#: The daemon's socket placement vocabulary (``msks/spec/sockets.py``):
#: ``$XDG_RUNTIME_DIR/msks/msksd.sock``.
SOCKET_NAME = "msksd.sock"
SOCKET_DIR = "msks"


def unix_url(path: str) -> str:
    """The address form of a unix socket path (the path percent-
    encoded into the authority position)."""
    return UNIX_SCHEME + quote(path, safe="")


def is_unix(url: str) -> bool:
    """True when *url* addresses the daemon's local listener."""
    return url.startswith(UNIX_SCHEME)


def unix_path(url: str) -> str:
    """The socket path inside an ``http+unix://`` address."""
    return unquote(url[len(UNIX_SCHEME) :])


def display_url(url: str) -> str:
    """The address as the operator reads it: a unix address shows
    its socket path decoded; a TCP address passes through."""
    if is_unix(url):
        return unix_path(url)
    return url


def default_socket() -> str | None:
    """The default socket an unconfigured client dials, when one
    exists — the same single candidate the CLI checks."""
    xdg = os.environ.get("XDG_RUNTIME_DIR", "")
    if not xdg:
        return None
    path = Path(xdg) / SOCKET_DIR / SOCKET_NAME
    return str(path) if path.exists() else None


class Settings(BaseSettings):
    """The resolved runtime settings (env-only, like the CLI)."""

    model_config = SettingsConfigDict(env_prefix="MSKSWEB_")

    daemon_url: str | None = None
    daemon_socket: str | None = None
    daemon_token: str | None = None
    cafile: str | None = None
    bind_host: str = "0.0.0.0"
    bind_port: int = 8400
    ui_token: str | None = None
    expected_daemon_version: str | None = None

    @property
    def address(self) -> str:
        """The daemon address in URL form: the configured URL, the
        configured socket, or the default socket when one exists.

        The precedence mirrors the client: an explicit address
        wins, the discovered socket is the unconfigured fallback,
        and no daemon at all answers ``None`` (the UI shows the
        unconfigured banner instead of guessing).
        """
        url = self.daemon_url
        if url:
            if is_unix(url) or url.startswith(("http://", "https://")):
                return url
            # A bare path spells the socket (the client's --daemon
            # accepts the same shape).
            return unix_url(url)
        socket = self.daemon_socket
        if socket:
            return unix_url(socket)
        found = default_socket()
        return unix_url(found) if found else None

    @property
    def ssl_verify(self) -> str | bool:
        """TLS verification for a TCP daemon: the pinned CA bundle
        when one is configured, else the platform default."""
        return self.cafile if self.cafile else True


def load_settings() -> Settings:
    """The settings with the ``MSKSC_*`` aliases folded in: each
    alias fills a slot the ``MSKSWEB_*`` spelling left empty."""
    aliases = {
        "MSKSWEB_DAEMON_URL": "MSKSC_URL",
        "MSKSWEB_DAEMON_SOCKET": "MSKSC_SOCKET",
        "MSKSWEB_DAEMON_TOKEN": "MSKSC_TOKEN",
        "MSKSWEB_CAFILE": "MSKSC_CAFILE",
    }
    for ours, theirs in aliases.items():
        if not os.environ.get(ours) and os.environ.get(theirs):
            os.environ[ours] = os.environ[theirs]
    return Settings()

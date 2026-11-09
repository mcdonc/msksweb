"""The daemon REST transport: one shared ``httpx.AsyncClient``
behind the web app's proxy endpoints.

The error contract mirrors the CLI's (:mod:`msks.client.rest`):
a timeout names the daemon and the possibility it still finishes
the request; a dead dial names the daemon; an HTTP status carries
the daemon's detail verbatim — validation lists joined into one
line. Each failure shape becomes an ``HTTPException`` the web UI
renders as one readable banner.
"""

import ssl
from typing import Any

import httpx
from fastapi import HTTPException

from .settings import Settings, is_unix, unix_path

#: The daemon's read budget (:mod:`msks.client.rest`): ``start``
#: answers only after the VMM boot completes (~3s p50), so the
#: default 5s would cut a healthy launch off mid-flight.
TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

#: The best-effort /health probe's budget (#706 posture): small,
#: so a blackholed route never doubles a page's failure latency.
PROBE_TIMEOUT = httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)


class DaemonClient:
    """The shared transport for one app lifetime.

    A unix address (``http+unix://…``) dials the socket with peer
    credentials — no token, no TLS, the kernel vouches for both
    ends. A TCP address dials ``https://host:port`` with the
    optional bearer token and the configured verification story.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.address = settings.address
        self._client: httpx.AsyncClient | None = None

    @property
    def display_address(self) -> str | None:
        """The address as the operator reads it (socket path
        decoded), or None when unconfigured."""
        return display if (display := self.address) else None

    def _build(self) -> httpx.AsyncClient:
        headers = (
            {"Authorization": f"Bearer {self.settings.daemon_token}"}
            if self.settings.daemon_token is not None
            and not is_unix(self.address or "")
            else None
        )
        if self.address is None:
            return httpx.AsyncClient(headers=headers, timeout=TIMEOUT)
        if is_unix(self.address):
            return httpx.AsyncClient(
                base_url="http://unix",
                transport=httpx.AsyncHTTPTransport(
                    uds=unix_path(self.address)
                ),
                headers=headers,
                timeout=TIMEOUT,
            )
        verify: ssl.SSLContext | str | bool = True
        if self.settings.cafile:
            verify = ssl.create_default_context(cafile=self.settings.cafile)
        return httpx.AsyncClient(
            base_url=self.address,
            headers=headers,
            timeout=TIMEOUT,
            verify=verify,
        )

    async def start(self) -> None:
        """Open the shared client (the app lifespan's startup)."""
        self._client = self._build()

    async def close(self) -> None:
        """Close the shared client (the app lifespan's shutdown)."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # --- The error contract (the CLI's shapes, web-adapted) ---

    def _timeout_detail(self, exc: Exception) -> str:
        return (
            f"timed out talking to {self.display_address} "
            f"(the daemon may still finish the request): {exc}"
        )

    def _reach_detail(self, exc: Exception) -> str:
        return f"cannot reach {self.display_address}: {exc}"

    def _error_detail(self, response: httpx.Response) -> str:
        """The daemon's ``detail`` field; validation lists become
        one line (``loc: msg`` joined by ``;``)."""
        try:
            detail = response.json()["detail"]
        except (ValueError, KeyError, TypeError):
            return response.text.strip() or "no detail"
        if isinstance(detail, list):
            return self._validation_detail(detail)
        return str(detail)

    def _validation_detail(self, items: list[Any]) -> str:
        lines = []
        for item in items:
            if not isinstance(item, dict):
                continue
            loc = ".".join(str(part) for part in item.get("loc", []))
            msg = item.get("msg", "invalid")
            lines.append(f"{loc}: {msg}" if loc else str(msg))
        return "; ".join(lines) or "invalid request"

    # --- The exchanges ---

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> Any:
        """One exchange with the CLI's error contract: a timeout
        is a 504, a dead dial a 502, a daemon status its own code
        with its detail verbatim."""
        if self._client is None or self.address is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "no daemon configured: set MSKSWEB_DAEMON_URL "
                    "(or MSKSC_URL) for a remote daemon, "
                    "MSKSWEB_DAEMON_SOCKET (or MSKSC_SOCKET) for a "
                    "local one"
                ),
            )
        try:
            response = await self._client.request(
                method,
                path,
                json=json_body,
                params=params,
                timeout=timeout or TIMEOUT,
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504, detail=self._timeout_detail(exc)
            ) from exc
        except httpx.TransportError as exc:
            raise HTTPException(
                status_code=502, detail=self._reach_detail(exc)
            ) from exc
        if response.is_error:
            raise HTTPException(
                status_code=response.status_code,
                detail=self._error_detail(response),
            )
        return response.json()

    async def health(self) -> dict | None:
        """The daemon's ``/health`` document best-effort (#706
        posture): every failure is the caller's silence — the page
        never crashes over the probe, the banner alone speaks."""
        try:
            return await self.request(
                "GET", "/api/v1/health", timeout=PROBE_TIMEOUT
            )
        except HTTPException:
            return None

"""The FastAPI app factory and the ``msksweb`` entry point.

The lifespan owns the shared daemon transport; the UI gate
(``MSKSWEB_UI_TOKEN``) is the remote-listener's seatbelt — without
it anyone on the network reaches every proxy endpoint, so the
token turns the app into a bearer-gated surface while leaving
``/api/health`` open for the banner's own reachability check.
"""

import argparse
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .daemon import DaemonClient
from .routes import health, workspaces
from .settings import load_settings

STATIC_DIR = Path(__file__).parent.parent / "static"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


async def ui_gate(request: Request, call_next):
    """The bearer gate over the proxy when ``MSKSWEB_UI_TOKEN`` is
    set: browsers carry the token after one prompt; the health
    probe stays open (it answers nothing the token protects)."""
    token = request.app.state.settings.ui_token
    path = request.url.path
    if not token or path == "/api/health" or not path.startswith("/api/"):
        # the shell and its assets load ungated — the page itself
        # prompts for the token; every proxy endpoint answers
        # only behind it, and /api/health stays open for the
        # banner's reachability check
        return await call_next(request)
    header = request.headers.get("authorization", "")
    supplied = header[7:] if header.lower().startswith("bearer ") else ""
    if supplied != token:
        return JSONResponse({"detail": "ui token required"}, status_code=401)
    return await call_next(request)


async def http_error_banner(request: Request, exc: HTTPException):
    """The daemon's one-line detail rendered verbatim by the UI's
    error banner (the CLI's error contract, carried across)."""
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


def create_app() -> FastAPI:
    settings = load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """The shared daemon transport's lifetime: one client
        opened at boot, closed at shutdown."""
        await app.state.daemon.start()
        yield
        await app.state.daemon.close()

    app = FastAPI(
        lifespan=lifespan,
        title="msksweb",
        version=__version__,
        description=(
            "FastAPI/Pydantic web client for the msks microvm "
            "workspace daemon"
        ),
    )
    app.state.settings = settings
    app.state.daemon = DaemonClient(settings)

    app.middleware("http")(ui_gate)
    app.add_exception_handler(HTTPException, http_error_banner)
    app.include_router(health.router)
    app.include_router(workspaces.router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(TEMPLATES_DIR / "index.html")

    @app.get("/favicon.svg", include_in_schema=False)
    async def favicon() -> FileResponse:
        return FileResponse(STATIC_DIR / "logo.svg")

    return app


app = create_app()


def main() -> None:
    """The ``msksweb`` console script: argparse over the bind pair
    (the env still wins when the flags stay unset)."""
    parser = argparse.ArgumentParser(
        prog="msksweb", description="the msks web client"
    )
    parser.add_argument(
        "--host", default=None, help="bind host (default MSKSWEB_BIND_HOST)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="bind port (default MSKSWEB_BIND_PORT)",
    )
    args = parser.parse_args()
    settings = app.state.settings
    uvicorn.run(
        "app.main:app",
        host=args.host or settings.bind_host,
        port=args.port or settings.bind_port,
    )


if __name__ == "__main__":
    main()

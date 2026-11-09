"""The workspace surface. Issue #02 ships the listing (the web
``msks ls``); the lifecycle endpoints (create, start, stop, …)
arrive with issue #03 and grow onto this router.
"""

from fastapi import APIRouter, Request

from ..models import WorkspaceRow, jsonable

router = APIRouter()


@router.get("/api/workspaces")
async def list_workspaces(request: Request) -> list[dict]:
    """Every workspace the daemon knows, with each image's
    catalog reference and the derived mount state riding every
    row — the daemon's listing shape verbatim."""
    daemon = request.app.state.daemon
    rows = await daemon.request("GET", "/api/v1/workspaces")
    return [jsonable(WorkspaceRow.model_validate(row)) for row in rows]

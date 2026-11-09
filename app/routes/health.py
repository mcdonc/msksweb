"""``/api/health`` — the daemon probe behind the top bar.

Parity with the CLI's #706 posture: the probe is best-effort and
never fails the page — an unreachable daemon answers
``status: "unreachable"`` and the banner speaks; a configured-
nothing deployment answers ``"unconfigured"``. The skew notice
warns (never refuses) when ``MSKSWEB_EXPECTED_DAEMON_VERSION`` is
set and the daemon's word differs.
"""

from fastapi import APIRouter, Request

from .. import __version__
from ..models import HealthDoc, HealthReport
from ..settings import display_url

router = APIRouter()


@router.get("/api/health")
async def health(request: Request) -> HealthReport:
    daemon = request.app.state.daemon
    if daemon.address is None:
        return HealthReport(
            status="unconfigured",
            daemon=None,
            daemon_address=None,
            client_version=__version__,
        )
    doc = await daemon.health()
    if doc is None:
        return HealthReport(
            status="unreachable",
            daemon=None,
            daemon_address=display_url(daemon.address),
            client_version=__version__,
        )
    parsed = HealthDoc.model_validate(doc)
    expected = daemon.settings.expected_daemon_version
    notice = None
    if expected and parsed.version and parsed.version != expected:
        notice = (
            f"daemon runs {parsed.version}, the expected version is "
            f"{expected}; align them by restarting the daemon on "
            "the expected build"
        )
    return HealthReport(
        status="ok",
        daemon=parsed,
        daemon_address=display_url(daemon.address),
        client_version=__version__,
        skew_notice=notice,
    )

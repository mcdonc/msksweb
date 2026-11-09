"""Pydantic models for the daemon's rows (``msks/server/api/``).

The wire shapes come from the daemon's serializers
(:mod:`msks.model.model` ``workspace_dict`` / ``placeholder_dict``,
the api routers' rules/requests/storage views). Fields the daemon
adds over time ride through untouched — every model ignores
unknown keys, the same tolerance the CLI's dict reads carry.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class DaemonRow(BaseModel):
    """A permissive row base: unknown daemon fields pass through,
    so a newer daemon never breaks an older page render."""

    model_config = ConfigDict(extra="allow")


# --- Workspaces -----------------------------------------------------


class MountEntry(DaemonRow):
    """One host mount on a workspace row (#620/#667): a host path
    through the allowed-roots gates, the absolute guest path, and
    the mode — ``rw`` when the daemon omitted it."""

    host: str | None = None
    guest: str
    mode: str | None = None


class MountIssue(DaemonRow):
    """One skipped mount frame (#620): the kind, the mount it
    names, and the named reason."""

    kind: str
    host: str | None = None
    guest: str
    mode: str | None = None
    detail: str


class WorkspaceRow(DaemonRow):
    """One workspace row as the listing serves it
    (``workspace_dict`` + the listing's derived fields)."""

    id: str
    name: str | None = None
    kernel: str | None = None
    initrd: str | None = None
    rootfs: str | None = None
    cmdline: str | None = None
    cpus: int
    mem_mib: int
    image_hash: str | None = None
    image_ref: str | None = None
    host: str | None = None
    root_mib: int
    home_mib: int
    egress: bool
    egress_slice: str | None = None
    egress_mode: str = "allow"
    secret_coverage: str = "all"
    egress_allowlist: list[str] = []
    mounts: list[MountEntry] = []
    mounts_pending: bool = False
    mount_issues: list[MountIssue] = []
    user_data: str | None = None
    ssh_pubkey: str | None = None
    login_user: str | None = None
    timezone: str | None = None
    status: str
    created_at: str | None = None


# --- Health ---------------------------------------------------------


class HealthDoc(DaemonRow):
    """The daemon's public ``/health`` document."""

    status: str = "ok"
    version: str | None = None
    machine: str | None = None
    fastapi: str | None = None
    image: str | None = None


class HealthReport(BaseModel):
    """What the top bar renders: the probe's outcome, this
    client's version, and the skew notice (``MSKSWEB_EXPECTED_
    DAEMON_VERSION`` set and differing — warn, never refuse)."""

    status: Literal["ok", "unreachable", "unconfigured"]
    daemon: HealthDoc | None = None
    daemon_address: str | None = None
    client_version: str
    skew_notice: str | None = None


# --- Later issues' surfaces (defined now, served later) -------------


class ImageRow(DaemonRow):
    """One catalog row (``msks image ls``)."""

    name: str
    version: str
    hash: str
    default: bool = False
    kernel_version: str | None = None
    kernel_format: str | None = None
    description: str | None = None
    imported: str | None = None
    origin_name: str | None = None
    origin_version: str | None = None
    bytes: int | None = None


class SecretRow(DaemonRow):
    """One placeholder row (``msks secret ls``); the sentinel is
    served on mint alone, never in listings."""

    id: int
    workspaces: list[str] = []
    name: str
    dests: list[str] = []
    created_at: str
    expires_at: str | None = None


class EgressVerdictRow(DaemonRow):
    """One in-effect verdict (``msks egress rules``)."""

    dest_host: str
    dest_port: int | None = None
    duration: str | None = None


class EgressRules(DaemonRow):
    """The in-effect consent view for one workspace."""

    workspace_id: str
    mode: str
    allow_list: list[str] = []
    allowed: list[EgressVerdictRow] = []
    denied: list[EgressVerdictRow] = []


class EgressRequestRow(DaemonRow):
    """One consent row (the audit trail)."""

    id: str
    workspace_id: str | None = None
    dest_host: str
    dest_port: int | None = None
    decision: str
    duration: str | None = None
    requested_at: float


class StorageState(DaemonRow):
    """The state-disk budget line."""

    used: int
    total: int
    free: int
    pressure: str


class StorageWorkspace(DaemonRow):
    """One per-workspace cost/ceiling row (``msks storage``)."""

    id: str
    name: str | None = None
    root_bytes: int
    root_mib: int
    home_bytes: int
    home_mib: int


class StorageImage(DaemonRow):
    """One catalog cost row."""

    name: str
    version: str
    bytes: int
    imported: str | None = None


class StorageReport(DaemonRow):
    """The whole capacity report."""

    state: StorageState
    workspaces: list[StorageWorkspace] = []
    images: list[StorageImage] = []


class SshKeyRow(DaemonRow):
    """The workspace identity row (``msks key``): the public half
    alone — the private half never crosses the API."""

    id: str
    name: str | None = None
    instance: str | None = None
    user: str | None = None
    public_key: str
    disk_epoch: int | None = None
    seed_epoch: int | None = None


def jsonable(model: BaseModel) -> dict[str, Any]:
    """The model with its extra daemon fields carried along (the
    permissive-row passthrough the pages rely on)."""
    return model.model_dump()

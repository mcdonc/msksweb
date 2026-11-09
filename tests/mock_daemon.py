"""A mock msks daemon for local testing of the web proxy.

Serves the two surfaces issues #01/#02 use — ``/api/v1/health``
(public) and ``/api/v1/workspaces`` (token-gated like the real
daemon on TCP) — with rows shaped exactly like the daemon's
``workspace_dict`` output plus the listing's derived fields.

Run one of:

    python tests/mock_daemon.py tcp 127.0.0.1 9410 mytoken
    python tests/mock_daemon.py unix /tmp/msksd-mock.sock
"""

import json
import sys
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn

APP = FastAPI()
APP.state.token = None  # set by main(); None = no gate (unix-socket mode)

NOW = time.time()

ROWS = [
    {
        "id": "ws-1a2b3c4d5e6f7890",
        "name": "payments",
        "kernel": "/var/lib/msks/images/debian-12/1.3.0/vmlinuz",
        "initrd": None,
        "rootfs": "/var/lib/msks/images/debian-12/1.3.0/rootfs.ext4",
        "cmdline": "console=ttyS0 root=/dev/vda rw",
        "cpus": 4,
        "mem_mib": 8192,
        "image_hash": "sha256:9f86d081884c7d659a2feaa0c55ad015",
        "image_ref": "debian-12:1.3.0",
        "host": "host-a",
        "root_mib": 20480,
        "home_mib": 40960,
        "egress": True,
        "egress_slice": None,
        "egress_mode": "static",
        "secret_coverage": "all",
        "egress_allowlist": ["api.github.com:443"],
        "mounts": [
            {"host": "/srv/repos/payments", "guest": "/workspace", "mode": "rw"},
        ],
        "mounts_pending": False,
        "mount_issues": [],
        "user_data": None,
        "ssh_pubkey": "ssh-ed25519 AAAA…mock",
        "login_user": "dev",
        "timezone": "UTC",
        "status": "running",
        "created_at": "2025-06-01T09:15:00+00:00",
    },
    {
        "id": "ws-0f9e8d7c6b5a4321",
        "name": "docs-scratch",
        "kernel": "/var/lib/msks/images/ubuntu-24.04/2.0.1/vmlinuz",
        "initrd": "/var/lib/msks/images/ubuntu-24.04/2.0.1/initrd",
        "rootfs": "/var/lib/msks/images/ubuntu-24.04/2.0.1/rootfs.ext4",
        "cmdline": "console=ttyS0",
        "cpus": 2,
        "mem_mib": 4096,
        "image_hash": "sha256:2c26b46b68ffc68ff99b453c1d304134",
        "image_ref": "ubuntu-24.04:2.0.1",
        "host": None,
        "root_mib": 10240,
        "home_mib": 8192,
        "egress": False,
        "egress_slice": None,
        "egress_mode": "allow",
        "secret_coverage": "scoped",
        "egress_allowlist": [],
        "mounts": [
            {"host": "/home/dev/notes", "guest": "/workspace/notes", "mode": "ro"},
            {"host": "/etc/secrets", "guest": "/run/creds", "mode": None},
        ],
        "mounts_pending": True,
        "mount_issues": [
            {
                "kind": "pending",
                "host": "/etc/secrets",
                "guest": "/run/creds",
                "mode": None,
                "detail": "secret-backed mounts wait for the unlock (#624)",
            },
        ],
        "user_data": "#cloud-config\n",
        "ssh_pubkey": None,
        "login_user": None,
        "timezone": None,
        "status": "starting",
        "created_at": "2025-06-03T14:02:00+00:00",
    },
    {
        "id": "ws-deadbeefdeadbeef",
        "name": None,
        "kernel": "/var/lib/msks/images/alpine-3.20/1.0.0/vmlinuz",
        "initrd": None,
        "rootfs": "/var/lib/msks/images/alpine-3.20/1.0.0/rootfs.ext4",
        "cmdline": None,
        "cpus": 1,
        "mem_mib": 2048,
        "image_hash": "sha256:7f83b1657ff1fc53b92dc18148a1d65d",
        "image_ref": None,
        "host": "host-b",
        "root_mib": 5120,
        "home_mib": 2048,
        "egress": True,
        "egress_mode": "interactive",
        "egress_slice": None,
        "secret_coverage": "all",
        "egress_allowlist": [],
        "mounts": [],
        "mounts_pending": False,
        "mount_issues": [
            {
                "kind": "missing",
                "host": "/gone/dir",
                "guest": "/workspace/gone",
                "mode": "ro",
                "detail": "host path does not exist (#620)",
            },
        ],
        "user_data": None,
        "ssh_pubkey": None,
        "login_user": "root",
        "timezone": None,
        "status": "stopped",
        "created_at": "2025-05-20T11:30:00+00:00",
    },
]


def require_token(request: Request) -> None:
    """The daemon's TCP gate: a bearer token when one is set."""
    token = request.app.state.token
    if not token:
        return
    header = request.headers.get("authorization", "")
    if header != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="invalid or missing token")


@APP.get("/api/v1/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": "0.9.0.dev0",
        "machine": "x86_64",
        "fastapi": "0.115.0",
        "image": None,
        "uptime_s": round(time.time() - NOW, 1),
    }


@APP.get("/api/v1/workspaces")
async def list_workspaces(_: None = Depends(require_token)) -> list[dict]:
    return json.loads(json.dumps(ROWS))


class CreateBody(BaseModel):
    name: str


@APP.post("/api/v1/workspaces")
async def create_workspace(body: CreateBody) -> dict:
    raise HTTPException(status_code=422, detail=[
        {"loc": ["body", "mem_mib"], "msg": "value must be >= 256"},
    ])


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "tcp"
    if mode == "tcp":
        host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 9410
        APP.state.token = sys.argv[4] if len(sys.argv) > 4 else None
        print(f"mock daemon (token={'on' if APP.state.token else 'off'}) on {host}:{port}")
        uvicorn.run(APP, host=host, port=port, log_level="warning")
    else:
        path = sys.argv[2] if len(sys.argv) > 2 else "/tmp/msksd-mock.sock"
        Path(path).unlink(missing_ok=True)
        APP.state.token = None  # unix socket: peer credentials, no token
        print(f"mock daemon on {path}")
        uvicorn.run(APP, uds=path, log_level="warning")


if __name__ == "__main__":
    main()

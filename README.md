# msksweb

A FastAPI/Pydantic web client for the [msks](https://github.com/mcdonc/msks)
microvm workspace daemon — the `msks` CLI's surfaces, in the browser.

## Running

```bash
uv venv && uv pip install -e .   # or: pip install -e .
msksweb                           # serves on 0.0.0.0:8400
```

Then open `http://<host>:8400`.

## Configuration (environment)

| Variable | Meaning |
|---|---|
| `MSKSWEB_DAEMON_URL` / `MSKSC_URL` | Daemon address: `https://host:port`, or `http+unix://<percent-encoded path>` |
| `MSKSWEB_DAEMON_SOCKET` / `MSKSC_SOCKET` | Daemon unix socket path (peer-credential auth — no token) |
| `MSKSWEB_DAEMON_TOKEN` / `MSKSC_TOKEN` | Bearer token for a TCP daemon |
| `MSKSWEB_CAFILE` / `MSKSC_CAFILE` | CA bundle pinning the daemon's certificate |
| `MSKSWEB_BIND_HOST` / `MSKSWEB_BIND_PORT` | Listen address (default `0.0.0.0:8400`) |
| `MSKSWEB_UI_TOKEN` | **Set this for remote testing** — gates every proxy endpoint behind a browser bearer token |
| `MSKSWEB_EXPECTED_DAEMON_VERSION` | When set, a differing daemon version raises the amber skew banner |

With no address configured, the default local socket
(`$XDG_RUNTIME_DIR/msks/msksd.sock`) is dialed — the same candidate
the CLI finds.

## Remote testing note

The bind default is `0.0.0.0` because remote testing is the point,
but that exposes workspace control (create/delete/boot) to the
network. Set `MSKSWEB_UI_TOKEN` and the browser will prompt for it
once:

```bash
MSKSWEB_UI_TOKEN=s3cret msksweb --host 0.0.0.0 --port 8400
```

## Roadmap

The feature surface tracks the CLI command groups — see the
[issues](https://github.com/mcdonc/msksweb/issues). Shipped: the
scaffold (daemon transport, `MSKSC_*` settings, Pydantic row models,
UI shell) and the workspaces listing (`msks ls` parity: the table,
status pills with mount markers, image refs, health banner with the
version-skew notice, JSON view, live polling).

## License

MIT

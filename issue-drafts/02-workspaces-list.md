## Summary

Workspaces list page — the web equivalent of `msks ls` — plus the daemon health/version banner.

## Details

- Table with the CLI's columns: name, id, status (with mounts-skip marker, e.g. "running, 1 mount skipped"), egress mode, created date, image ref (clipped to 16 chars, middle-cut), host
- Status rendered as colored pills (created / starting / running / stopping / stopped / paused)
- Polling refresh (a few seconds) so boots and stops animate through their transitions
- Daemon `/api/v1/health` shown in the top bar: version, image; version-skew notice when the daemon and client versions differ (warn, never refuse — parity with the CLI's notice)
- JSON view toggle (parity with `--json`)

## Reference

- `../msks/src/msks/msks/client/workspaces.py` — `workspace_cells`, `status_with_mounts`, `version_skew_notice`
- `../msks/src/msks/msks/client/tabular.py` — the listing shapes

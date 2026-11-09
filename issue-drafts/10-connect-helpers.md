## Summary

Connection helpers page — surfacing the CLI's interactive commands (`console`, `ssh`, `forward`, `rsync`) from the web UI.

## Details

The web app cannot host a raw tty, but it should teach the operator the exact commands:

- Per-workspace "connect" card showing ready-to-copy command lines:
  - `msks console <ref>` — interactive root shell
  - `msks ssh <ref>` — ssh over the forward, identity staged in memory
  - `msks rsync <ref> ...` — file sync against the empty-host path form
  - `msks forward <ref> <port> [--local PORT]` — TCP bridge
- Login user from the row (`login_user`), plus `msks key <ref>` hint for the identity's public half
- If the workspace is stopped, the card notes the auto-boot behavior (`msks ssh` boots it) and the paused-workspace refusal advice

## Reference

- `../msks/src/msks/msks/client/ssh.py`, `console.py`, `forward.py`, `rsync.py`
- `../msks/src/msks/msks/client/rest.py` — `paused_advice`

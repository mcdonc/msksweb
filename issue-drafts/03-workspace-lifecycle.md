## Summary

Workspace lifecycle: create, start, stop, clone, rm, resize, key — the web equivalents of the `msks` commands of the same names.

## Details

- **Create dialog** with the full flag surface: name, image ref (or explicit kernel/initrd/rootfs/cmdline), cpus, mem-mib, root-mib, home-mib, egress toggle, egress mode (allow / static / interactive), static allowlist entries (repeatable specs: host, host:port, .host, *.host, cidr[:port]), secret coverage (all / scoped), user_data payload, login user, ssh pubkey, share mounts (HOST_PATH:GUEST_PATH[:MODE]), start-now checkbox
- **Start / Stop** buttons with in-flight states; wait-out polling for `starting`/`stopping` rows (parity with the CLI's #789 wait behavior)
- **Clone** with the `copy_allowlist` option; source must be stopped (daemon gate)
- **Resize** form: home-mib (grow/shrink), root-mib (grow only), cpus, mem-mib — next-boot semantics noted in UI
- **Delete** with confirmation; prints each deleted id
- **Key** view: fetch `/ssh-key` and display the public half (id, name, instance stamp, login user, disk epoch, seed epoch, public key)

## Reference

- `../msks/src/msks/msks/client/workspaces.py`, `create.py`, `resize.py`
- `../msks/src/msks/msks/server/api/schemas.py` — `WorkspaceCreate`, `WorkspaceResize`, `WorkspaceClone`

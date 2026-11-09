## Summary

Scaffold the `msksweb` application: a FastAPI backend with Pydantic models that acts as a web client/proxy for the msks daemon, plus the base UI shell.

## Details

- FastAPI app factory with lifespan-managed `httpx.AsyncClient` daemon transport
- Pydantic settings honoring the msks client conventions: `MSKSC_URL` (https URL), `MSKSC_SOCKET` (`http+unix://` local listener with peer-credential auth, no token), `MSKSC_TOKEN`, `MSKSC_CAFILE`
- Shared daemon client module mirroring the CLI's error contract: timeout / reach / HTTP-status detail surfaced as readable errors
- Pydantic response models for the daemon rows (see `msks/server/api/schemas.py`): `WorkspaceRow` (id, name, kernel, initrd, rootfs, cmdline, cpus, mem_mib, image_hash/image_ref, host, root_mib, home_mib, egress, egress_slice, egress_mode, secret_coverage, egress_allowlist, mounts, mounts_pending, mount_issues, user_data, ssh_pubkey, login_user, timezone, status, created_at), `ImageRow`, `SecretRow`, `EgressRules`, `EgressRequestRow`, `StorageReport`
- Serve a clean single-page UI (no build step): sidebar navigation, hash routing, system font stack, status pills
- README documenting setup and env vars

## Reference

- `../msks/src/msks/msks/client/rest.py` — transport, error contract
- `../msks/src/msks/msks/client/env.py` — `MSKSC_*` conventions, unix socket support
- `../msks/src/msks/msks/server/api/schemas.py` — daemon request models

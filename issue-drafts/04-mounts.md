## Summary

Host-mount management per workspace — the web equivalent of `msks mount` / `msks umount`.

## Details

- Mounts table on the workspace page: host path, guest path, mode (ro/rw), pending marker ("next start" while configured set ≠ attached set)
- Add mount form validating the spec client-side: absolute host path (~ expanded), absolute guest path, ro|rw mode (rw default); refuse `..`
- Remove mount(s) by host path; the set is posted whole (read row → apply edit → POST full list), parity with the CLI
- Mount issues display: kind + detail per issue (unresolved root, missing path), from the row's `mount_issues`

## Reference

- `../msks/src/msks/msks/client/workspaces.py` — `mount_spec`, `mounts_after`, `mounts_line`
- `../msks/src/msks/msks/server/api/schemas.py` — `MountIn`, `MountsSet`

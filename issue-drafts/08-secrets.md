## Summary

Placeholder-secret management — the web equivalent of `msks secret mint / ls / revoke / renew / coverage`.

## Details

- **Mint** form: name, coverage (daemon-wide by default, or scoped to workspaces by name/id — comma-splitting multi-select), destination allowlist (exact host or `.suffix`), optional TTL, secret value (masked input; whitespace-stripped; never echoed back)
- **List**: rows with id, coverage label (`*` for daemon-wide), name, destinations, created/expires; sentinels never listed
- **Revoke** (effective next request), **Renew** (new TTL from now)
- **Coverage flip** per workspace: all / scoped (parity with `msks secret coverage`)
- Mint response shows the sentinel **once** — display it prominently with a copy button, mirroring the CLI's print-once semantics
- (Optional, stretch) unlock flow against `/secrets/pending` + `/secrets/unlock` — needs client-side age decryption; can be deferred

## Reference

- `../msks/src/msks/msks/client/secrets.py` — `read_secret`, `coverage_label`, `resolve_coverage`
- `../msks/src/msks/msks/server/api/schemas.py` — `SecretMint`, `SecretRenew`, `SecretCoverageSet`

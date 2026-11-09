## Summary

Egress consent management — the web equivalent of `msks egress rules / requests / decide / revoke / mode`.

## Details

- **Rules view**: mode banner, static allowlist, in-effect verdicts (allowed/denied with destination + duration)
- **Requests view**: audit table (id, destination with "all ports" label for portless rows, decision, duration, requested-at) with a decision filter (pending / allowed / denied / expired / revoked)
- **Decide**: allow/deny with duration selector (once, 5m, 15m, tilrestart, forever)
- **Revoke**: undo an in-effect verdict
- **Mode switch**: allow / static / interactive; allowlist replacement editor (one spec per line); offline confirmation for a switch to static with nothing effectively allowed (`confirm_empty`)
- Live updates: poll requests, or stream via the events websocket (the daemon holds SYNs for interactive workspaces only while a decider is connected — a connected web page should register as one)

## Reference

- `../msks/src/msks/msks/client/egress.py` — `rules_line`, `request_cells`, `run_mode`, durations
- `../msks/src/msks/msks/server/api/schemas.py` — `EgressDecide`, `EgressPolicySet`

## Summary

Storage report page — the web equivalent of `msks storage`.

## Details

- Budget line: state disk used / total / free, with pressure indicator
- Per-workspace framed table: workspace label, root cost/ceiling, home cost/ceiling, total cost (binary units: 512K, 812M, 23.4G — whole numbers when decimals add nothing)
- Image cost table: ref, imported stamp, bytes
- Optional narrowing to one workspace (parity with the positional arg)
- JSON view toggle

## Reference

- `../msks/src/msks/msks/client/volumes.py` — `render_storage`, `storage_cells`, `human_bytes`, `cost_pair`

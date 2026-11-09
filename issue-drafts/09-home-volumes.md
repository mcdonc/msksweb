## Summary

Home-volume moves — the web equivalents of `msks home export` and `msks home import`.

## Details

- **Export**: download a workspace's `/home` volume as `<workspace_id>.ext4` — stream through the web app (never buffer whole; volumes run to gigabytes), report byte count
- **Import**: upload an ext4 volume image to replace a workspace's `/home` — streamed with the octet-stream type, 1 MiB windows
- Guard rails in UI: workspace should be stopped for an import; byte counts shown on completion

## Reference

- `../msks/src/msks/msks/client/volumes.py` — `run_home_export`, `run_home_import`, `file_windows`
- `../msks/src/msks/msks/client/rest.py` — `download`, `upload` streaming shapes

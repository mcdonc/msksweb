## Summary

Image catalog management — the web equivalent of `msks image ls / import / rename / rm / info / default`.

## Details

- Catalog table: ref (name:version), origin pair when renamed, short hash (12), default flag, kernel (version + format), description (capped), imported stamp (local time to the minute)
- **Import**: source is a daemon-side path or an `https://` URL the daemon downloads itself; optional name/version overrides
- **Rename**: move registered name/version (bytes, hash, manifest origin stay)
- **Info**: one image's full record
- **Default**: designate the image a bare create boots; unset clears it
- **Remove**: delete from catalog
- Storage cost of each image rides the storage page (see storage issue)

## Reference

- `../msks/src/msks/msks/client/images.py` — `image_cells`, `origin_cell`, `imported_cell`
- `../msks/src/msks/msks/server/api/images.py` — endpoints incl. `POST /images/default`, `DELETE /images/default`, `PATCH /images/{digest}`

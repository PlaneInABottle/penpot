# media

`provenance.json` is this project's media table: the single source for photo choice. A
rebuild re-imports from it, so persist the accepted record **before** claiming a lossless
rebuild. The generic importer does not create the file and does not write the table — it
prints `source:` and `provenance:` on stdout, and that output is your input.

Generic import (one source, `--url` or `--search`; board-local `--x`/`--y`):

```sh
python3 scripts/import_media.py --url <pinned-url> --name <slot> \
  --page <page> --board <board> --x 0 --y 0 --w <w> --h <h>
```

`--only`, `--force` and `--restore` are not generic flags. They belong to a project's own
`tools/media.py` when it ships one (this template does not); that tool is also the thing
that writes the media table. Open the target page first, read the committed slot size, crop
to that aspect, and confirm the subject at 1:1.

Fields to persist for every accepted photo:

| field | meaning |
|---|---|
| `slot` | shape name the photo replaces (never covers) |
| `board`, `page` | where it lands |
| `role` | shows / proves / sets mood — a photo with no role is cut |
| `source` | pinned Pexels URL; the key stays in the shell profile |
| `query` | the search that produced it, for a re-run |
| `crop` | committed aspect and what must survive it (face, hands, equipment) |

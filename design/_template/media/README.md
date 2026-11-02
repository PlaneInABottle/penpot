# media

`provenance.json` (created by the first photo import) is the media table: the single source for photo choice. A rebuild
re-imports from it, so a one-off inline import regresses on the next run — persist the
winning query or pinned URL the moment a photo is accepted.

| field | meaning |
|---|---|
| `slot` | shape name the photo replaces (never covers) |
| `board`, `page` | where it lands |
| `role` | shows / proves / sets mood — a photo with no role is cut |
| `source` | pinned Pexels URL; the key stays in the shell profile |
| `query` | the search that produced it, for a re-run |
| `crop` | committed aspect and what must survive it (face, hands, equipment) |

Import: `python3 scripts/import_media.py --only <slot> --board <b> --page <p> --force`
(always scope with `--only`; a bare `--board` retargets every slot to one board). Open the
target page first — the attach fails on an inactive page — then read the committed slot
size, crop to that aspect, and confirm the subject at 1:1.

# build

One script per screen (`screen-NN.js`), run one at a time through
`python3 scripts/penpot_exec.py --file design/<project>/build/screen-NN.js`.

Write this project's `lib.js` from the four structural axes in `brief.md` §2. Copying the
previous project's `lib.js` is the failure the template exists to prevent: reuse of the
primitive library reuses the grammar, and a new accent on old atoms produces the old page.

Rules the helpers must hold:

- a row's height comes from its measured content (`storage.FIT` from the design-system
  skill's `assets/fit-slot.js`), never from a fixed pitch;
- one `rows(items)`, one `bullets()`, one `fitCards()` per project — no hand-written y;
- every content x/w derives from the grid constants, never from a literal that "reaches the
  edge";
- ids and names are check-then-create so a rebuild replaces rather than duplicates.

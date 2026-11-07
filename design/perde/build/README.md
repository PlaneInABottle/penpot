# build

One script per screen (`screen-NN.js`). A project **must** ship a runner at
`build/build.py`; this template does **not** ship one. A raw
`python3 scripts/penpot_exec.py --file .../screen-NN.js` run is not a rebuild:
it bypasses page/session affinity, the fit poll, photo restoration, flows and
the live counts, so a green snippet proves nothing about the final board.

The runner is required to:

- hold the plugin writer session for the whole screen and verify `currentPage`
  by name after every page move (page affinity, not a fire-and-forget write);
- poll the fit until text ink is measured and stable, with a bounded deadline;
- restore every photo recorded for the board from the project media table,
  pinned source first — never a fresh search;
- apply `flows.js` once after the build, not per pass;
- verify live `photos N/N` and `links N/N` and fail on any shortfall;
- print a final machine-readable `RESULT ok|fail nulls=N` line and make its exit
  code match it. Never read a build's status through a pipe.

Read an existing project's runner in this workspace before writing one; the
contract above is what a template screen must satisfy.

Write this project's `lib.js` from the four structural axes in `brief.md` §2.
Copying the previous project's `lib.js` is the failure the template exists to
prevent: reuse of the primitive library reuses the grammar, and a new accent on
old atoms produces the old page.

Rules the helpers must hold:

- a row's height comes from its measured content (`storage.FIT` from the design-system
  skill's `assets/fit-slot.js`), never from a fixed pitch;
- one `rows(items)`, one `bullets()`, one `fitCards()` per project — no hand-written y;
- every content x/w derives from the grid constants, never from a literal that "reaches the
  edge";
- ids and names are check-then-create so a rebuild replaces rather than duplicates.

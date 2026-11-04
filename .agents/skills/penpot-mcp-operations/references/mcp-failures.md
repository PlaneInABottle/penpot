# Penpot MCP gotchas

Failure modes observed against Penpot 2.18.5 through the Penpot MCP bridge on a local stack.
Load this when a call fails, or once before a first run on a new file; workflow and decision
rules live in [../SKILL.md](../SKILL.md). Every call needs the plugin connected to the target
file, otherwise it returns `No Penpot instance connected for user token.`

## When a call fails

1. Re-read the state in a new call: a failure often means the write already applied.
2. `storage.H` undefined means the plugin reloaded; re-inject `assets/helpers.js`.
3. Change one hypothesis per attempt, and stop when two attempts add no evidence.

## Known failures, by phase

### Connection and commit

| # | Symptom or error text | Cause | Fix |
|---|---|---|---|
| 1 | asynchronous commit | a fill is still `#B1B2B5`, `tokens: {}`, `library.components` empty, and a just-deleted board is still listed | write in one call and verify in the next; delete in one call and confirm in the next |
| 20 | page activation is async | `appendChild` fails with `Cannot modify a page that is not currently active`; a board created right after `createPage()` lands on the old page; renaming it renames the previous page | `openPage`/`createPage` do not switch synchronously — open in one call, verify `penpot.currentPage.id` in the next, address pages by object or UUID, never by name |
| 37 | background-page reads report null textBounds | every text on a non-open page reports `textBounds` null although the render is complete | open the page first (`penpot.openPage`), wait, then read; bounds-dependent checks (fit, lint dumps, rhythm) are only valid on the open page |
| 40 | another writer on the shared plugin tab | a build writes into the wrong page, or `Cannot modify a page that is not currently active` appears mid-run; the same board builds "randomly" unfinished | one plugin, one writer: the server accepts one plugin connection per user token (a second is closed with WS 1008 `duplicate`), `penpot.currentPage` is one global target, and tasks run in parallel, not queued. Every call takes a `flock` (`scripts/penpot_exec.py`: `plugin-<host>-<hash8>.lock` per call, `<…>.session.lock` per build); a second writer waits then exits 2 with `plugin busy: held by pid=…`, a read warns `build in progress` and passes (`PENPOT_WAIT_BUILD=1` waits). `--expect-page NAME` (penpot_exec, build, import_media) refuses a drifted `currentPage` (`page-affinity`, `another session changed the page`). Real isolation — one Penpot user + MCP key + browser profile per agent — needs accounts: deliberately not done, a user decision |
| 38 | a call times out at 240 s | `MCP call timed out after 240s — task may still be running` while the file looks half-built | the plugin task may still be running: do not resend the same screen, wait and query the live board (node count, `textBounds` nulls, fit quiet); `PENPOT_HTTP_TIMEOUT` only changes the wait |
| 39 | a rebuild never measures its texts | after rebuilding the page that is already open, every new text reports `textBounds: null` for minutes, so fit resizes nothing | `penpot.openPage` on the current page is a no-op and a no-op never re-runs layout; open another page first, then the target, and poll `currentPage` until it is the target before reading bounds |
| 44 | a call stalls although the file is idle and the tab was in the background | `execute_code` takes far longer than usual, or the next call looks frozen | the browser here is Firefox (checked with `ps -axo comm`); it throttles a background tab's timers (1000 ms floor, budget throttling up to 15 s) — bring the Penpot tab to the front and rerun. A permanent fix is a separate task |
| 45 | browser advice copied from another session | "add Penpot to Chrome's always-keep-active list" or a Chromium flag, on a machine without Chrome | never assume the browser: `ps -axo comm \| grep -i "firefox\|chrome\|safari"` names the one running Penpot, and the advice is written for that one |

### Tokens and fills

| # | Symptom or error text | Cause | Fix |
|---|---|---|---|
| 2 | duplicate names on re-create | `A set with the same name already exists` and `A token already exists at the path` | one token per role path per set; delete, verify the deletion, then create |
| 12 | token-bound numbers are strings | a tokenized `fontSize` or `width` reads back as `"18"`, not `18` | compare loosely or convert; never assume a number |
| 13 | token value is writable | `token.value` looks read-only, so updates go through remove-and-re-add | assign directly on the existing token; it persists |
| 15 | binding is not paint | a shape reports `tokens.fill: "<a colour token>"` yet exports white or black; and `fills` written after binding empties `tokens` | `applyToken` records the binding only — paint the literal first, then bind (`H.apply`); never write `fills` afterwards; export and look |
| 16 | bulk re-bind drops bindings | a 170-shape re-bind reported success, then their `tokens.fill` was empty | chunk the batch to about 50 shapes and verify the binding count in a later call |
| 10 | library is file-scoped | token sets and components survive a deleted scratch page | remove sets and components explicitly (`set.remove()`, delete the component's main board), then verify |

### Text

| # | Symptom or error text | Cause | Fix |
|---|---|---|---|
| 6 | font weight rejected | `Font weight '500' not supported` with `Code: :fontWeight` | only 200/300/400/600/700/900 are settable; 500 works through the `fontVariantId` row below |
| 17 | text has no metrics | `textBounds: null` and a 1×1 box with `fontWeight = "400"` | set `fontId` + `fontFamily` + `fontVariantId` (`"regular"`, `"500"`, `"600"`) |
| 18 | letter spacing is px | `Value not valid: 0.14em` on `letterSpacing` | convert: 0.14em at 11px = `1.54` |
| 19 | text in a flex parent | a text child keeps a 1×1 box although `textBounds` is right | `layoutChild.horizontalSizing = "auto"`, then resize to `textBounds` in a later call |
| 27 | instance label does not fit | an instance's label wraps or clips inside a fixed-size chip | widen the box, then set it to the measured ink width, in two passes |
| 28 | glyph missing or clipped | `→` renders as a short dash and `−` as a hyphen | the UI font may lack the glyph and a fixed 16px box clips the head — use a font that carries it (Plex Mono does, Plex Sans does not), create the text `auto-width`, right-align by measured ink |
| 30 | ink is not the box | a rule touches the heading below it, or a headline and the line under it print on top of each other | line height below 1.15 puts ink outside the box and a 32px title's ink starts above it — keep display/h1 at 1.2, stack from `textBounds`, keep ≥40px from a rule to the next heading's ink |
| 31 | fresh text reports height 10 | bands overlap after a layout pass although every coordinate looked right | a new auto-height text reports `height: 10` until its commit; place from the previous pass's measured height or re-run the pass |

### Components and pages

| # | Symptom or error text | Cause | Fix |
|---|---|---|---|
| 5 | labels cannot be children | `Value not valid: :rect` on `appendChild` | `Rectangle` and `Text` take no children; place the label on the board over the shape |
| 7 | variant helper missing | `Value not valid: [object ShapeProxy]` from `createVariantFromComponents`; `penpotUtils.createVariantContainer` undefined | `createComponent`, then `component.transformInVariant()` |
| 21 | component names carry a path | `component.name = "nav/top"` shows `nav / nav` | the slash separates component path and name; set it at creation or leave it alone |
| 22 | component from a fresh instance | `Cannot create a component from the given shapes` right after instancing inside it | the library is stale inside the writing call; retry in the next |
| 11 | instance lands elsewhere | `component.instance()` appears inside an unrelated board | `targetBoard.appendChild(instance)`, then set `x`/`y` |
| 4 | layout not exposed | `board.flexLayout` is null or undefined | read `board.flex` / `board.grid` |
| 8 | markup is geometry | about 24 KB of `position: absolute` CSS from `generateStyle()` / `generateMarkup()` | measure with it; implement from tokens and structure, never paste it |
| 3 | animation action rejected | `Value not valid` with `Code: :addInteraction` for `dissolve`, `slide`, `push` | always pass `easing`, e.g. `"ease-out"`, although the docs mark it optional |
| 14 | flow disappears | interactions exist but `page.flows` is empty | a flow can drop while its interactions stay; audit and repair with `page.createFlow(name, board)` |
| 35 | cross-page navigate-to stores hollow | `addInteraction` with a destination Board proxy from another page succeeds silently but stores `{"id":"","type":null}` | keep prototype links same-page, or wire cross-page links in the Penpot UI; verify every destination resolves to a live `Page/Board` in a later read |

### Media

| # | Symptom or error text | Cause | Fix |
|---|---|---|---|
| 23 | cross-origin media | `uploadMediaUrl` returns a media object but the shape renders empty | the sandbox cannot fetch cross-origin; download the bytes yourself, then `await penpot.uploadMediaData(name, Uint8Array, mime)` |
| 24 | request body limit | upload fails with `HTTP 413` | the body tops out near 100 KB of base64; resize to about 700px longest side at q55 and retry once smaller |
| 25 | image fills do export | a board exports blank and you conclude images do not render | check the shape's parent and `fills[0].fillImage.id`; image fills render |
| 32 | media does not survive a rebuild | image fills vanish after a rebuild and the frames come back empty | the rebuild deletes the shapes that held the media; re-import by name after the last rebuild |
| 34 | placeholder rect survives under the photo | an empty `surface.alt` mat renders beneath every imported image | place the photo, then delete every same-named shape except the fresh one in the same call; a render must show zero empty mats |
| 36 | photo lands one board-height off | image renders shifted up by exactly the board's y (or x) | the placer assigned board-local numbers to page-absolute coords — add `board.x/board.y`, or read the live slot geometry which is already absolute |

### Export

| # | Symptom or error text | Cause | Fix |
|---|---|---|---|
| 9 | export of a page | export fails, returns empty, or times out on `#screenshot-00000000-…` | export each board by its own shape id; `"page"` and page names are a zero-size shape |
| 29 | exporter hangs | a board export times out at 120s although the board is small and the document is idle | restart the exporter container, wait, retry; if it persists the shape is the suspect |
| 33 | `export_shape` times out on tall boards | `Task … timed out after 120 seconds` on boards above ~2500px while smaller boards export fine | loopback only: the exporter may still have rendered; use the local recovery in `export_board.py` (`penpot.resource.png.<uuid>` has `.png` mid-name). Hosted runs must never copy a local exporter's bitmap; report a bridge failure instead |

### Build runner and gates

| # | Symptom or error text | Cause | Fix |
|---|---|---|---|
| 41 | a pipe eats the build's exit code | `build.py <screen> \| tail` prints a green log although the build failed | never read a build's status through a pipe (`pipefail` or the tool's own status); build.py prints a last machine-readable line `RESULT ok\|fail nulls=N` and its exit code always matches it |
| 42 | a rebuild silently drops photos and links | after a rebuild the photo slots are empty mats and the prototype links are gone while lint/QA stay green | a rebuild is lossless or it is not done: re-place every `name@board` provenance photo (pinned source, not a fresh search), re-apply flows once, verify live `photos N/N` and `links N/N`; build.py does this and exits 1 on a shortfall |
| 46 | a build exits 1 with `fit never settled` | the built board still has unmeasured or overflowing slots after the fit poll | `build.py` holds `build/.build.lock` (stale after 5 min) and polls fit 250 ms up to `--fit-deadline` (20 s), then exits 1 and reports a timed-out call against live state instead of retrying (`PENPOT_HTTP_TIMEOUT`, 240 s); open the board, re-measure, rebuild once |
| 43 | lint is clean on a page nobody measured | `design_lint.py` prints `0 high` for a page whose texts all report `textBounds: null`, because every ink rule skips unmeasured text | more than 5% unmeasured texts exits **2** with `page not active: textBounds unavailable — open <page>; findings are NOT valid`, writes `valid:false` in `--json`, and `gate.py` prints `FAIL (invalid)` instead of PASS; open the page and rerun |

## Scope of these claims

Verified on a local 2.18.5 stack, one file open in the browser plugin. Not verified: Penpot
cloud, other versions, several files open at once, or headless use. A row describes an
observed failure; anything new stays a hypothesis until a call proves it.

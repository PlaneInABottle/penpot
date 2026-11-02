# Penpot MCP gotchas

Failure modes observed against Penpot 2.18.5 through the Penpot MCP bridge on a local
stack. Load this when a call fails, or once before a first run on a new file; workflow
and decision rules live in [../SKILL.md](../SKILL.md). Every call needs the plugin
connected to the target file, otherwise it returns
`No Penpot instance connected for user token.`

## Write in one call, verify in the next

Penpot commits asynchronously, so a read inside the writing call sees the previous
state. Split every mutation from its check.

```js
// Call A — write, return the id for the check
const board = penpot.createBoard();
board.name = "01-dashboard";
board.resize(1440, 900);
return board.id;
```

```js
// Call B — separate execute_code call
// re-read the shape by the id returned in call A and compare name/size/fill,
// then export_shape(shapeId: "<id>", format: "png", mode: "shape")
```

The same split applies to token sets, components, page deletion and prototype links.

## Known failures

| # | Symptom or error text | Cause | Fix |
|---|---|---|---|
| 1 | asynchronous commit | a fill is still `#B1B2B5`, `tokens: {}`, `library.components` empty, and a just-deleted board is still listed | write in one call and verify in the next; delete in one call and confirm in the next |
| 2 | duplicate names on re-create | `A set with the same name already exists` and `A token already exists at the path` | one `md` per set, role-prefixed names; delete, verify the deletion, then create |
| 3 | animation action rejected | `Value not valid` with `Code: :addInteraction` for `dissolve`, `slide`, `push` | always pass `easing`, e.g. `"ease-out"`, although the docs mark it optional |
| 4 | layout not exposed | `board.flexLayout` is null or undefined | read `board.flex` / `board.grid` |
| 5 | labels cannot be children | `Value not valid: :rect` on `appendChild` | `Rectangle` and `Text` take no children; place the label on the board over the shape |
| 6 | font weight rejected | `Font weight '500' not supported` with `Code: :fontWeight` | only 200/300/400/600/700/900; but see the `fontVariantId` row — 500 works through the variant |
| 7 | variant helper missing | `Value not valid: [object ShapeProxy]` from `createVariantFromComponents`; `penpotUtils.createVariantContainer` undefined | `createComponent`, then `component.transformInVariant()` |
| 8 | markup is geometry | about 24 KB of `position: absolute` CSS from `generateStyle()` / `generateMarkup()` | measure with it; implement from tokens and structure, never paste it |
| 9 | export of a page | export fails, returns empty, or times out on `#screenshot-00000000-…` | export each board by its own shape id; `"page"` and page names are a zero-size shape |
| 10 | library is file-scoped | token sets and components survive a deleted scratch page | remove sets and components explicitly (`set.remove()`, delete the component's main board), then verify |
| 11 | instance lands elsewhere | `component.instance()` appears inside an unrelated board | `targetBoard.appendChild(instance)`, then set `x`/`y` |
| 12 | token-bound numbers are strings | a tokenized `fontSize` or `width` reads back as `"18"`, not `18` | compare loosely or convert; never assume a number |
| 13 | token value is writable | `token.value` looks read-only, so updates go through remove-and-re-add | assign directly on the existing token; it persists |
| 14 | flow disappears | interactions exist but `page.flows` is empty | a flow can drop while its interactions stay; audit and repair with `page.createFlow(name, board)` |
| 15 | binding is not paint | a shape reports `tokens.fill: "<a colour token>"` yet the export paints it white or black; and `fills` written after binding empties `tokens` | `applyToken` records the binding only — paint the literal first, then bind (`H.apply`); never write `fills` afterwards; a binding is not visual proof, so export and look |
| 16 | bulk re-bind drops bindings | a 170-shape re-bind reported success, then their `tokens.fill` was empty | chunk the batch to about 50 shapes and verify the binding count in a later call |
| 17 | text has no metrics | `textBounds: null` and a 1×1 text box with `fontWeight = "400"` | set `fontId` + `fontFamily` + `fontVariantId` (`"regular"`, `"500"`, `"600"`); `fontWeight` alone asks for a variant that does not exist |
| 18 | letter spacing is px | `Value not valid: 0.14em` on `letterSpacing` | convert: 0.14em at 11px = `1.54` |
| 19 | text in a flex parent | a text child keeps a 1×1 box although `textBounds` is right | `layoutChild.horizontalSizing = "auto"`, then resize to `textBounds` in a later call |
| 20 | page activation is async | `appendChild` fails with `Cannot modify a page that is not currently active`; a board created right after `createPage()` lands on the old page; renaming it renames the previous page | `openPage` and `createPage` do not switch synchronously — open in one call, verify `penpot.currentPage.id` in the next, and address pages by object or UUID, never by name |
| 21 | component names carry a path | `component.name = "nav/top"` shows `nav / nav` | the slash separates component path and name; set it at creation or leave it alone |
| 22 | component from a fresh instance | `Cannot create a component from the given shapes` right after instancing inside it | the library is stale inside the writing call; retry in the next |
| 23 | cross-origin media | `uploadMediaUrl` returns a media object but the shape renders empty | the sandbox cannot fetch cross-origin; download the bytes yourself, then `await penpot.uploadMediaData(name, Uint8Array, mime)` |
| 24 | request body limit | upload fails with `HTTP 413` | the body tops out near 100 KB of base64; resize to about 700px longest side at q55 and retry once smaller |
| 25 | image fills do export | a board exports blank and you conclude images do not render | check the shape's parent and `fills[0].fillImage.id`; image fills render |
| 26 | rebuild drops interactions | after a rebuild every prototype link is gone, and calling `createFlow` again leaves two flows | re-wire after the last rebuild, delete the duplicate flow, verify `page.flows.length` and the per-board count |
| 27 | instance label does not fit | an instance's label wraps or clips inside a fixed-size chip | widen the box, then set it to the measured ink width, in two passes |
| 28 | glyph missing or clipped | `→` renders as a short dash and `−` as a hyphen | the UI font may lack the glyph and a fixed 16px box clips the head — use a font that carries it (Plex Mono does, Plex Sans does not), create the text `auto-width`, right-align by measured ink |
| 29 | exporter hangs | a board export times out at 120s although the board is small and the document is idle | restart the exporter container, wait, retry; if it persists the shape is the suspect |
| 30 | ink is not the box | a rule touches the heading below it, or a headline and the line under it print on top of each other | line height below 1.15 puts ink outside the box, and a 32px title's ink starts above it — keep display/h1 at 1.2 and stack from `textBounds`, not the box; keep ≥40px from a rule to the next heading's ink |
| 31 | fresh text reports height 10 | bands overlap after a layout pass even though every coordinate looked right | a new auto-height text reports `height: 10` until its commit; place from the previous pass's measured height or re-run the pass |
| 33 | `export_shape` times out on tall boards | `Task … timed out after 120 seconds` on boards above ~2500px while smaller boards export fine | the exporter usually still rendered: fire the export, ignore the task result, and copy the newest `penpot.*.png.*` file out of the exporter container (`docker compose cp penpot-exporter:/tmp/penpot/<file>`); filenames are `penpot.resource.png.<uuid>`, the `.png` sits mid-name |
| 36 | photo lands one board-height off | image renders shifted up by exactly the board's y (or x) | the placer assigned board-local numbers to page-absolute coords — add `board.x/board.y`, or read the live slot geometry which is already absolute |
| 35 | cross-page navigate-to stores hollow | `addInteraction` with a destination Board proxy from another page succeeds silently but stores `{"id":"","type":null}` — the link goes nowhere, no error | keep prototype links same-page, or wire cross-page links in the Penpot UI where the proxy resolves; verify every destination resolves to a live `Page/Board` in a later read |
| 34 | placeholder rect survives under the photo | an empty `surface.alt` mat renders beneath every imported image | place the photo, then delete every same-named shape except the fresh one in the same call; a render must show zero empty mats |
| 37 | background-page reads report null textBounds | every text on a non-open page reports `textBounds` null although the render is complete | open the page first (`penpot.openPage`), wait, then read; bounds-dependent checks (fit, lint dumps, rhythm) are only valid on the open page |
| 32 | media does not survive a rebuild | image fills vanish after a rebuild and the frames come back empty | the rebuild deletes the shapes that held the media; re-import by name after the last rebuild, or keep media out of rebuilt boards |
| 38 | a call times out at 240 s | `MCP call timed out after 240s — task may still be running` while the file looks half-built | the plugin task may still be running: do not resend the same screen, wait and query the live board (node count, `textBounds` nulls, fit quiet) before deciding anything; `PENPOT_HTTP_TIMEOUT` only changes the wait |
| 39 | a rebuild never measures its texts | after rebuilding the page that is already open, every new text reports `textBounds: null` for minutes, so fit cannot resize anything and the board looks unfinished | `penpot.openPage` on the current page is a no-op and a no-op never re-runs layout; open another page first, then the target, and poll `currentPage` until it is the target before reading bounds |

## Render truth

A written shape is a hypothesis until an export proves it. `tokens.fill` proves intent, not
paint: export the board, look at the image, and compare the colours you see with the token
values. Two failure classes reach production this way — a bound fill that renders black or
white (row 15) and text that wraps or clips differently from its measured box. Any QA that
counts bindings instead of comparing `fills[0].fillColor` with the token value reports
false coverage.

## When a call fails

1. Re-read the state in a new call: a failure often means the write already applied.
2. `storage.H` undefined means the plugin reloaded; re-inject `assets/helpers.js`.
3. Change one hypothesis per attempt, and stop when two attempts add no evidence.

## Scope of these claims

Verified on a local 2.18.5 stack, one file open in the browser plugin. Not verified:
Penpot cloud, other versions, several files open at once, or headless use. A row
describes an observed failure unless it says otherwise; anything new stays a
hypothesis until a call proves it.

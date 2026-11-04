---
name: penpot-mcp-operations
description: Operate and debug the Penpot MCP bridge — run execute_code snippets, inject the helpers library, bind tokens so they actually paint, export boards for review, and diagnose plugin, page, component and text failures. Use when writing or fixing a script against the Penpot MCP server, when a Penpot call fails or returns stale data, when a board must be exported to an image, or when helpers must be loaded. Not for design decisions, page structure or visual direction (use penpot-design-system).
license: MIT
metadata:
  author: configs
  version: "2.0.0"
---

# Penpot MCP operations

The bridge runs arbitrary JavaScript inside an open browser tab, observed against Penpot 2.18.5
locally and 2.19 hosted. Design process lives in [penpot-design-system](../penpot-design-system/SKILL.md);
proof lives in [design-verification](../design-verification/SKILL.md).

## Contract

- A browser tab with the target file must have the plugin connected. Otherwise every call
  returns `No Penpot instance connected for user token.` — stop, do not retry.
- The MCP endpoint URL carries the user token: read it from its file, never copy it into a
  snippet, prompt, log or commit. Verify a value by its length only; never echo the header.
- Never assume the browser: `ps -axo comm | grep -i "firefox\|chrome\|safari"` names the running one.
- `execute_code` returns text the server may wrap as `{"result": "<json>", "log": ""}`.
  Unwrap before decoding, or you decode a string twice.
- One plugin, one writer: locks, `--expect-page` and `--read` intent are stated once in
  `AGENTS.md` § Ownership and safety; the hosted-vs-local target in § Runtime.
- A raw snippet run is not a rebuild: it proves execution, not page affinity, fit, photos,
  flows or live counts; use the project runner.

## Helpers

`assets/helpers.js` (in `penpot-design-system`, symlinked as `scripts/helpers.js`) assigns
`storage.H` when the whole file is sent through `execute_code`; later calls use `storage.H.*` —
a bare `H` is undefined. `storage` persists across calls and MCP sessions, functions included;
re-inject after a plugin reload or version mismatch. No CLI path injects it: `penpot_exec.py`
runs the snippet only, and `design_lint`/`design_qa` refuse a missing version during a read.
Bootstrap a fresh tab via `tokens_sync.py --check`, the project runner or `ensure_helpers(load_url())`.

| helper | effect |
|---|---|
| `find(name, parent?)` / `all(name)` | shape by name on the current page |
| `ensureSet(name, active?)` / `readSet(name)` | get or create a token set / read it |
| `syncTokens(set, specs)` | reconcile a whole token set by name |
| `paint(shape, set, token)` | write the literal fill and bind it |
| `apply(shape, set, token, props, fallback?)` | same, for any property list |
| `tokens(set)` / `invalidateTokens()` | resolve a set once per generation / force a re-read after a UI token edit |
| `upsertBoard(name, opts)` / `link(shape, trigger, action)` | idempotent board / interaction |
| `cleanup(prefix, {dryRun}?)` | remove shapes and sets by prefix; throws under four characters |
| `audit(page?)` | read-only coverage report |

## Paint is not bind

`shape.applyToken(token, ["fill"])` records the binding in `shape.tokens` and does **not** change
`shape.fills`; it keeps rendering white or black. Assigning `shape.fills` clears the binding, so
**literal first, then bind** (`H.apply`/`H.paint`) — a shape can be "100% token covered" and
visually wrong. Re-binding in bulk is not free: chunk to ~50 shapes and verify in the next call.

## Text

Set `fontId` + `fontFamily` + `fontVariantId` (`"regular"`, `"500"`, `"600"`); `fontWeight` alone
asks for a variant that does not exist and leaves a 1×1 box with `textBounds: null` (500 works
through the variant id). `letterSpacing` is px, not em (0.14em at 11px = `1.54`). Text in a flex
parent never auto-sizes: set `layoutChild.horizontalSizing = "auto"` and resize to `textBounds`
in a later call. `growType` controls wrapping (`auto-height` copy, `auto-width` labels).

## Pages, components, flows

- `openPage` needs a Page object or UUID, not a name. `createPage()` does not switch
  `currentPage` synchronously, so renaming the current page right after it renames the
  previous one — rename by id in a later call.
- `component.instance()` lands in the last active container: `targetBoard.appendChild(it)`,
  then set `x`/`y`. Instances inherit the master's size.
- Component names containing `/` are a path plus a name; assigning `"nav/top"` later corrupts
  the path into `nav / nav`.
- Create a component only on a board that does not already hold a fresh instance of it;
  otherwise `Cannot create a component from the given shapes` until the next call.
- A flow can drop while its interactions stay: read `page.flows` and repair with
  `createFlow(name, board)`. Animations require `easing` even though docs call it optional.

## Media

The plugin sandbox cannot fetch cross-origin, so `uploadMediaUrl` returns an object with no
bytes and the shape renders empty. Download outside Penpot, shrink it (~700px longest side,
JPEG q55 — the request body tops out near 100KB of base64 and answers `HTTP 413` above it),
then `await penpot.uploadMediaData(name, bytes, mime)` and set `shape.fills = [{fillOpacity: 1,
fillImage: media}]`; attach **after** the page is active or `Cannot modify a page that is not
currently active`. `scripts/import_media.py` places one image (`--url` or `--search`, explicit
name/page/board/w/h), prints source and provenance, and persists nothing: record the URL in
the project media table before a rebuild. `--only`/`--force`/`--restore` are project-tool flags.

## Export

`scripts/export_board.py` is the only path to an image, one board per call — the bulk renderer
is unreliable past the MCP task limit. `export_shape` is a separate tool (`shapeId`, `format`,
`mode`) returning image data and writing no file; `"page"` and page names fail because the page
root is zero-size. A bound fill can still render white: `design_qa.py` reports that as
`renderMismatches` and fails on it. The exporter rescue exists only on a loopback endpoint:
matching width x height proves the size, never the identity, of a render.

## Failures

[references/mcp-failures.md](references/mcp-failures.md) is the table of 45 observed failure
modes, grouped by phase, with the exact error strings and fixes. Open it on the first failed
call. The four that hit first: async commit, remove-and-recreate in one call, `easing` missing
on animations, and a bound fill that never painted.

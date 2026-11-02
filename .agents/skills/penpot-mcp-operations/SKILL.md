---
name: penpot-mcp-operations
description: Operate and debug the Penpot MCP bridge — run execute_code snippets, inject the helpers library, bind tokens so they actually paint, export boards for review, and diagnose plugin, page, component and text failures. Use when writing or fixing a script against the Penpot MCP server, when a Penpot call fails or returns stale data, when a board must be exported to an image, or when helpers must be loaded. Not for design decisions, page structure or visual direction (use penpot-design-system).
license: MIT
metadata:
  author: configs
  version: "1.0.0"
---

# Penpot MCP operations

The bridge runs arbitrary JavaScript inside an open browser tab. Everything here is
observed against Penpot 2.18.5 through `execute_code`; the design process lives in
[penpot-design-system](../penpot-design-system/SKILL.md).

## Contract

- A browser tab with the target file must have the plugin connected. Otherwise every
  call returns `No Penpot instance connected for user token.` — stop, do not retry.
- The MCP endpoint URL carries the user token. Read it from its file, never copy it into
  a snippet, prompt, log or commit.
- `execute_code` returns text; the server may wrap it as `{"result": "<json>", "log": ""}`.
  Unwrap before decoding, or you decode a string twice.
- `export_shape` is a separate tool (`shapeId`, `format`, `mode`), not a snippet call, and
  it returns image data to the client — no file, no path.

## Helpers

`assets/helpers.js` (in the `penpot-design-system` skill, symlinked as `scripts/helpers.js`)
is loaded by sending the whole file through `execute_code`; it assigns `storage.H` and
returns `{loaded: version}`. Later calls use `storage.H.*` — a bare `H` is undefined.
`storage` persists across calls and MCP sessions, functions included; re-inject after a
plugin reload, and on any version mismatch.

| helper | effect |
|---|---|
| `find(name, parent?)` / `all(name)` | shape by name on the current page |
| `ensureSet(name, active?)` / `readSet(name)` | get or create a token set / read it |
| `syncTokens(set, specs)` | reconcile a whole token set by name |
| `paint(shape, set, token)` | write the literal fill and bind it |
| `apply(shape, set, token, props, fallback?)` | same, for any property list |
| `tokens(set)` / `invalidateTokens()` | resolve a set once per generation (one `sets` read for a whole build) / force a re-read after a token edit made in the UI |
| `upsertBoard(name, opts)` / `link(shape, trigger, action)` | idempotent board / interaction |
| `cleanup(prefix, {dryRun}?)` | remove shapes and sets by prefix; throws under four characters |
| `audit(page?)` | read-only coverage report |

## Paint is not bind

`shape.applyToken(token, ["fill"])` records the binding in `shape.tokens` and does **not**
change `shape.fills`; the shape keeps rendering white or black. Assigning `shape.fills`
clears the binding. The only working order is **literal first, then bind** — what
`H.apply`/`H.paint` do. A shape can therefore be "100% token covered" and visually wrong,
so coverage counts are not evidence: export the board and look.

Re-binding in bulk is not free: a single call that repainted 170 shapes left their
`tokens.fill` empty afterwards, while the same code on ~50 shapes held. Re-bind in batches
of about 50, verify the bindings in the next call, and never treat a batch result count as
proof.

## Text

Set `fontId` + `fontFamily` + `fontVariantId` (`"regular"`, `"500"`, `"600"`). Setting
`fontWeight` alone asks for a variant that does not exist and leaves a 1×1 box with
`textBounds: null`; weight 500 does work through the variant id. `letterSpacing` is px,
not em (0.14em at 11px = `1.54`). Text inside a flex parent never auto-sizes: set
`layoutChild.horizontalSizing = "auto"` and resize to `textBounds` in a later call.
`growType` controls wrapping (`auto-height` for copy, `auto-width` for labels).

## Pages, components, flows

- `openPage` needs a Page object or UUID, not a name. `createPage()` does not switch
  `currentPage` synchronously, so renaming the current page right after it renames the
  previous one — rename by id in a later call.
- `component.instance()` lands in the last active container: `targetBoard.appendChild(it)`,
  then set `x`/`y`. Instances inherit the master's size.
- Component names containing `/` are a path plus a name; assigning `"nav/top"` later
  corrupts the path into `nav / nav`.
- Create a component only on a board that does not already hold a fresh instance of it;
  otherwise `Cannot create a component from the given shapes` until the next call.
- A flow can drop while its interactions stay: read `page.flows` and repair with
  `createFlow(name, board)`. Animations require `easing` even though docs call it optional.

## Write, then verify

Penpot commits asynchronously: a read inside the writing call sees the previous state
(stale `#B1B2B5` fill, `tokens: {}`, an empty component list, a deleted board still
listed). Write in one call, read in the next, export in a third. "Delete then recreate the
same name" in one call fails for the same reason.

## Media

The plugin sandbox cannot fetch cross-origin, so `uploadMediaUrl` returns an object with no
bytes and the shape renders empty. Download the file outside Penpot, shrink it (about 700px
longest side, JPEG q55 — the MCP request body tops out near 100KB of base64 and answers
`HTTP 413` above it), then `await penpot.uploadMediaData(name, bytes, mime)` and set
`shape.fills = [{fillOpacity: 1, fillImage: media}]`. Attach the shape to the board with
`appendChild` **after** the target page is active, or the call fails with
`Cannot modify a page that is not currently active`. Image fills do export, so a blank
export means the shape is not in the board, not that the renderer ignores images.

## Render truth

Export the board by its own id (`format` `png|svg`, `mode` `shape|fill`) and compare what
is painted with the token values. `"page"` and page names fail — the page root is a
zero-size shape. Two defects only a render reveals: a bound fill painting the wrong
colour, and text that clips or overlaps because its box was measured in the same call it
was written.

## Failures

The full table of 42 observed failure modes, with the exact error strings and fixes, is in
[references/mcp-failures.md](references/mcp-failures.md). Open it on the first failed call.
The four that hit first: async commit, remove-and-recreate in one call, `easing` missing on
animations, and a bound fill that never painted.

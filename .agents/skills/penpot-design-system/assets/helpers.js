/**
 * Penpot MCP helpers — idempotent operations for the `execute_code` tool.
 *
 * Load once per plugin session:
 *   const code = <this file> + "\nreturn storage.H.version;"
 *   -> then every later call uses `storage.H.*`
 * The plugin context persists `storage` across `execute_code` calls (functions
 * included), so re-injection is only needed after the plugin reloads — or after
 * this file changes. Compare the `version` below with `storage.H.version` and
 * re-inject on mismatch (penpot_exec.ensure_helpers does that).
 *
 * Design rules:
 * - every function reconciles by name; running it twice must not duplicate anything
 * - no function reads back a value it just wrote (Penpot commits asynchronously)
 * - return JSON-serializable summaries, never shapes
 */
const H = {
  version: "1.4.0",

  page() { return penpot.currentPage; },

  find(name, parent) {
    const p = parent || penpot.currentPage.root;
    return (p.children || []).filter((c) => c.name === name)[0] || null;
  },

  all(name) {
    const out = [];
    const walk = (s) => {
      if (s.name === name) out.push(s);
      (s.children || []).forEach(walk);
    };
    walk(penpot.currentPage.root);
    return out;
  },

  /** Returns the existing set with that name, or creates it. Never duplicates. */
  ensureSet(name, active) {
    const cat = penpot.library.local.tokens;
    const existing = cat.sets.filter((s) => s.name === name)[0];
    if (existing) return { set: existing, created: false };
    return { set: cat.addSet({ name: name, active: active !== false }), created: true };
  },

  /**
   * Returns {name, active, tokens: [{type, name, value}]} for a token set, or null
   * when the set does not exist. Read-only.
   */
  readSet(name) {
    const set = penpot.library.local.tokens.sets.filter((s) => s.name === name)[0];
    if (!set) return null;
    return {
      name: set.name,
      active: set.active,
      tokens: set.tokens.map((t) => ({ type: t.type, name: t.name, value: String(t.value) })),
    };
  },

  /**
   * Reconciles tokens by name: adds missing, updates changed values, leaves equal
   * ones alone. `specs` is [{type, name, value}].
   * A repeated spec name is reported in `conflicts` and skipped, so one batch can
   * never add the same token twice.
   * Returns counts only — verify in a separate call.
   */
  syncTokens(setName, specs) {
    const { set, created } = this.ensureSet(setName, true);
    const byName = Object.create(null);
    const specsSeen = Object.create(null);
    set.tokens.forEach((t) => { byName[t.name] = t; });
    let added = 0, updated = 0, unchanged = 0;
    const conflicts = [];
    specs.forEach((spec) => {
      if (specsSeen[spec.name]) {
        conflicts.push(spec.name + " appears twice in specs; kept the first one");
        return;
      }
      specsSeen[spec.name] = true;
      const existing = byName[spec.name];
      if (!existing) {
        const token = set.addToken({ type: spec.type, name: spec.name, value: String(spec.value) });
        byName[spec.name] = token || { type: spec.type, name: spec.name, value: String(spec.value) };
        added++;
        return;
      }
      if (existing.type !== spec.type) {
        conflicts.push(spec.name + " is " + existing.type + ", spec says " + spec.type);
        return;
      }
      if (String(existing.value) === String(spec.value)) { unchanged++; return; }
      existing.value = String(spec.value);
      updated++;
    });
    return { set: setName, createdSet: created, added, updated, unchanged, conflicts };
  },

  /**
   * Binds a token to shape properties; falls back to the literal if it is missing.
   *
   * A colour fill also gets its literal value written first: `applyToken` records
   * the binding in `shape.tokens` but does not touch `shape.fills`, so a shape can
   * be "token bound" and still render black or white. Writing `fills` clears the
   * binding, hence the order — literal, then bind.
   */
  apply(shape, setName, tokenName, props, fallback) {
    const set = penpot.library.local.tokens.sets.filter((s) => s.name === setName)[0];
    const token = set && set.tokens.filter((t) => t.name === tokenName)[0];
    if (!token) {
      if (fallback && props.indexOf("fill") !== -1) {
        shape.fills = [{ fillColor: fallback, fillOpacity: 1 }];
      }
      return { applied: false, reason: "missing token " + setName + "/" + tokenName };
    }
    if (props.indexOf("fill") !== -1) this.paint(shape, setName, tokenName);
    shape.applyToken(token, props);
    return { applied: true, value: String(token.value) };
  },

  /** Paints the token's literal colour and binds it, in the only order that works. */
  paint(shape, setName, tokenName) {
    const set = penpot.library.local.tokens.sets.filter((s) => s.name === setName)[0];
    const token = set && set.tokens.filter((t) => t.name === tokenName)[0];
    if (!token) return { painted: false };
    const value = String(token.value);
    shape.fills = [{ fillColor: value, fillOpacity: 1 }];
    return { painted: true, value };
  },

  /** Finds a root board by name or creates it, then reconciles size and position. */
  upsertBoard(name, opts) {
    const o = opts || {};
    let board = this.find(name);
    let created = false;
    if (!board) { board = penpot.createBoard(); board.name = name; created = true; }
    if (o.w && o.h) board.resize(o.w, o.h);
    if (o.x !== undefined) board.x = o.x;
    if (o.y !== undefined) board.y = o.y;
    if (o.fill) board.fills = [{ fillColor: o.fill, fillOpacity: 1 }];
    if (o.radius !== undefined) board.borderRadius = o.radius;
    return { board, created };
  },

  /**
   * Idempotent prototype link: drops an existing interaction with the same trigger
   * and action type on that shape, then adds the requested one.
   */
  link(shape, trigger, action) {
    const same = (shape.interactions || []).filter(
      (i) => i.trigger === trigger && i.action.type === action.type,
    );
    same.forEach((i) => i.remove());
    shape.addInteraction(trigger, action);
    return { replaced: same.length };
  },

  /**
   * Deletes every shape and token set whose name starts with `prefix`.
   * Components are never removed (they outlive their main instance). With
   * `opts.dryRun` it only lists what it would delete.
   * Throws when `prefix` is shorter than 4 characters: an empty prefix matches
   * everything, including the real `core` token set.
   */
  cleanup(prefix, opts) {
    const p = prefix === undefined || prefix === null ? "" : String(prefix);
    if (p.trim().length < 4) {
      throw new Error("cleanup: prefix must be at least 4 characters, got " + JSON.stringify(p));
    }
    const dryRun = !!(opts && opts.dryRun === true);
    const removed = [];
    const page = penpot.currentPage;
    const walk = (parent) => {
      (parent.children || []).slice().forEach((c) => {
        if (String(c.name || "").indexOf(p) === 0) {
          removed.push(c.name);
          if (!dryRun) c.remove();
          return;
        }
        walk(c);
      });
    };
    walk(page.root);
    penpot.library.local.tokens.sets.slice().forEach((s) => {
      if (String(s.name || "").indexOf(p) === 0) {
        removed.push("set:" + s.name);
        if (!dryRun) s.remove();
      }
    });
    return { removed, dryRun };
  },

  /**
   * Read-only audit of one page: token coverage, naming, prototype and component
   * hygiene. Takes a page object or a page name and walks that page's root, so the
   * user's current page is never switched. Defaults to the current page.
   * Returns {error} when a named page does not exist.
   */
  audit(pageArg) {
    let page = pageArg || penpot.currentPage;
    if (typeof page === "string") {
      const wanted = page;
      page = (penpot.currentFile.pages || []).filter((p) => p.name === wanted)[0] || null;
      if (!page) return { error: "page not found: " + wanted };
    }
    let shapes = 0, boards = 0, texts = 0;
    let tokenFilled = 0, hardFilled = 0, tokenType = 0, hardType = 0;
    let interactive = 0, unnamed = 0, renderMismatch = 0;
    const hardColors = {};
    const mismatches = [];
    const values = {};
    penpot.library.local.tokens.sets.forEach((s) => s.tokens.forEach((t) => { values[t.name] = String(t.value).toUpperCase(); }));
    const walk = (s) => {
      shapes++;
      if (s.type === "board") boards++;
      if (!s.name || /^(Text|Rectangle|Ellipse|Board|Group)$/.test(s.name)) unnamed++;
      const fills = s.fills;
      if (Array.isArray(fills) && fills.length && fills[0] && fills[0].fillColor) {
        if (s.tokens && s.tokens.fill) {
          tokenFilled++;
          const actual = String(fills[0].fillColor).toUpperCase();
          const expected = values[s.tokens.fill];
          if (expected && actual !== expected) {
            renderMismatch++;
            if (mismatches.length < 5) mismatches.push((s.name || s.type) + ": " + s.tokens.fill + " renders " + actual + " not " + expected);
          }
        } else {
          hardFilled++;
          const c = String(fills[0].fillColor).toUpperCase();
          hardColors[c] = (hardColors[c] || 0) + 1;
        }
      }
      if (s.type === "text") {
        texts++;
        if (s.tokens && s.tokens.fontSize) tokenType++; else hardType++;
      }
      if ((s.interactions || []).length) interactive++;
      (s.children || []).forEach(walk);
    };
    (page.root.children || []).forEach(walk);

    const comps = penpot.library.local.components.map((c) => {
      let orphan = false;
      try { orphan = !c.mainInstance(); } catch (e) { orphan = true; }
      return { name: c.name, variant: c.isVariant(), orphan };
    });
    const sets = penpot.library.local.tokens.sets.map((s) => ({ name: s.name, tokens: s.tokens.length, active: s.active }));

    return {
      page: page.name,
      shapes, boards, texts,
      tokenCoverage: {
        fills: tokenFilled + "/" + (tokenFilled + hardFilled),
        textSizes: tokenType + "/" + (tokenType + hardType),
        hardColors: Object.keys(hardColors).sort().map((c) => c + " x" + hardColors[c]),
        renderMismatches: renderMismatch,
        mismatchSample: mismatches,
      },
      interactiveShapes: interactive,
      flows: (page.flows || []).map(
        (f) => f.name + " -> " + (f.startingBoard ? f.startingBoard.name : "(no starting board)"),
      ),
      unnamed,
      components: comps,
      tokenSets: sets,
    };
  },
};

storage.H = H;
return { loaded: H.version };

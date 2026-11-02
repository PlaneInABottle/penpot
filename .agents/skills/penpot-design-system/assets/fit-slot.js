/**
 * fit-slot.js — generic content-derived slot sizing for Penpot build scripts.
 *
 * Load after helpers.js in the same `execute_code` context:
 *   storage.H ... (helpers) + this file -> `storage.FIT`
 *
 * The rule this file exists for: a slot's height is derived from its
 * measured content, never from a fixed grid constant. A calendar that maps
 * minutes to px with a fixed scale while copy height varies paints text
 * over the next row; the lint `fit` family catches it after the fact, this
 * file prevents it at build time.
 *
 * Two modes:
 *  - growable slots (cards, panels, rows): the container resizes to fit.
 *  - fixed slots (time grids, table rows with a contractual pitch): content
 *    that does not fit is a BUILD ERROR, not a warning. Warnings scroll by;
 *    errors stop the screen.
 *
 * Pure geometry (`measure`, `slotHeight`, `fitRows`) touches no Penpot
 * globals and can be reasoned about in isolation. The `*Live` wrappers read
 * Penpot shapes and write sizes back.
 */
const FIT = (function () {
  const SNAP = 4;

  const snap = (v, step) => Math.round(v / (step || SNAP)) * (step || SNAP);

  /** Plain-box union. Boxes: {x, y, w, h}. Returns null when empty. */
  function measure(boxes) {
    const live = (boxes || []).filter((b) => b && b.w > 0 && b.h > 0);
    if (!live.length) return null;
    const l = Math.min(...live.map((b) => b.x));
    const t = Math.min(...live.map((b) => b.y));
    const r = Math.max(...live.map((b) => b.x + b.w));
    const b = Math.max(...live.map((b) => b.y + b.h));
    return { x: l, y: t, w: r - l, h: b - t };
  }

  /** Read a Penpot shape as a plain box: measured ink when available, else the box. */
  function inkOf(shape) {
    if (shape.type === "text" && shape.textBounds && shape.textBounds.height) {
      const b = shape.textBounds;
      return { x: b.x, y: b.y, w: b.width, h: b.height };
    }
    return { x: shape.x, y: shape.y, w: shape.width, h: shape.height };
  }

  /**
   * Container height for content: paddings plus content, floored at minH,
   * snapped to the spacing step. Pure.
   */
  function slotHeight(contentH, opts) {
    const o = opts || {};
    return snap(Math.max(o.minH || 0, contentH + (o.padTop || 0) + (o.padBottom || 0)), o.step);
  }

  /**
   * Grow (or verify) a container around its children's measured ink.
   * Returns {contentH, needed, resized, dy}. When `opts.fixed` is set and
   * the content exceeds the container, THROWS — the build must fail.
   */
  function fitSlotLive(container, children, opts) {
    const o = opts || {};
    const union = measure((children || []).map(inkOf));
    const contentH = union ? union.h : 0;
    const needed = slotHeight(contentH, o);
    const cur = container.height;
    if (o.fixed && needed > cur + (o.tol || 1)) {
      throw new Error(
        "fit: " + container.name + " content needs " + needed +
        "px in a fixed " + Math.round(cur) + "px slot (" +
        (children || []).length + " children) — shorten the copy or grow the slot"
      );
    }
    let dy = 0;
    if (!o.fixed && Math.abs(needed - cur) > (o.tol || 1)) {
      container.resize(container.width, needed);
      dy = needed - cur;
    }
    return { contentH: Math.round(contentH), needed, resized: dy !== 0, dy: Math.round(dy) };
  }

  /**
   * Split a fixed total height across rows that each declare a measured
   * minimum and a weight (e.g. duration). Rows get at least their minimum;
   * leftover space goes to weighted rows. THROWS when the minima exceed
   * the total — a fixed grid that cannot hold its content is a build
   * error, never a silent overlap.
   * Pure: rows = [{id, minH, weight}]. Returns [{id, h, y}].
   */
  function fitRows(totalH, rows, opts) {
    const o = opts || {};
    const list = (rows || []).map((r) => ({ id: r.id, minH: r.minH || 0, weight: r.weight || 0 }));
    const mins = list.reduce((n, r) => n + r.minH, 0);
    if (mins > totalH + (o.tol || 1)) {
      throw new Error(
        "fit: rows need at least " + Math.round(mins) + "px in a fixed " +
        Math.round(totalH) + "px grid — grow the grid or cut " +
        Math.round(mins - totalH) + "px of content"
      );
    }
    const weights = list.reduce((n, r) => n + r.weight, 0);
    let left = totalH - mins;
    const out = [];
    let y = 0;
    list.forEach((r, i) => {
      const last = i === list.length - 1;
      const share = !last && weights > 0 ? Math.floor((left * r.weight) / weights) : left;
      const h = snap(r.minH + share);
      out.push({ id: r.id, h, y: snap(y) });
      y += h;
      left -= share;
    });
    return out;
  }

  /** Move every shape at or below `fromY` down by `dy` (followers ride). Pure on plain boxes. */
  function rideDown(shapes, fromY, dy) {
    if (!dy) return 0;
    let n = 0;
    (shapes || []).forEach((s) => {
      if (s.y >= fromY - 0.5) { s.y = snap(s.y + dy); n++; }
    });
    return n;
  }

  return { SNAP, snap, measure, inkOf, slotHeight, fitSlotLive, fitRows, rideDown };
})();

if (typeof storage !== "undefined") storage.FIT = FIT;

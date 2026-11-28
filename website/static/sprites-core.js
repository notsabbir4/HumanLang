/* HumanLang Sprite Editor: the logic (no screen in here, so it can be tested).
   Pixels are stored as numbers: -1 is a see-through pixel, anything else is 0xRRGGBB.
   The editor makes the SAME text HumanLang already reads:   make a sprite called NAME with pixel size N and M frames
   so nothing about sprites in the language changes. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.HLSprite = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  const T = -1;                                       // see-through
  let COLOURS = { red: "#ff0000", blue: "#0000ff", green: "#008000", yellow: "#ffff00", pink: "#ffc0cb", orange: "#ffa500",
    purple: "#800080", white: "#ffffff", black: "#000000", gray: "#808080", grey: "#808080", brown: "#a52a2a", skin: "#f1c27d" };
  let RESERVED = new Set(["make", "a", "the", "sprite", "game", "play", "draw", "set", "if", "say", "and", "or", "not", "is", "in", "of", "to", "from", "with"]);
  const MAX_FRAMES = 64, MAX_PS = 64;

  // The language's colour words and reserved words are handed over by the page (they come from the real interpreter).
  function setData(d) {
    if (d && d.colours) COLOURS = d.colours;
    if (d && d.reserved) RESERVED = new Set(d.reserved);
  }

  // ---- colours ------------------------------------------------------------------------
  const toHex = (n) => "#" + (n & 0xffffff).toString(16).padStart(6, "0");
  function fromHex(h) {
    h = String(h || "").trim().toLowerCase();
    if (h[0] !== "#") return null;
    let d = h.slice(1);
    if (!/^[0-9a-f]+$/.test(d)) return null;
    if (d.length === 3) d = d.split("").map((c) => c + c).join("");
    return d.length === 6 ? parseInt(d, 16) : null;
  }
  function mix(n, target, amount) {
    const a = [(n >> 16) & 255, (n >> 8) & 255, n & 255], b = [(target >> 16) & 255, (target >> 8) & 255, target & 255];
    const c = a.map((x, i) => Math.round(x + (b[i] - x) * amount));
    return (c[0] << 16) | (c[1] << 8) | c[2];
  }
  // colour words as HumanLang understands them ("red", "dark blue", "sky blue", "#ff8800"); null when it is not a colour
  function resolveColour(text) {
    text = String(text).toLowerCase().replace(/[-_]/g, " ").split(/\s+/).filter(Boolean).join(" ");
    if (!text) return null;
    if (text[0] === "#") return fromHex(text);
    const words = text.split(" "), joined = words.join("");
    if (COLOURS[joined]) return fromHex(COLOURS[joined]);
    if (["dark", "light", "pale", "bright"].includes(words[0]) && words.length > 1) {
      const base = resolveColour(words.slice(1).join(" "));
      if (base !== null) return mix(base, words[0] === "dark" ? 0 : 0xffffff, words[0] === "bright" ? 0 : 0.35);
    }
    return null;
  }
  // the simple colour word for a colour, when HumanLang has one that is exactly it
  const NICE = ["red", "blue", "green", "yellow", "pink", "orange", "purple", "white", "black", "gray", "brown", "skin"];
  function niceName(n) {
    for (const name of NICE) if (COLOURS[name] && fromHex(COLOURS[name]) === n) return name;
    return null;
  }

  // ---- the letters of the picture ----------------------------------------------------------
  // each colour gets one letter; these are the ones we like for the common colours, then a, b, c ... for the rest
  const LIKED = { red: "r", blue: "b", green: "g", yellow: "y", pink: "p", orange: "o", purple: "u", white: "w", black: "k", gray: "e", brown: "n", skin: "s" };
  const POOL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@$%&*+=-~^:;<>/?|_()[]";
  const MAX_COLOURS = POOL.length;

  function sanitiseName(name) {
    let s = String(name || "").trim().toLowerCase().replace(/[\s-]+/g, "_").replace(/[^\p{L}\p{N}_]/gu, "");
    if (!s || /^[\d_]/.test(s)) s = "sprite_" + s.replace(/^_+/, "");
    s = s.replace(/_+$/, "");
    if (RESERVED.has(s)) s = "my_" + s;
    return s;
  }

  // the colours used by the frames, in the order they are first met (so the same picture always gives the same letters)
  function coloursUsed(frames) {
    const seen = [], have = new Set();
    for (const f of frames) for (let i = 0; i < f.length; i++) { const c = f[i]; if (c !== T && !have.has(c)) { have.add(c); seen.push(c); } }
    return seen;
  }

  function letterFor(used) {
    const map = new Map(), taken = new Set();
    for (const c of used) {                             // common colours first, so "red" is always r
      const nm = niceName(c);
      if (nm && LIKED[nm] && !taken.has(LIKED[nm])) { map.set(c, LIKED[nm]); taken.add(LIKED[nm]); }
    }
    let k = 0;
    for (const c of used) {
      if (map.has(c)) continue;
      while (k < POOL.length && taken.has(POOL[k])) k++;
      if (k >= POOL.length) return null;
      map.set(c, POOL[k]); taken.add(POOL[k]);
    }
    return map;
  }

  // ---- making the code ------------------------------------------------------------------------
  // sprite = { name, w, h, ps, frames: [Int32Array(w*h)...] }   ->   { code, warnings, error }
  function generate(sprite) {
    const { w, h, ps, frames } = sprite, warnings = [];
    const name = sanitiseName(sprite.name);
    if (name !== String(sprite.name || "").trim()) warnings.push('The sprite name was changed to "' + name + '" because HumanLang names use letters, numbers and _ and must not be a word HumanLang already uses.');
    if (!(ps >= 1 && ps <= MAX_PS) || ps !== Math.floor(ps)) return { error: "The pixel size must be a whole number from 1 to " + MAX_PS + "." };
    if (!(frames.length >= 1 && frames.length <= MAX_FRAMES)) return { error: "A sprite has 1 to " + MAX_FRAMES + " frames." };
    const used = coloursUsed(frames), letters = letterFor(used);
    if (!letters) return { error: "This picture uses " + used.length + " colours, but HumanLang can give a letter to at most " + MAX_COLOURS + ". Use \"Fewer colours\" to join similar colours." };
    const lines = [];
    let head = "make a sprite called " + name + " with pixel size " + ps;
    if (frames.length > 1) head += " and " + frames.length + " frames";
    lines.push(head);
    const defs = used.map((c) => '"' + letters.get(c) + '" is ' + (niceName(c) || '"' + toHex(c) + '"'));
    for (let i = 0; i < defs.length; i += 4) lines.push("    where " + defs.slice(i, i + 4).join(" and "));
    if (!defs.length) warnings.push("This sprite is empty (every pixel is see-through).");
    for (const f of frames) {
      for (let y = 0; y < h; y++) {
        let row = "";
        for (let x = 0; x < w; x++) { const c = f[y * w + x]; row += c === T ? "." : letters.get(c); }
        lines.push('    "' + row + '"');
      }
    }
    return { code: lines.join("\n") + "\n", warnings, legend: used.map((c) => ({ colour: toHex(c), letter: letters.get(c) })) };
  }

  // a small program that shows the sprite (and animates it when it has frames)
  function demoProgram(sprite) {
    const g = generate(sprite);
    if (g.error) return null;
    const name = sanitiseName(sprite.name), n = sprite.frames.length;
    const W = Math.max(160, sprite.w * sprite.ps + 80), H = Math.max(120, sprite.h * sprite.ps + 60);
    const x = Math.floor((W - sprite.w * sprite.ps) / 2), y = Math.floor((H - sprite.h * sprite.ps) / 2);
    let c = g.code + "\nplay a game titled \"" + name + "\" with size " + W + " by " + H + ' and background "#1b1f2a"\n    every frame\n';
    if (n > 1) c += "        set beat to 1 + (frame number divided evenly by 8) mod " + n + "\n        draw the sprite " + name + " at " + x + ", " + y + " frame beat\n";
    else c += "        draw the sprite " + name + " at " + x + ", " + y + "\n";
    return c;
  }

  // ---- reading code back into a picture -------------------------------------------------------------------
  // text -> { sprites: [{name, w, h, ps, frames}], errors: ["Line 4: ..."] }
  function parse(text) {
    const lines = String(text).replace(/\r/g, "").split("\n"), sprites = [], errors = [];
    const indentOf = (s) => s.match(/^ */)[0].length;
    for (let i = 0; i < lines.length; i++) {
      const m = lines[i].match(/^(\s*)make\s+a\s+sprite\s+called\s+(\S+)\s*(.*)$/i);
      if (!m) continue;
      const startLine = i + 1, ind = m[1].length, name = m[2];
      let rest = m[3], ps = 4, nframes = 1;
      const p = rest.match(/pixel\s+size\s+(\d+(?:\.\d+)?)/i);
      if (p) { ps = Number(p[1]); rest = rest.replace(p[0], ""); }
      const f = rest.match(/(\d+)\s+frames?\b/i);
      if (f) { nframes = Number(f[1]); rest = rest.replace(f[0], ""); }
      if (rest.replace(/\b(with|and)\b|,/gi, "").trim()) { errors.push("Line " + startLine + ": I did not understand \"" + rest.trim() + "\" after the sprite's name."); }
      const legend = { ".": T, " ": T }, rows = [], bad = [];
      let j = i + 1;
      for (; j < lines.length; j++) {
        const ln = lines[j];
        if (!ln.trim()) continue;
        if (indentOf(ln) <= ind) break;
        const t = ln.trim(), no = j + 1;
        if (/^note:/i.test(t)) continue;
        if (/^where\b/i.test(t)) {
          const body = t.replace(/^where\s+/i, ""), re = /"([^"])"\s+is\s+/g, hits = [];
          let mm;
          while ((mm = re.exec(body))) hits.push({ letter: mm[1], at: mm.index, end: re.lastIndex });
          if (!hits.length) { bad.push("Line " + no + ': after "where" I expected a letter in quotes, then "is", then a colour, like: where "r" is red'); continue; }
          hits.forEach((h, k) => {
            let phrase = body.slice(h.end, k + 1 < hits.length ? hits[k + 1].at : body.length).trim();
            phrase = phrase.replace(/(?:\s*,\s*|\s+and\s*)$/i, "").replace(/,\s*$/, "").trim();
            if (/^"[^"]*"$/.test(phrase)) phrase = phrase.slice(1, -1);
            if (/^(none|transparent|nothing)$/i.test(phrase)) { legend[h.letter] = T; return; }
            const c = resolveColour(phrase);
            if (c === null) bad.push("Line " + no + ': I don\'t know the colour "' + phrase + '". Use a colour name like red or dark blue, or a code like "#ff8800".');
            else legend[h.letter] = c;
          });
          continue;
        }
        const r = t.match(/^"([^"]*)"$/);
        if (r) { rows.push({ text: r[1], no }); continue; }
        bad.push("Line " + no + ': I can only read a "where" line or a row in quotes here, not: ' + t);
      }
      i = j - 1;
      const own = bad.slice();
      if (!rows.length) own.push("Line " + startLine + ': the sprite "' + name + '" has no rows of pixels.');
      else {
        const w = rows[0].text.length;
        for (const r of rows) if (r.text.length !== w) { own.push("Line " + r.no + ": every row must be as long as the first (" + w + " letters), but this one has " + r.text.length + "."); break; }
        if (!Number.isInteger(nframes) || nframes < 1 || nframes > MAX_FRAMES) own.push("Line " + startLine + ": a sprite has 1 to " + MAX_FRAMES + " frames.");
        else if (rows.length % nframes) own.push("Line " + startLine + ": " + rows.length + " rows don't split into " + nframes + " frames of equal height.");
        if (!(ps >= 1 && ps <= MAX_PS) || ps !== Math.floor(ps)) own.push("Line " + startLine + ": the pixel size must be a whole number from 1 to " + MAX_PS + ".");
        if (!own.length) {
          for (const r of rows) for (const ch of r.text) if (!(ch in legend)) { own.push("Line " + r.no + ': the letter "' + ch + '" has no colour. Add a line like: where "' + ch + '" is red'); break; }
        }
        if (!own.length) {
          const h = rows.length / nframes, fr = [];
          for (let k = 0; k < nframes; k++) {
            const buf = new Int32Array(w * h).fill(T);
            for (let y = 0; y < h; y++) { const s = rows[k * h + y].text; for (let x = 0; x < w; x++) buf[y * w + x] = legend[s[x]]; }
            fr.push(buf);
          }
          sprites.push({ name, w, h, ps, frames: fr });
        }
      }
      for (const e of own) errors.push(e);
    }
    if (!sprites.length && !errors.length) errors.push('I did not find a sprite here. A sprite starts with a line like: make a sprite called heart with pixel size 4');
    return { sprites, errors };
  }

  // ---- drawing helpers (all work on one frame's pixels; each returns the list of pixel indexes it changed) ----
  function put(buf, w, h, x, y, c, out) {
    if (x < 0 || y < 0 || x >= w || y >= h) return;
    const i = y * w + x;
    if (buf[i] !== c) { out.push(i, buf[i]); buf[i] = c; }       // remembers (where, what was there) for undo
  }
  function linePoints(x0, y0, x1, y1) {
    const pts = [];
    let dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1, err = dx + dy;
    for (;;) {
      pts.push([x0, y0]);
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 >= dy) { err += dy; x0 += sx; }
      if (e2 <= dx) { err += dx; y0 += sy; }
    }
    return pts;
  }
  function rectPoints(x0, y0, x1, y1, filled) {
    const a = Math.min(x0, x1), b = Math.max(x0, x1), c = Math.min(y0, y1), d = Math.max(y0, y1), pts = [];
    for (let y = c; y <= d; y++) for (let x = a; x <= b; x++) if (filled || x === a || x === b || y === c || y === d) pts.push([x, y]);
    return pts;
  }
  // a circle or oval that fits the box between the two corners
  function ovalPoints(x0, y0, x1, y1, filled) {
    const a = Math.min(x0, x1), b = Math.max(x0, x1), c = Math.min(y0, y1), d = Math.max(y0, y1), pts = [];
    const cx = (a + b) / 2, cy = (c + d) / 2, rx = (b - a + 1) / 2, ry = (d - c + 1) / 2;
    const inside = (x, y, ax, ay) => ax > 0 && ay > 0 && ((x - cx) / ax) ** 2 + ((y - cy) / ay) ** 2 <= 1;
    for (let y = c; y <= d; y++) for (let x = a; x <= b; x++) {
      if (!inside(x, y, rx, ry)) continue;
      if (filled || !inside(x, y, rx - 1, ry - 1)) pts.push([x, y]);
    }
    return pts;
  }
  function floodFill(buf, w, h, x, y, c, out) {
    if (x < 0 || y < 0 || x >= w || y >= h) return;
    const target = buf[y * w + x];
    if (target === c) return;
    const stack = [[x, y]];
    while (stack.length) {
      let [px, py] = stack.pop();
      while (px >= 0 && buf[py * w + px] === target) px--;
      px++;
      let up = false, down = false;
      while (px < w && buf[py * w + px] === target) {
        out.push(py * w + px, target); buf[py * w + px] = c;
        if (py > 0) { const u = buf[(py - 1) * w + px] === target; if (u && !up) stack.push([px, py - 1]); up = u; }
        if (py < h - 1) { const d = buf[(py + 1) * w + px] === target; if (d && !down) stack.push([px, py + 1]); down = d; }
        px++;
      }
    }
  }
  // undo: a "change" is the list [index, old, index, old, ...] a tool made; undoing puts the old pixels back
  function undoChange(buf, out) { const after = []; for (let k = out.length - 2; k >= 0; k -= 2) { after.push(out[k], buf[out[k]]); buf[out[k]] = out[k + 1]; } return after; }

  // ---- fewer colours: join the closest colours until at most `keep` are left (the user asks for this; nothing is dropped silently) ----
  function reduceColours(frames, keep) {
    const used = coloursUsed(frames).slice();
    const dist = (a, b) => { const dr = ((a >> 16) & 255) - ((b >> 16) & 255), dg = ((a >> 8) & 255) - ((b >> 8) & 255), db = (a & 255) - (b & 255); return dr * dr + dg * dg + db * db; };
    const into = new Map(used.map((c) => [c, c]));
    let live = used.slice();
    while (live.length > keep) {
      let best = null;
      for (let i = 0; i < live.length; i++) for (let j = i + 1; j < live.length; j++) { const d = dist(live[i], live[j]); if (!best || d < best[0]) best = [d, i, j]; }
      const [, i, j] = best, drop = live[j];
      for (const [k, v] of into) if (v === drop) into.set(k, live[i]);
      live.splice(j, 1);
    }
    for (const f of frames) for (let i = 0; i < f.length; i++) if (f[i] !== T) f[i] = into.get(f[i]);
    return live.length;
  }

  // ---- changing the size (keeps the picture's top-left corner) ----
  function resizeFrame(buf, w, h, nw, nh) {
    const out = new Int32Array(nw * nh).fill(T);
    for (let y = 0; y < Math.min(h, nh); y++) for (let x = 0; x < Math.min(w, nw); x++) out[y * nw + x] = buf[y * w + x];
    return out;
  }

  // The handles to the whole thing:
  return { T, MAX_FRAMES, MAX_PS, MAX_COLOURS, setData, toHex, fromHex, resolveColour, niceName, sanitiseName, coloursUsed,
    generate, demoProgram, parse, put, linePoints, rectPoints, ovalPoints, floodFill, undoChange, reduceColours, resizeFrame };
});

/* HumanLang Sprite Editor: the screen. The logic (making/reading the code, flood fill, ...) is in sprites-core.js. */
(function () {
  "use strict";
  const S = window.HLSprite;
  if (!S || !document.getElementById("sp")) return;
  S.setData(window.HL_SPRITE_DATA);
  const T = S.T;
  const $ = (id) => document.getElementById(id);
  const root = $("sp");

  // ---- icons -----------------------------------------------------------------------------------
  const ICONS = {
    pencil: '<path d="M3 21l3.5-1 11-11a2.1 2.1 0 0 0-3-3l-11 11L3 21z"/><path d="M13.5 7.5l3 3"/>',
    eraser: '<path d="M20 20H9l-5-5a2 2 0 0 1 0-3l8-8a2 2 0 0 1 3 0l5 5a2 2 0 0 1 0 3l-7 8"/><path d="M8 11l6 6"/>',
    bucket: '<path d="M5 11l6-6 8 8-6 6a2 2 0 0 1-3 0l-5-5a2 2 0 0 1 0-3z"/><path d="M19 15s2 2.5 2 4a2 2 0 0 1-4 0c0-1.5 2-4 2-4z"/>',
    picker: '<path d="M14 4l6 6-3 3-6-6 3-3z"/><path d="M11 7l-7 7v5h5l7-7"/>',
    line: '<path d="M5 19L19 5"/>',
    rect: '<rect x="4" y="5" width="16" height="14" rx="1"/>',
    oval: '<ellipse cx="12" cy="12" rx="8" ry="6.5"/>',
    hand: '<path d="M8 13V6a1.5 1.5 0 0 1 3 0v5m0-6.5a1.5 1.5 0 0 1 3 0V11m0-4a1.5 1.5 0 0 1 3 0v6.5c0 4-2 6.5-5.5 6.5S7 19 5.5 16.5L4 14a1.5 1.5 0 0 1 2.5-1.5L8 14"/>',
    undo: '<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',
    redo: '<path d="M15 14l5-5-5-5"/><path d="M20 9H10a6 6 0 0 0 0 12h3"/>',
    play: '<path d="M7 4l13 8-13 8z" style="fill:currentColor"/>',
    pause: '<rect x="6" y="4" width="4" height="16" style="fill:currentColor"/><rect x="14" y="4" width="4" height="16" style="fill:currentColor"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    left: '<path d="M15 5l-7 7 7 7"/>',
    right: '<path d="M9 5l7 7-7 7"/>',
    new: '<path d="M6 3h8l5 5v13H6z"/><path d="M14 3v5h5M12 12v6M9 15h6"/>',
    open: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    save: '<path d="M5 3h12l3 3v15H5z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/>',
    import: '<path d="M12 3v12M7 10l5 5 5-5M4 20h16"/>',
    code: '<path d="M8 8l-5 4 5 4M16 8l5 4-5 4M14 5l-4 14"/>',
    help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 .9-1 1.7M12 17v.1"/>',
  };
  document.querySelectorAll("i[data-icon]").forEach((el) => {
    el.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[el.dataset.icon] || "") + "</svg>";
  });
  const setIcon = (btn, name) => { const i = btn.querySelector("i"); if (i) { i.dataset.icon = name; i.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + "</svg>"; } };

  // ---- the sprite we are drawing ------------------------------------------------------------------
  const newId = () => "s" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  let doc = { id: newId(), name: "player", w: 16, h: 16, ps: 4, frames: [new Int32Array(256).fill(T)], cur: 0 };
  let tool = "pencil", color = 0xe43a4c, shapeFilled = false, dirty = false, saved = false;
  let showGrid = true, onion = false, playing = false, playIdx = 0, fps = 6;
  let undoSt = [], redoSt = [];
  const MAX_UNDO = 300, MAX_STRUCT = 40;

  // ---- remembering things (all wrapped: a blocked browser store must not break the editor) ------------
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } },
  };
  const LIB = "hl-sprites-v1", DRAFT = "hl-sprite-draft-v1", PAL = "hl-sprite-palette-v1", RECENT = "hl-sprite-recent-v1", TOUR = "hl-sprite-tour-v1";
  const rle = (buf) => { const o = []; for (let i = 0; i < buf.length;) { let j = i; while (j < buf.length && buf[j] === buf[i]) j++; o.push(buf[i], j - i); i = j; } return o; };
  const unrle = (a, n) => { const b = new Int32Array(n); let p = 0; for (let i = 0; i < a.length; i += 2) { b.fill(a[i], p, p + a[i + 1]); p += a[i + 1]; } return b; };
  const pack = (d) => ({ format: "hl-sprite", id: d.id, name: d.name, w: d.w, h: d.h, ps: d.ps, frames: d.frames.map(rle) });
  function unpack(o) {
    if (!o || o.format !== "hl-sprite" || !(o.w >= 1 && o.w <= 256 && o.h >= 1 && o.h <= 256) || !Array.isArray(o.frames) || !o.frames.length) throw new Error("This is not a sprite file from the editor.");
    const frames = o.frames.slice(0, S.MAX_FRAMES).map((f) => unrle(f, o.w * o.h));
    return { id: o.id || newId(), name: String(o.name || "sprite"), w: o.w | 0, h: o.h | 0, ps: Math.min(64, Math.max(1, o.ps | 0 || 4)), frames, cur: 0 };
  }
  let draftTimer = 0;
  function saveDraftSoon() { clearTimeout(draftTimer); draftTimer = setTimeout(() => store.set(DRAFT, { doc: pack(doc), dirty, saved }), 500); }

  // ---- little helpers ------------------------------------------------------------------------------------
  let toastTimer = 0;
  function toast(msg) { const t = $("sp-toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("show"), 2600); }
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const css = (n) => (n === T ? "transparent" : S.toHex(n));
  function download(name, text, type) {
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type: type || "text/plain" })); a.download = name;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
  const frame = () => doc.frames[doc.cur];

  // ---- the drawing area -----------------------------------------------------------------------------------
  const cv = $("sp-canvas"), wrap = $("sp-wrap"), ctx = cv.getContext("2d", { alpha: false });
  const off = document.createElement("canvas"), offx = off.getContext("2d");
  const onionCv = document.createElement("canvas"), onionx = onionCv.getContext("2d");
  const checker = document.createElement("canvas");
  const ZOOMS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48, 64];
  let dpr = 1, view = { zs: 12, z: 12, ox: 0, oy: 0 };
  let hover = null, preview = null, drag = null, panning = null, spaceDown = false, renderQueued = false, offDirty = true;
  const pointers = new Map();
  let gesture = null;

  function toImage(buf, canvas, w, h) {
    canvas.width = w; canvas.height = h;
    const c = canvas.getContext("2d"), id = c.createImageData(w, h), d = id.data;
    for (let i = 0; i < buf.length; i++) { const v = buf[i]; if (v !== T) { d[i * 4] = (v >> 16) & 255; d[i * 4 + 1] = (v >> 8) & 255; d[i * 4 + 2] = v & 255; d[i * 4 + 3] = 255; } }
    c.putImageData(id, 0, 0);
  }
  function buildChecker() {
    checker.width = doc.w; checker.height = doc.h;
    const c = checker.getContext("2d"), id = c.createImageData(doc.w, doc.h), d = id.data;
    for (let y = 0; y < doc.h; y++) for (let x = 0; x < doc.w; x++) { const v = (x + y) & 1 ? 0x2b3142 : 0x232836, i = (y * doc.w + x) * 4; d[i] = v >> 16; d[i + 1] = (v >> 8) & 255; d[i + 2] = v & 255; d[i + 3] = 255; }
    c.putImageData(id, 0, 0);
  }
  function layout() {
    dpr = window.devicePixelRatio || 1;
    const r = wrap.getBoundingClientRect();
    cv.width = Math.max(1, Math.round(r.width * dpr)); cv.height = Math.max(1, Math.round(r.height * dpr));
    setZoom(view.zs, null, true);
  }
  function setZoom(zs, anchor, keepCentre) {
    const oldz = view.z, cw = cv.width, ch = cv.height;
    view.zs = zs; view.z = Math.max(1, Math.round(zs * dpr));
    if (anchor && oldz) { const lx = (anchor.x - view.ox) / oldz, ly = (anchor.y - view.oy) / oldz; view.ox = Math.round(anchor.x - lx * view.z); view.oy = Math.round(anchor.y - ly * view.z); }
    else if (keepCentre) { view.ox = Math.round((cw - doc.w * view.z) / 2); view.oy = Math.round((ch - doc.h * view.z) / 2); }
    clampView(); $("z-val").textContent = zs + "\u00d7"; queue();
  }
  function clampView() {
    const W = doc.w * view.z, H = doc.h * view.z, m = 48 * dpr;
    view.ox = clamp(view.ox, Math.min(m - W, (cv.width - W) / 2), Math.max(cv.width - m, (cv.width - W) / 2));
    view.oy = clamp(view.oy, Math.min(m - H, (cv.height - H) / 2), Math.max(cv.height - m, (cv.height - H) / 2));
  }
  function fit() {
    const cw = cv.width / dpr - 40, ch = cv.height / dpr - 40;
    let best = 1; for (const z of ZOOMS) if (doc.w * z <= cw && doc.h * z <= ch) best = z;
    view.ox = view.oy = 0; setZoom(best, null, true);
  }
  function queue() { if (!renderQueued) { renderQueued = true; requestAnimationFrame(render); } }

  function render() {
    renderQueued = false;
    const z = view.z, ox = view.ox, oy = view.oy, W = doc.w * z, H = doc.h * z;
    ctx.imageSmoothingEnabled = false;
    ctx.fillStyle = "#0a0c11"; ctx.fillRect(0, 0, cv.width, cv.height);
    if (checker.width !== doc.w || checker.height !== doc.h) buildChecker();
    ctx.drawImage(checker, ox, oy, W, H);
    if (onion && doc.cur > 0) { toImage(doc.frames[doc.cur - 1], onionCv, doc.w, doc.h); ctx.globalAlpha = 0.3; ctx.drawImage(onionCv, ox, oy, W, H); ctx.globalAlpha = 1; }
    if (offDirty || off.width !== doc.w || off.height !== doc.h) { toImage(frame(), off, doc.w, doc.h); offDirty = false; }
    ctx.drawImage(off, ox, oy, W, H);
    if (preview) {
      ctx.fillStyle = tool === "eraser" ? "#ffffff66" : css(color);
      for (const [x, y] of preview) ctx.fillRect(ox + x * z, oy + y * z, z, z);
    }
    if (showGrid && z >= 8) {
      ctx.strokeStyle = "rgba(255,255,255,.13)"; ctx.lineWidth = 1; ctx.beginPath();
      for (let x = 0; x <= doc.w; x++) { const px = ox + x * z + 0.5; ctx.moveTo(px, oy); ctx.lineTo(px, oy + H); }
      for (let y = 0; y <= doc.h; y++) { const py = oy + y * z + 0.5; ctx.moveTo(ox, py); ctx.lineTo(ox + W, py); }
      ctx.stroke();
    }
    ctx.strokeStyle = "rgba(255,255,255,.45)"; ctx.lineWidth = 1; ctx.strokeRect(ox - 0.5, oy - 0.5, W + 1, H + 1);
    if (hover && !panning && tool !== "hand") {
      ctx.strokeStyle = "#ffffffcc"; ctx.lineWidth = Math.max(1, Math.round(dpr)); ctx.strokeRect(ox + hover[0] * z + 0.5, oy + hover[1] * z + 0.5, z - 1, z - 1);
    }
  }

  // ---- looking at the pointer -------------------------------------------------------------------------------
  function spot(e) {
    const r = cv.getBoundingClientRect(), px = (e.clientX - r.left) * dpr, py = (e.clientY - r.top) * dpr;
    const x = Math.floor((px - view.ox) / view.z), y = Math.floor((py - view.oy) / view.z);
    return { px, py, x, y, inside: x >= 0 && y >= 0 && x < doc.w && y < doc.h, cx: clamp(x, 0, doc.w - 1), cy: clamp(y, 0, doc.h - 1) };
  }
  const drawColour = () => (tool === "eraser" ? T : color);

  function shapePoints(a, b) {
    if (tool === "line") return S.linePoints(a[0], a[1], b[0], b[1]);
    if (tool === "rect") return S.rectPoints(a[0], a[1], b[0], b[1], shapeFilled);
    return S.ovalPoints(a[0], a[1], b[0], b[1], shapeFilled);
  }
  function touchPixel(x, y) { S.put(frame(), doc.w, doc.h, x, y, drawColour(), drag.ch); offDirty = true; }
  function cancelStroke() { if (drag) { if (drag.ch && drag.ch.length) { S.undoChange(frame(), drag.ch); offDirty = true; } drag = null; preview = null; queue(); } }
  function endStroke() {
    if (!drag) return;
    const d = drag; drag = null;
    if (d.shape && preview) { const c = drawColour(); for (const [x, y] of preview) S.put(frame(), doc.w, doc.h, x, y, c, d.ch); offDirty = true; }
    preview = null;
    if (d.ch.length) { pushChange(doc.cur, d.ch); if (drawColour() !== T) remember(drawColour()); thumb(doc.cur); }
    queue();
  }

  cv.addEventListener("contextmenu", (e) => e.preventDefault());
  cv.addEventListener("pointerdown", (e) => {
    cv.focus({ preventScroll: true });
    try { cv.setPointerCapture(e.pointerId); } catch (err) { /* fine */ }
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 2) { cancelStroke(); panning = null; startGesture(); return; }
    if (pointers.size > 2) return;
    const wantPan = e.button === 1 || e.button === 2 || spaceDown || tool === "hand";
    if (wantPan) { panning = { x: e.clientX, y: e.clientY, ox: view.ox, oy: view.oy }; wrap.classList.add("panning"); return; }
    if (e.button !== 0) return;
    const p = spot(e);
    if (!p.inside) return;                                      // a click outside the picture does nothing
    if (tool === "picker") { pickAt(p.x, p.y); return; }
    if (tool === "bucket") { const ch = []; S.floodFill(frame(), doc.w, doc.h, p.x, p.y, color, ch); offDirty = true; if (ch.length) { pushChange(doc.cur, ch); remember(color); thumb(doc.cur); } queue(); return; }
    drag = { ch: [], last: [p.x, p.y], start: [p.x, p.y], shape: tool === "line" || tool === "rect" || tool === "oval" };
    if (drag.shape) preview = shapePoints(drag.start, drag.start); else touchPixel(p.x, p.y);
    queue();
  });
  cv.addEventListener("pointermove", (e) => {
    if (pointers.has(e.pointerId)) pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (gesture && pointers.size >= 2) { moveGesture(); return; }
    if (panning) { view.ox = panning.ox + (e.clientX - panning.x) * dpr; view.oy = panning.oy + (e.clientY - panning.y) * dpr; clampView(); queue(); return; }
    const p = spot(e);
    hover = p.inside ? [p.x, p.y] : null;
    $("s-pos").textContent = p.inside ? "x " + p.x + ", y " + p.y + (frame()[p.y * doc.w + p.x] === T ? "  (see-through)" : "  " + S.toHex(frame()[p.y * doc.w + p.x])) : " ";
    if (drag) {
      if (drag.shape) preview = shapePoints(drag.start, [p.cx, p.cy]);
      else { for (const [x, y] of S.linePoints(drag.last[0], drag.last[1], p.cx, p.cy).slice(1)) touchPixel(x, y); drag.last = [p.cx, p.cy]; }
    }
    queue();
  });
  function release(e) {
    pointers.delete(e.pointerId);
    if (gesture && pointers.size < 2) gesture = null;
    if (pointers.size === 0) { endStroke(); panning = null; wrap.classList.remove("panning"); }
  }
  cv.addEventListener("pointerup", release);
  cv.addEventListener("pointercancel", release);
  cv.addEventListener("pointerleave", () => { hover = null; $("s-pos").textContent = " "; queue(); });
  cv.addEventListener("wheel", (e) => {
    e.preventDefault();
    const r = cv.getBoundingClientRect(), a = { x: (e.clientX - r.left) * dpr, y: (e.clientY - r.top) * dpr };
    stepZoom(e.deltaY < 0 ? 1 : -1, a);
  }, { passive: false });
  function stepZoom(dir, anchor) {
    let i = ZOOMS.indexOf(view.zs); if (i < 0) i = ZOOMS.findIndex((z) => z >= view.zs);
    const n = clamp(i + dir, 0, ZOOMS.length - 1);
    setZoom(ZOOMS[n], anchor || { x: cv.width / 2, y: cv.height / 2 });
  }
  function startGesture() {
    const [a, b] = [...pointers.values()];
    gesture = { d: Math.hypot(a.x - b.x, a.y - b.y) || 1, zs: view.zs, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2, ox: view.ox, oy: view.oy };
  }
  function moveGesture() {
    const [a, b] = [...pointers.values()], d = Math.hypot(a.x - b.x, a.y - b.y) || 1, mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    const want = gesture.zs * d / gesture.d, nz = ZOOMS.reduce((best, z) => (Math.abs(z - want) < Math.abs(best - want) ? z : best), ZOOMS[0]);
    if (nz !== view.zs) { const r = cv.getBoundingClientRect(); setZoom(nz, { x: (mx - r.left) * dpr, y: (my - r.top) * dpr }); }
    view.ox += (mx - gesture.mx) * dpr; view.oy += (my - gesture.my) * dpr; gesture.mx = mx; gesture.my = my; clampView(); queue();
  }

  function pickAt(x, y) {
    const v = frame()[y * doc.w + x];
    if (v === T) { toast("That pixel is see-through. Pick a pixel that has a colour."); return; }
    setColour(v); remember(v);
  }

  // ---- history (what changed, not whole copies) ------------------------------------------------------------------------
  const snapshot = () => ({ w: doc.w, h: doc.h, ps: doc.ps, cur: doc.cur, frames: doc.frames.map((f) => f.slice()) });
  function restore(s) {
    const same = doc.w === s.w && doc.h === s.h;
    doc.w = s.w; doc.h = s.h; doc.ps = s.ps; doc.cur = clamp(s.cur, 0, s.frames.length - 1); doc.frames = s.frames.map((f) => f.slice());
    offDirty = true; syncAll(same);
  }
  function trimStructs() { let n = 0; for (let i = undoSt.length - 1; i >= 0; i--) if (undoSt[i].struct && ++n > MAX_STRUCT) { undoSt.splice(0, i + 1); break; } }
  function pushChange(fi, change) {
    if (!change.length) return;
    undoSt.push({ fi, change }); if (undoSt.length > MAX_UNDO) undoSt.shift();
    redoSt = []; changed();
  }
  function structural(fn) {          // for things that change the frames, the size or the pixel size
    const before = snapshot(); fn();
    undoSt.push({ struct: true, before, after: snapshot() }); trimStructs(); if (undoSt.length > MAX_UNDO) undoSt.shift();
    redoSt = []; offDirty = true; changed(); syncAll(before.w === doc.w && before.h === doc.h);
  }
  function undo() {
    const e = undoSt.pop(); if (!e) return;
    if (e.struct) { restore(e.before); redoSt.push(e); }
    else { const after = S.undoChange(doc.frames[e.fi], e.change); redoSt.push({ fi: e.fi, change: after }); doc.cur = e.fi; offDirty = true; thumb(e.fi); syncAll(true); }
    changed(true);
  }
  function redo() {
    const e = redoSt.pop(); if (!e) return;
    if (e.struct) { restore(e.after); undoSt.push(e); }
    else { const back = S.undoChange(doc.frames[e.fi], e.change); undoSt.push({ fi: e.fi, change: back }); doc.cur = e.fi; offDirty = true; thumb(e.fi); syncAll(true); }
    changed(true);
  }
  function changed(keepRedo) { dirty = true; updateUndoUi(); updateInfo(); saveDraftSoon(); queue(); miniDraw(); }
  function updateUndoUi() { $("b-undo").disabled = !undoSt.length; $("b-redo").disabled = !redoSt.length; }

  // ---- colours -----------------------------------------------------------------------------------------------------------------
  const DEFAULT_PAL = ["#141c3e", "#e43a4c", "#f58b3a", "#ffd95c", "#6fd36a", "#1e8f4e", "#2eb2f5", "#2b5fd6", "#8e4fd6", "#ff8fc8", "#f1c27d", "#a0623a", "#ffffff", "#c3c8d4", "#7b8498", "#000000"];
  let palette = store.get(PAL, null) || DEFAULT_PAL.slice(), recent = store.get(RECENT, []);
  function swatch(hex, on) { const b = document.createElement("button"); b.type = "button"; b.style.background = hex; b.title = hex; b.setAttribute("aria-label", "Colour " + hex); if (on) b.className = "on"; return b; }
  function renderColours() {
    const cur = S.toHex(color);
    $("c-swatch").style.background = cur; $("c-hex").value = cur;
    const pal = $("c-pal"); pal.textContent = "";
    palette.forEach((h, i) => {
      const b = swatch(h, h === cur);
      b.onclick = () => setColour(S.fromHex(h));
      b.oncontextmenu = (e) => { e.preventDefault(); removePal(i); };
      let t = 0; b.addEventListener("pointerdown", (e) => { if (e.pointerType === "touch") t = setTimeout(() => removePal(i), 650); }); b.addEventListener("pointerup", () => clearTimeout(t)); b.addEventListener("pointerleave", () => clearTimeout(t));
      pal.appendChild(b);
    });
    const rec = $("c-recent"); rec.textContent = "";
    if (!recent.length) { const s = document.createElement("span"); s.className = "sp-hint"; s.textContent = "Colours you use show up here."; rec.appendChild(s); }
    recent.forEach((h) => { const b = swatch(h, h === cur); b.onclick = () => setColour(S.fromHex(h)); rec.appendChild(b); });
  }
  function removePal(i) { const h = palette[i]; palette.splice(i, 1); store.set(PAL, palette); renderColours(); toast("Removed " + h + " from your palette."); }
  function setColour(n) { color = n; if (tool === "eraser" || tool === "hand" || tool === "picker") { /* keep the tool: they may be choosing before drawing */ } renderColours(); queue(); }
  function remember(n) { const h = S.toHex(n); if (recent[0] === h) return; recent = [h, ...recent.filter((x) => x !== h)].slice(0, 12); store.set(RECENT, recent); renderColours(); }
  $("c-swatch").onclick = () => $("c-input").click();
  $("c-input").oninput = (e) => setColour(S.fromHex(e.target.value));
  $("c-input").onchange = (e) => remember(S.fromHex(e.target.value));
  $("c-hex").onchange = (e) => {
    const n = S.resolveColour(e.target.value.trim());
    if (n === null) { toast('I don\'t know the colour "' + e.target.value + '". Try a code like #ff8800 or a name like sky blue.'); renderColours(); return; }
    setColour(n); remember(n);
  };
  $("c-hex").onkeydown = (e) => { if (e.key === "Enter") e.target.blur(); e.stopPropagation(); };
  $("c-add").onclick = () => { const h = S.toHex(color); if (palette.includes(h)) { toast("That colour is already in your palette."); return; } palette.push(h); store.set(PAL, palette); renderColours(); };

  // ---- tools ----------------------------------------------------------------------------------------------------------------------
  function setTool(t) {
    tool = t;
    document.querySelectorAll(".sp-tool").forEach((b) => b.classList.toggle("on", b.dataset.tool === t));
    $("o-shape").hidden = !(t === "line" || t === "rect" || t === "oval") || t === "line";
    wrap.classList.toggle("pan", t === "hand"); wrap.classList.toggle("picker", t === "picker");
    const tips = { pencil: "Click or drag to draw.", eraser: "Click or drag to erase.", bucket: "Click to fill an area.", picker: "Click a pixel to use its colour.", line: "Drag from one point to another.", rect: "Drag to make a box.", oval: "Drag to make a circle or oval.", hand: "Drag to move the picture." };
    $("s-tip").textContent = tips[t] || ""; queue();
  }
  document.querySelectorAll(".sp-tool").forEach((b) => (b.onclick = () => setTool(b.dataset.tool)));
  $("o-outline").onclick = () => { shapeFilled = false; $("o-outline").classList.add("on"); $("o-filled").classList.remove("on"); };
  $("o-filled").onclick = () => { shapeFilled = true; $("o-filled").classList.add("on"); $("o-outline").classList.remove("on"); };
  $("o-onion").onchange = (e) => { onion = e.target.checked; queue(); };
  $("o-grid").onchange = (e) => { showGrid = e.target.checked; queue(); };
  $("z-in").onclick = () => stepZoom(1); $("z-out").onclick = () => stepZoom(-1); $("z-fit").onclick = fit;
  $("b-undo").onclick = undo; $("b-redo").onclick = redo;

  // ---- sprite properties -----------------------------------------------------------------------------------------------------------
  const SIZES = [8, 16, 24, 32, 48, 64];
  function chips(box, onPick, isOn) {
    box.textContent = "";
    for (const n of SIZES) { const b = document.createElement("button"); b.type = "button"; b.textContent = n + "×" + n; b.className = isOn(n) ? "on" : ""; b.onclick = () => onPick(n); box.appendChild(b); }
  }
  function updateInfo() {
    $("sp-info").textContent = doc.w + " × " + doc.h + " · pixel size " + doc.ps + " · " + doc.frames.length + (doc.frames.length === 1 ? " frame" : " frames") + (dirty ? " · not saved" : saved ? " · saved" : "");
    $("p-note").textContent = "In a game each pixel is " + doc.ps + " × " + doc.ps + " screen pixels, so this sprite is " + doc.w * doc.ps + " × " + doc.h * doc.ps + ". Checkerboard pixels are see-through.";
  }
  function syncProps() {
    if (document.activeElement !== $("sp-name")) $("sp-name").value = doc.name;
    $("p-w").value = doc.w; $("p-h").value = doc.h; $("p-ps").value = doc.ps;
    chips($("p-chips"), (n) => { $("p-w").value = n; $("p-h").value = n; syncChips(); }, (n) => doc.w === n && doc.h === n);
    updateInfo();
  }
  function syncChips() { const w = +$("p-w").value, h = +$("p-h").value; [...$("p-chips").children].forEach((b, i) => b.classList.toggle("on", SIZES[i] === w && w === h)); }
  $("sp-name").oninput = (e) => { doc.name = e.target.value; dirty = true; updateInfo(); saveDraftSoon(); };
  $("p-w").oninput = syncChips; $("p-h").oninput = syncChips;
  $("p-resize").onclick = () => {
    const w = Math.round(+$("p-w").value), h = Math.round(+$("p-h").value);
    if (!(w >= 1 && w <= 256 && h >= 1 && h <= 256)) { toast("The width and the height must be 1 to 256."); syncProps(); return; }
    if (w === doc.w && h === doc.h) return;
    if ((w < doc.w || h < doc.h) && !confirm("The picture gets smaller, so what is outside the new size is cut off (you can undo it). Continue?")) { syncProps(); return; }
    structural(() => { doc.frames = doc.frames.map((f) => S.resizeFrame(f, doc.w, doc.h, w, h)); doc.w = w; doc.h = h; });
    fit();
  };
  $("p-ps").onchange = () => {
    const n = Math.round(+$("p-ps").value);
    if (!(n >= 1 && n <= 64)) { toast("The pixel size must be 1 to 64."); syncProps(); return; }
    if (n !== doc.ps) structural(() => { doc.ps = n; });
  };

  // ---- frames and the little animation -------------------------------------------------------------------------------------------------
  const framesBox = $("sp-frames"), mini = $("sp-mini");
  function thumb(i) { const c = framesBox.children[i] && framesBox.children[i].querySelector("canvas"); if (c) toImage(doc.frames[i], c, doc.w, doc.h); }
  function renderFrames() {
    framesBox.textContent = "";
    doc.frames.forEach((f, i) => {
      const d = document.createElement("div"); d.className = "sp-fr" + (i === doc.cur ? " on" : ""); d.setAttribute("role", "option"); d.setAttribute("aria-selected", i === doc.cur ? "true" : "false"); d.tabIndex = 0;
      const c = document.createElement("canvas"); toImage(f, c, doc.w, doc.h); d.appendChild(c);
      const l = document.createElement("span"); l.textContent = "Frame " + (i + 1); d.appendChild(l);
      d.onclick = () => selectFrame(i);
      d.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectFrame(i); } };
      framesBox.appendChild(d);
    });
    const on = framesBox.children[doc.cur];                       // keep the chosen frame in view (only the strip scrolls, never the page)
    if (on) { const l = on.offsetLeft - framesBox.offsetLeft, r = l + on.offsetWidth; if (l < framesBox.scrollLeft) framesBox.scrollLeft = l - 8; else if (r > framesBox.scrollLeft + framesBox.clientWidth) framesBox.scrollLeft = r - framesBox.clientWidth + 8; }
    $("f-del").disabled = doc.frames.length < 2; $("f-left").disabled = doc.cur === 0; $("f-right").disabled = doc.cur === doc.frames.length - 1;
  }
  function selectFrame(i) { if (drag) endStroke(); doc.cur = clamp(i, 0, doc.frames.length - 1); offDirty = true; renderFrames(); queue(); miniDraw(); }
  $("f-add").onclick = () => { if (doc.frames.length >= S.MAX_FRAMES) { toast("A sprite can have at most " + S.MAX_FRAMES + " frames."); return; } structural(() => { doc.frames.splice(doc.cur + 1, 0, new Int32Array(doc.w * doc.h).fill(T)); doc.cur++; }); };
  $("f-dup").onclick = () => { if (doc.frames.length >= S.MAX_FRAMES) { toast("A sprite can have at most " + S.MAX_FRAMES + " frames."); return; } structural(() => { doc.frames.splice(doc.cur + 1, 0, frame().slice()); doc.cur++; }); };
  $("f-del").onclick = () => { if (doc.frames.length < 2) return; structural(() => { doc.frames.splice(doc.cur, 1); doc.cur = Math.min(doc.cur, doc.frames.length - 1); }); };
  $("f-left").onclick = () => { if (doc.cur > 0) structural(() => { const f = doc.frames; [f[doc.cur - 1], f[doc.cur]] = [f[doc.cur], f[doc.cur - 1]]; doc.cur--; }); };
  $("f-right").onclick = () => { if (doc.cur < doc.frames.length - 1) structural(() => { const f = doc.frames; [f[doc.cur + 1], f[doc.cur]] = [f[doc.cur], f[doc.cur + 1]]; doc.cur++; }); };

  let miniTimer = 0;
  function miniDraw() {
    const i = playing ? playIdx % doc.frames.length : doc.cur;
    toImage(doc.frames[i], mini, doc.w, doc.h);
    const k = Math.max(1, Math.floor(Math.min(88 / doc.w, 72 / doc.h)));
    mini.style.width = doc.w * k + "px"; mini.style.height = doc.h * k + "px";
    [...framesBox.children].forEach((c, j) => c.classList.toggle("playing", playing && j === i));
  }
  function setPlaying(p) {
    playing = p && doc.frames.length > 1; if (p && !playing) toast("Add a second frame to see an animation.");
    clearInterval(miniTimer); playIdx = doc.cur;
    if (playing) miniTimer = setInterval(() => { playIdx = (playIdx + 1) % doc.frames.length; miniDraw(); }, 1000 / fps);
    setIcon($("f-play"), playing ? "pause" : "play"); $("f-play").querySelector("span").textContent = playing ? "Stop" : "Play"; miniDraw();
  }
  $("f-play").onclick = () => setPlaying(!playing);
  $("f-speed").oninput = (e) => { fps = +e.target.value; $("f-fps").textContent = fps + "/s"; $("pv-speed").value = fps; if (playing) setPlaying(true); previewSpeed(); };

  // after anything big: bring every part of the screen up to date
  function syncAll(keepView) {
    renderFrames(); syncProps(); updateUndoUi(); renderColours();
    if (playing && doc.frames.length < 2) setPlaying(false);
    buildChecker(); miniDraw(); if (!keepView) fit(); else queue();
  }

  // ---- saving and opening ----------------------------------------------------------------------------------------------------------------------------
  const lib = () => store.get(LIB, []);
  function saveToLib(asNew) {
    const items = lib(); if (asNew) doc.id = newId();
    const p = pack(doc), i = items.findIndex((x) => x.id === doc.id);
    if (i >= 0) items[i] = p; else items.push(p);
    if (!store.set(LIB, items)) { toast("I could not save in this browser (the storage is full or blocked). Use Export or the download button in Open instead."); return false; }
    dirty = false; saved = true; updateInfo(); saveDraftSoon(); toast('Saved "' + doc.name + '" in this browser.'); return true;
  }
  // ---- the account: sprites are also kept on the website for people who are signed in (the same table as saved programs) ----
  const account = () => window.HLAccount && window.HLAccount.configured ? window.HLAccount : null;
  async function who() { const a = account(); if (!a) return null; try { const s = await a.session(); return s ? { a, s, c: await a.client() } : null; } catch (e) { return null; } }
  async function saveToCloud() {
    const w = await who(); if (!w) return null;
    const name = doc.name.slice(0, 60) || "sprite", code = JSON.stringify(pack(doc));
    const { error } = await w.c.from("saved_programs").upsert({ user_id: w.s.user.id, kind: "sprite", name, code }, { onConflict: "user_id,kind,name" });
    return error ? error.message : true;
  }
  async function saveBoth(asNew) {
    if (!saveToLib(asNew === true)) return;
    const w = await who();
    if (!w) { if (account()) toast('Saved in this browser. Sign in (menu, top right) to keep it in your account too.'); return; }
    const r = await saveToCloud();
    toast(r === true ? 'Saved "' + doc.name + '" in this browser and in your account.' : 'Saved in this browser, but not in your account: ' + r);
  }
  $("b-save").onclick = saveBoth;
  function load(d, msg) {
    doc = d; undoSt = []; redoSt = []; dirty = false; saved = false; offDirty = true; playing = false; clearInterval(miniTimer);
    setIcon($("f-play"), "play"); $("f-play").querySelector("span").textContent = "Play";
    syncAll(); if (msg) toast(msg); saveDraftSoon();
  }
  const sure = () => !dirty || confirm("The sprite you are drawing has changes that are not saved. Continue anyway?");
  function openDlg(d) { if (d.showModal) d.showModal(); else d.setAttribute("open", ""); }
  document.querySelectorAll("dialog [data-close]").forEach((b) => (b.onclick = () => b.closest("dialog").close()));
  document.querySelectorAll("dialog").forEach((d) => d.addEventListener("click", (e) => { if (e.target === d) d.close(); }));

  // new
  chips($("n-chips"), (n) => { $("n-w").value = n; $("n-h").value = n; nchips(); }, () => false);
  const nchips = () => { const w = +$("n-w").value, h = +$("n-h").value; [...$("n-chips").children].forEach((b, i) => b.classList.toggle("on", SIZES[i] === w && w === h)); };
  $("n-w").oninput = nchips; $("n-h").oninput = nchips; nchips();
  $("b-new").onclick = () => { if (!sure()) return; openDlg($("d-new")); $("n-name").select(); };
  $("f-new").onsubmit = (e) => {
    const w = Math.round(+$("n-w").value), h = Math.round(+$("n-h").value), ps = Math.round(+$("n-ps").value);
    if (!(w >= 1 && w <= 256 && h >= 1 && h <= 256 && ps >= 1 && ps <= 64)) { e.preventDefault(); toast("The size must be 1 to 256, and the pixel size 1 to 64."); return; }
    load({ id: newId(), name: $("n-name").value.trim() || "sprite", w, h, ps, frames: [new Int32Array(w * h).fill(T)], cur: 0 });
    $("d-new").close(); e.preventDefault();
  };
  // open
  function renderLib() {
    const items = lib(), box = $("o-list"); box.textContent = ""; $("o-none").hidden = items.length > 0;
    items.forEach((it) => {
      let d; try { d = unpack(it); } catch (e) { return; }
      const card = document.createElement("div"); card.className = "sp-card";
      const c = document.createElement("canvas"); toImage(d.frames[0], c, d.w, d.h); card.appendChild(c);
      const t = document.createElement("b"); t.textContent = d.name; t.title = d.name; card.appendChild(t);
      const s = document.createElement("small"); s.textContent = d.w + "×" + d.h + " · " + d.frames.length + (d.frames.length === 1 ? " frame" : " frames"); card.appendChild(s);
      const row = document.createElement("div"); row.className = "sp-actions";
      const mk = (label, fn, cls) => { const b = document.createElement("button"); b.type = "button"; b.className = "sp-btn small " + (cls || ""); b.textContent = label; b.onclick = fn; row.appendChild(b); };
      mk("Open", () => { if (!sure()) return; load(d); saved = true; updateInfo(); $("d-open").close(); }, "primary");
      mk("Copy", () => { const all = lib(); const n = pack(d); n.id = newId(); n.name = d.name + " copy"; all.push(n); store.set(LIB, all); renderLib(); });
      mk("Delete", () => { if (!confirm('Delete "' + d.name + '" from this browser? This cannot be undone.')) return; store.set(LIB, lib().filter((x) => x.id !== it.id)); renderLib(); });
      mk("⬇", () => download(S.sanitiseName(d.name) + ".sprite.json", JSON.stringify(pack(d)), "application/json"));
      card.appendChild(row); box.appendChild(card);
    });
  }
  async function renderCloud() {
    const box = $("o-cloud"), msg = $("o-acc-msg"), inb = $("o-acc-in"); box.textContent = "";
    if (!account()) { msg.textContent = "Accounts are not switched on here, so sprites stay in this browser."; inb.hidden = true; return; }
    msg.textContent = "Looking for your sprites..."; inb.hidden = true;
    const w = await who();
    if (!w) { msg.textContent = "Sign in to keep your sprites in your account, on any device."; inb.hidden = false; return; }
    const { data, error } = await w.c.from("saved_programs").select("id,name,code,updated_at").eq("kind", "sprite").order("updated_at", { ascending: false }).limit(60);
    if (error) { msg.textContent = "I could not load your account sprites (" + error.message + ")."; return; }
    msg.textContent = data.length ? "Saved in your account (Save keeps both places up to date; the name is what tells them apart)." : "Nothing in your account yet. Press Save while signed in.";
    data.forEach((row) => {
      let d; try { d = unpack(JSON.parse(row.code)); } catch (e) { return; }
      const card = document.createElement("div"); card.className = "sp-card";
      const c = document.createElement("canvas"); toImage(d.frames[0], c, d.w, d.h); card.appendChild(c);
      const t = document.createElement("b"); t.textContent = d.name; t.title = d.name; card.appendChild(t);
      const sm = document.createElement("small"); sm.textContent = d.w + "×" + d.h + " · " + d.frames.length + (d.frames.length === 1 ? " frame" : " frames"); card.appendChild(sm);
      const r = document.createElement("div"); r.className = "sp-actions";
      const mk = (label, fn, cls) => { const b = document.createElement("button"); b.type = "button"; b.className = "sp-btn small " + (cls || ""); b.textContent = label; b.onclick = fn; r.appendChild(b); };
      mk("Open", () => { if (!sure()) return; d.id = newId(); load(d); $("d-open").close(); toast('Opened "' + d.name + '" from your account.'); }, "primary");
      mk("Delete", async () => { if (!confirm('Delete "' + d.name + '" from your account? This cannot be undone.')) return; await w.c.from("saved_programs").delete().eq("id", row.id); renderCloud(); });
      card.appendChild(r); box.appendChild(card);
    });
  }
  $("o-signin").onclick = async () => { try { saveDraftSoon(); await account().signIn(); } catch (e) { toast("Could not start sign-in: " + (e.message || e)); } };
  $("b-open").onclick = () => { renderLib(); renderCloud(); openDlg($("d-open")); };
  // the Account page links here: sprites.html#cloud=ID
  (async function fromAccount() {
    const id = new URLSearchParams(location.hash.slice(1)).get("cloud"); if (!id) return;
    for (let i = 0; i < 40 && !account(); i++) await new Promise((r) => setTimeout(r, 100));
    const w = await who(); if (!w) { toast("Sign in to open your account sprites."); return; }
    const { data } = await w.c.from("saved_programs").select("code").eq("id", id).eq("kind", "sprite").maybeSingle();
    if (!data) { toast("I could not find that sprite."); return; }
    try { const d = unpack(JSON.parse(data.code)); d.id = newId(); load(d, 'Opened "' + d.name + '" from your account.'); saved = true; updateInfo(); } catch (e) { toast("That sprite could not be read."); }
  })();
  function readFile(file, cb) { const r = new FileReader(); r.onload = () => cb(String(r.result)); r.onerror = () => toast("I could not read that file."); r.readAsText(file); }
  $("o-file").onchange = (e) => {
    const f = e.target.files[0]; e.target.value = ""; if (!f) return;
    readFile(f, (text) => {
      if (text.trim()[0] === "{") { try { if (!sure()) return; load(unpack(JSON.parse(text))); $("d-open").close(); } catch (err) { toast(err.message || "That file is not a sprite from the editor."); } }
      else { $("d-open").close(); $("i-text").value = text; showImport(); checkImport(); }
    });
  };
  // save as (and Ctrl+Shift+S)
  $("f-saveas").onsubmit = (e) => { e.preventDefault(); const n = $("sa-name").value.trim(); if (!n) return; doc.name = n; $("sp-name").value = n; $("d-saveas").close(); saveBoth(true); };
  $("b-save").addEventListener("contextmenu", (e) => { e.preventDefault(); $("sa-name").value = doc.name; openDlg($("d-saveas")); });
  $("b-save").title = "Save in this browser (Ctrl+S). Right-click for Save As.";

  // ---- export, import ---------------------------------------------------------------------------------------------------------------------------------------------
  let lastCode = "";
  function showExport() {
    const g = S.generate(doc), code = $("e-code"), warn = $("e-warn");
    $("e-reduce").hidden = !(g.error && /colours/.test(g.error));
    if (g.error) { code.textContent = ""; warn.hidden = false; warn.className = "sp-warn bad"; warn.textContent = g.error; lastCode = ""; $("e-use").textContent = ""; }
    else {
      lastCode = g.code; code.textContent = g.code; $("e-use").textContent = "draw the sprite " + S.sanitiseName(doc.name) + " at 20, 30" + (doc.frames.length > 1 ? " frame 2" : "");
      warn.hidden = !g.warnings.length; warn.className = "sp-warn"; warn.textContent = g.warnings.join(" ");
    }
    ["e-copy", "e-dl", "e-play"].forEach((id) => ($(id).disabled = !lastCode));
    openDlg($("d-export"));
  }
  $("b-export").onclick = showExport;
  $("e-copy").onclick = () => {
    const done = () => { $("e-copy").lastChild.textContent = "Copied!"; setTimeout(() => ($("e-copy").lastChild.textContent = "Copy code"), 1600); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(lastCode).then(done, fallbackCopy); else fallbackCopy();
    function fallbackCopy() { const r = document.createRange(); r.selectNodeContents($("e-code")); const s = getSelection(); s.removeAllRanges(); s.addRange(r); try { document.execCommand("copy"); done(); } catch (e) { toast("Select the code and press Ctrl+C."); } }
  };
  $("e-dl").onclick = () => download(S.sanitiseName(doc.name) + ".hum", lastCode);
  $("e-play").onclick = () => {
    const prog = S.demoProgram(doc); if (!prog) return;
    const b64 = btoa(String.fromCharCode(...new TextEncoder().encode(prog)));
    window.open("playground.html#code=" + encodeURIComponent(b64), "_blank");
  };
  $("e-reduce").onclick = () => { $("d-export").close(); openDlg($("d-reduce")); };
  $("f-reduce").onsubmit = (e) => {
    e.preventDefault(); const n = Math.round(+$("r-n").value);
    if (!(n >= 1)) return;
    const before = S.coloursUsed(doc.frames).length;
    structural(() => { S.reduceColours(doc.frames, n); });
    $("d-reduce").close(); toast("Joined colours: " + before + " → " + S.coloursUsed(doc.frames).length + ". You can undo it."); showExport();
  };

  let imported = [];
  function showImport() { $("i-err").hidden = true; $("i-pick").hidden = true; openDlg($("d-import")); }
  $("b-import").onclick = showImport;
  $("i-file").onchange = (e) => { const f = e.target.files[0]; e.target.value = ""; if (f) readFile(f, (t) => { $("i-text").value = t; checkImport(); }); };
  function checkImport() {
    const r = S.parse($("i-text").value), err = $("i-err"), pick = $("i-pick");
    imported = r.sprites;
    err.hidden = !r.errors.length; err.className = "sp-warn bad"; err.textContent = ""; r.errors.forEach((m) => { const d = document.createElement("div"); d.textContent = m; err.appendChild(d); });
    pick.hidden = r.sprites.length < 2; pick.textContent = "";
    if (r.sprites.length > 1) {
      const h = document.createElement("div"); h.textContent = "I found " + r.sprites.length + " sprites. Which one do you want to edit?"; pick.appendChild(h);
      r.sprites.forEach((s, i) => { const l = document.createElement("label"), x = document.createElement("input"); x.type = "radio"; x.name = "ipick"; x.value = i; if (!i) x.checked = true; l.appendChild(x); l.appendChild(document.createTextNode(" " + s.name + " (" + s.w + "×" + s.h + ", " + s.frames.length + (s.frames.length === 1 ? " frame" : " frames") + ")")); pick.appendChild(l); });
    }
    return r;
  }
  $("i-go").onclick = () => {
    const r = checkImport();
    if (!r.sprites.length) return;
    let i = 0; const ch = document.querySelector('input[name="ipick"]:checked'); if (ch) i = +ch.value;
    const s = r.sprites[i];
    if (s.w > 256 || s.h > 256) { const e = $("i-err"); e.hidden = false; e.textContent = "This sprite is " + s.w + " × " + s.h + ". The editor handles up to 256 × 256."; return; }
    if (!sure()) return;
    load({ id: newId(), name: s.name, w: s.w, h: s.h, ps: s.ps, frames: s.frames, cur: 0 }, 'Imported "' + s.name + '". Edit it, then Export to get the code back.');
    $("d-import").close();
  };
  $("i-text").oninput = () => { if ($("i-text").value.trim()) checkImport(); else { $("i-err").hidden = true; $("i-pick").hidden = true; } };

  // ---- preview (how it looks in a game) --------------------------------------------------------------------------------------------------------------
  let pvTimer = 0, pvIdx = 0;
  function previewDraw() {
    const c = $("pv-canvas"); toImage(doc.frames[pvIdx % doc.frames.length], c, doc.w, doc.h);
    c.style.width = doc.w * doc.ps + "px"; c.style.height = doc.h * doc.ps + "px";
  }
  function previewSpeed() { clearInterval(pvTimer); if (!$("d-preview").open || doc.frames.length < 2) return; pvTimer = setInterval(() => { pvIdx++; previewDraw(); }, 1000 / (+$("pv-speed").value)); }
  $("b-preview").onclick = () => { pvIdx = 0; $("pv-speed").value = fps; previewDraw(); openDlg($("d-preview")); previewSpeed(); };
  $("d-preview").addEventListener("close", () => clearInterval(pvTimer));
  $("pv-speed").oninput = (e) => { fps = +e.target.value; $("f-speed").value = fps; $("f-fps").textContent = fps + "/s"; previewSpeed(); };
  document.querySelectorAll("[data-bg]").forEach((b) => (b.onclick = () => { $("pv-bg").className = "sp-pv-bg " + b.dataset.bg; document.querySelectorAll("[data-bg]").forEach((x) => x.classList.toggle("on", x === b)); }));

  // ---- the quick tour -------------------------------------------------------------------------------------------------------------------------------------------
  const STEPS = [
    ["1. Choose a colour", "Click a colour in your palette. You can also type a code like #ff8800 or a name like sky blue.", "#p-colour"],
    ["2. Draw", "Click or drag on the squares to colour them. Scroll to zoom in and out.", "#sp-wrap"],
    ["3. Erase", "The Erase tool makes pixels see-through again (the checkerboard). Press E, or click it.", '[data-tool="eraser"]'],
    ["4. Add a frame", "Frames make a sprite move. Press Add to make a second picture, change it a little, then press Play.", "#f-add"],
    ["5. Export", "When you are done, press Export to HumanLang, copy the code and paste it into your program.", "#b-export"],
  ];
  let step = -1, ringed = null;
  function tour(i) {
    if (ringed) ringed.classList.remove("sp-ring");
    if (i < 0 || i >= STEPS.length) { step = -1; $("sp-coach").hidden = true; ringed = null; store.set(TOUR, 1); return; }
    step = i; const [t, p, sel] = STEPS[i];
    $("co-n").textContent = "Quick tour · " + (i + 1) + " of " + STEPS.length; $("co-t").textContent = t; $("co-p").textContent = p;
    $("co-back").disabled = i === 0; $("co-next").textContent = i === STEPS.length - 1 ? "Done" : "Next";
    ringed = document.querySelector(sel); if (ringed) { ringed.classList.add("sp-ring"); }
    $("sp-coach").hidden = false;
  }
  $("co-next").onclick = () => tour(step + 1); $("co-back").onclick = () => tour(step - 1); $("co-skip").onclick = () => tour(-1);
  $("b-help").onclick = () => openDlg($("d-help"));
  $("h-tour").onclick = () => { $("d-help").close(); tour(0); };

  // ---- the keyboard ----------------------------------------------------------------------------------------------------------------------------------------------------------
  const KEYS = { p: "pencil", e: "eraser", f: "bucket", i: "picker", l: "line", r: "rect", c: "oval", h: "hand" };
  document.addEventListener("keydown", (e) => {
    const t = e.target, typing = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable);
    const mod = e.ctrlKey || e.metaKey, k = e.key.toLowerCase();
    if (document.querySelector("dialog[open]")) return;
    if (mod && k === "s") { e.preventDefault(); if (e.shiftKey) { $("sa-name").value = doc.name; openDlg($("d-saveas")); } else saveBoth(); return; }
    if (typing) return;
    if (mod && k === "z") { e.preventDefault(); if (e.shiftKey) redo(); else undo(); return; }
    if (mod && k === "y") { e.preventDefault(); redo(); return; }
    if (mod || e.altKey) return;
    if (KEYS[k]) { setTool(KEYS[k]); return; }
    if (k === " ") { if (t === cv || t === document.body) e.preventDefault(); spaceDown = true; wrap.classList.add("pan"); return; }
    if (k === "+" || k === "=") { stepZoom(1); return; }
    if (k === "-" || k === "_") { stepZoom(-1); return; }
    if (k === "0") { fit(); return; }
    if (k === ",") { selectFrame(doc.cur - 1); return; }
    if (k === ".") { selectFrame(doc.cur + 1); return; }
    if (k === "enter" && t.tagName !== "BUTTON") { setPlaying(!playing); return; }
  });
  document.addEventListener("keyup", (e) => { if (e.key === " ") { spaceDown = false; wrap.classList.toggle("pan", tool === "hand"); } });
  window.addEventListener("beforeunload", (e) => { if (dirty) { store.set(DRAFT, { doc: pack(doc), dirty, saved }); } });

  // ---- start -----------------------------------------------------------------------------------------------------------------------------------------------------------------
  if (window.ResizeObserver) new ResizeObserver(() => { layout(); }).observe(wrap); else window.addEventListener("resize", layout);
  const draft = store.get(DRAFT, null);
  if (draft && draft.doc) { try { doc = unpack(draft.doc); dirty = !!draft.dirty; saved = !!draft.saved; } catch (e) { /* start fresh */ } }
  setTool("pencil"); renderColours(); renderFrames(); syncProps(); updateUndoUi(); buildChecker(); layout(); fit(); miniDraw(); updateInfo();
  if (!store.get(TOUR, 0) && !(draft && draft.doc)) setTimeout(() => tour(0), 500);
  window.HLSpriteEditor = { get doc() { return doc; }, tool: () => tool, undoCount: () => undoSt.length };   // for the tests
})();

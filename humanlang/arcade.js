/* HumanLang arcade engine: draws a game on a <canvas>, collects keys and the mouse, plays sounds.
 *
 * It does not run HL itself. Whoever uses it hands in `step(input)`, a function that runs one frame of the game
 * (in Pyodide) and gives back {cmds, sounds, maps, over}. The Playground runs that in a worker; a saved game
 * runs it on the page. Everything else (drawing, input, timing, sound) is here, once, for both.
 */
(function (root) {
  "use strict";

  const KEYS = {
    ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down", " ": "space", Enter: "enter",
    Escape: "escape", Shift: "shift", Tab: "tab", Backspace: "backspace",
  };
  const FONTS = {
    normal: "system-ui, sans-serif", serif: "Georgia, serif", monospace: "ui-monospace, Menlo, Consolas, monospace",
    mono: "ui-monospace, Menlo, Consolas, monospace", rounded: "'Trebuchet MS', system-ui, sans-serif",
  };
  const CAPTURE = new Set(["left", "right", "up", "down", "space", "tab", "backspace"]);

  function keyName(e) {
    if (KEYS[e.key]) return KEYS[e.key];
    const k = (e.key || "").toLowerCase();
    return k.length === 1 ? k : null;
  }

  // ---- sound: tiny synthesizer, no audio files ----------------------------------------------------
  function makeSound() {
    let ctx = null;
    function ensure() {
      if (!ctx) {
        const AC = root.AudioContext || root.webkitAudioContext;
        if (!AC) return null;
        try { ctx = new AC(); } catch (e) { return null; }
      }
      if (ctx.state === "suspended") ctx.resume();
      return ctx;
    }
    function tone(c, t, type, f0, f1, dur, vol) {
      const o = c.createOscillator(), g = c.createGain();
      o.type = type;
      o.frequency.setValueAtTime(f0, t);
      if (f1 !== f0) o.frequency.exponentialRampToValueAtTime(Math.max(f1, 1), t + dur);
      g.gain.setValueAtTime(vol, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g); g.connect(c.destination);
      o.start(t); o.stop(t + dur + 0.02);
    }
    function noise(c, t, dur, vol) {
      const n = Math.max(1, Math.floor(c.sampleRate * dur)), buf = c.createBuffer(1, n, c.sampleRate), d = buf.getChannelData(0);
      for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n);
      const s = c.createBufferSource(), g = c.createGain();
      s.buffer = buf; g.gain.value = vol; s.connect(g); g.connect(c.destination); s.start(t);
    }
    const bank = {
      jump: (c, t) => tone(c, t, "square", 260, 620, 0.16, 0.12),
      coin: (c, t) => { tone(c, t, "square", 988, 988, 0.07, 0.1); tone(c, t + 0.07, "square", 1319, 1319, 0.16, 0.1); },
      hit: (c, t) => { noise(c, t, 0.12, 0.2); tone(c, t, "square", 160, 60, 0.12, 0.1); },
      shoot: (c, t) => tone(c, t, "sawtooth", 900, 120, 0.14, 0.09),
      explosion: (c, t) => { noise(c, t, 0.45, 0.28); tone(c, t, "sawtooth", 120, 30, 0.4, 0.1); },
      powerup: (c, t) => [392, 494, 587, 784].forEach((f, i) => tone(c, t + i * 0.07, "square", f, f, 0.1, 0.09)),
      win: (c, t) => [523, 659, 784, 1047].forEach((f, i) => tone(c, t + i * 0.11, "square", f, f, 0.16, 0.1)),
      lose: (c, t) => [392, 330, 262, 196].forEach((f, i) => tone(c, t + i * 0.14, "triangle", f, f, 0.2, 0.14)),
      beep: (c, t) => tone(c, t, "square", 660, 660, 0.12, 0.09),
      blip: (c, t) => tone(c, t, "square", 440, 440, 0.05, 0.07),
      step: (c, t) => tone(c, t, "triangle", 110, 90, 0.04, 0.12),
    };
    // ---- built-in background tunes: "C4" notes, one step each ("-" is a rest) ----
    const NOTE = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
    const freq = (n) => 440 * Math.pow(2, (NOTE[n[0]] + (n[1] === "#" ? 1 : 0) + 12 * (+n[n.length - 1] + 1) - 69) / 12);
    const TUNES = {
      adventure: { bpm: 150, lead: "E4 G4 A4 G4 E4 G4 C5 - D4 F4 A4 F4 D4 F4 B4 -", bass: "C3 - G3 - C3 - G3 - D3 - A3 - D3 - A3 -" },
      chill: { bpm: 90, lead: "C4 - E4 - G4 - E4 - A3 - C4 - E4 - C4 -", bass: "C3 - - - - - - - A2 - - - - - - -" },
      boss: { bpm: 190, lead: "A4 A4 E5 A4 D#5 A4 E5 A4 F5 F5 C5 F5 E5 D#5 E5 A4", bass: "A2 A2 A2 - A2 A2 E2 - F2 F2 F2 - F2 F2 E2 -" },
      doom: { bpm: 112, lead: "E4 - - D#4 E4 - B3 - C4 - - B3 C4 - F#4 -", bass: "E2 - E2 - E2 - B1 - C2 - C2 - C2 - F#1 -" },
      chase: { bpm: 180, lead: "A4 A4 C5 A4 E5 A4 C5 A4 G4 G4 B4 G4 D5 G4 B4 G4", bass: "A2 - A2 - A2 - A2 - G2 - G2 - G2 - G2 -" },
    };
    let timer = null, musicEl = null, uMuted = false;
    function stopMusic() {
      if (timer) { clearInterval(timer); timer = null; }
      if (musicEl) { musicEl.pause(); musicEl = null; }
    }
    function playTune(name) {
      const tune = TUNES[name]; if (!tune) return;
      const lead = tune.lead.split(" "), bass = tune.bass.split(" "), step = 30 / tune.bpm;
      let i = 0;
      const tick = () => {
        const c = ensure(); if (!c || uMuted || c.state !== "running") return;
        const t = c.currentTime + 0.02;
        if (lead[i % lead.length] !== "-") tone(c, t, "square", freq(lead[i % lead.length]), freq(lead[i % lead.length]), step * 0.9, 0.035);
        if (bass[i % bass.length] !== "-") tone(c, t, "triangle", freq(bass[i % bass.length]), freq(bass[i % bass.length]), step * 1.8, 0.07);
        i++;
      };
      tick(); timer = setInterval(tick, step * 1000);
    }
    return {
      unlock: ensure,
      play(name, files) {
        if (files && files[name]) {
          if (uMuted) return;
          const a = new Audio(files[name]); a.volume = 0.8; const p = a.play(); if (p && p.catch) p.catch(() => {});
          return;
        }
        const c = ensure();
        if (c && bank[name]) bank[name](c, c.currentTime);
      },
      music(name, files) {
        stopMusic();
        if (!name) return;
        if (files && files[name]) {
          musicEl = new Audio(files[name]); musicEl.loop = true; musicEl.volume = 0.5;
          if (!uMuted) { const p = musicEl.play(); if (p && p.catch) p.catch(() => {}); }
        } else playTune(name);
      },
      mute(m) { uMuted = m; if (musicEl) { if (m) musicEl.pause(); else { const p = musicEl.play(); if (p && p.catch) p.catch(() => {}); } } },
      stopMusic,
    };
  }

  // ---- sprites -------------------------------------------------------------------------------------
  function buildSprite(sp) {
    const per = sp.rows.length / sp.frames, cols = sp.rows[0].length, ps = sp.ps, frames = [];
    for (let f = 0; f < sp.frames; f++) {
      const cv = document.createElement("canvas");
      cv.width = cols * ps; cv.height = per * ps;
      const g = cv.getContext("2d");
      for (let r = 0; r < per; r++) {
        const row = sp.rows[f * per + r];
        for (let c = 0; c < cols; c++) {
          const colour = sp.legend[row[c]];
          if (colour) { g.fillStyle = colour; g.fillRect(c * ps, r * ps, ps, ps); }
        }
      }
      frames.push(cv);
    }
    return frames;
  }

  // ---- the game -------------------------------------------------------------------------------------
  function Arcade(canvas, info, step, opts) {
    opts = opts || {};
    const g = canvas.getContext("2d");
    const sound = makeSound();
    const sprites = {}, maps = {};
    for (const k in info.sprites) sprites[k] = buildSprite(info.sprites[k]);
    for (const k in info.maps) maps[k] = info.maps[k];
    const files = opts.assets || {}, pictures = {};  // your own files: name -> data (or web address)
    for (const k in files) if (/\.(png|jpe?g|gif|webp)$/i.test(k)) { const im = new Image(); im.src = files[k]; pictures[k] = im; }
    let lastMusic = null;
    canvas.width = info.w; canvas.height = info.h;
    g.imageSmoothingEnabled = false;

    const down = new Set();
    let pressed = [], clicked = false, mouse = [0, 0];
    let running = false, busy = false, last = 0, acc = 0, muted = !!opts.muted, frame = null, over = false;
    const STEP = 1000 / 60;

    function onKeyDown(e) {
      if (!running || e.ctrlKey || e.metaKey || e.altKey) return;
      const k = keyName(e);
      if (!k) return;
      if (CAPTURE.has(k)) e.preventDefault();
      sound.unlock();
      if (!down.has(k)) { down.add(k); pressed.push(k); }
    }
    function onKeyUp(e) { const k = keyName(e); if (k) down.delete(k); }
    function onBlur() { down.clear(); }
    function onMouse(e) {
      const r = canvas.getBoundingClientRect();
      mouse = [Math.round((e.clientX - r.left) * info.w / r.width), Math.round((e.clientY - r.top) * info.h / r.height)];
    }
    function onClick(e) { onMouse(e); clicked = true; sound.unlock(); canvas.focus(); }

    // a finger (or a held mouse button) dragged over the game counts as clicks where it is: that is how to steer by dragging
    let dragging = false;
    function onTouch(e) { const t = e.touches[0]; if (t) onClick({ clientX: t.clientX, clientY: t.clientY }); }
    function onTouchMove(e) { const t = e.touches[0]; if (t) onClick({ clientX: t.clientX, clientY: t.clientY }); }
    function onMouseDown(e) { dragging = true; onClick(e); }
    function onMouseDrag(e) { onMouse(e); if (dragging) clicked = true; }
    function onMouseUp() { dragging = false; }

    function shape(n) {
      const p = n.props || {}, k = n.kind;
      const fill = p.colour || (k === "text" ? "#ffffff" : "#000000");
      const border = p.border || ((p["border colour"]) ? 1 : 0);
      const paint = () => {
        if (fill !== "none") { g.fillStyle = fill; g.fill(); }
        if (border) { g.lineWidth = border; g.strokeStyle = p["border colour"] || "#000000"; g.stroke(); }
      };
      if (k === "circle") { g.beginPath(); g.arc(n.at[0], n.at[1], p.radius, 0, 6.2832); paint(); }
      else if (k === "oval") { g.beginPath(); g.ellipse(n.at[0], n.at[1], p.width / 2, p.height / 2, 0, 0, 6.2832); paint(); }
      else if (k === "rectangle" || k === "square") {
        const w = p.width, h = k === "square" ? w : p.height, r = p.rounded === true ? 10 : (p.rounded || 0);
        g.beginPath();
        if (r && g.roundRect) g.roundRect(n.at[0], n.at[1], w, h, r); else g.rect(n.at[0], n.at[1], w, h);
        paint();
      } else if (k === "triangle") {
        const [x, y] = n.at, w = p.width, h = p.height;
        g.beginPath(); g.moveTo(x + w / 2, y); g.lineTo(x + w, y + h); g.lineTo(x, y + h); g.closePath(); paint();
      } else if (k === "polygon") {
        g.beginPath(); n.points.forEach((pt, i) => (i ? g.lineTo(pt[0], pt[1]) : g.moveTo(pt[0], pt[1]))); g.closePath(); paint();
      } else if (k === "line") {
        g.beginPath(); g.moveTo(n.points[0][0], n.points[0][1]); g.lineTo(n.points[1][0], n.points[1][1]);
        g.lineWidth = p.thickness || 2; g.lineCap = "round"; g.strokeStyle = p.colour || "#000000"; g.stroke();
      } else if (k === "text") {
        const px = p.px || 18;
        g.font = `${p.italic ? "italic " : ""}${p.bold ? "bold " : ""}${px}px ${FONTS[p.font] || FONTS.monospace}`;
        g.textBaseline = "top"; g.fillStyle = fill;
        g.textAlign = p.align === "center" || p.align === "centre" || p.centered ? "center" : p.align === "right" ? "right" : "left";  // "at" is the middle / the right end
        g.fillText(n.text || "", n.at[0], n.at[1]);
        if (p.underlined) g.fillRect(n.at[0], n.at[1] + px * 1.1, g.measureText(n.text || "").width, Math.max(1, px / 12));
      } else if (k === "pixel art") {
        const ps = p["pixel size"] || 10;
        n.rows.forEach((row, r) => { for (let c = 0; c < row.length; c++) {
          const col = n.legend[row[c]];
          if (col) { g.fillStyle = col; g.fillRect(n.at[0] + c * ps, n.at[1] + r * ps, ps, ps); }
        } });
      }
    }

    function drawMap(name, ox, oy) {
      const m = maps[name]; if (!m) return;
      const t = m.tile, rows = m.rows;
      const c0 = Math.max(0, Math.floor(-ox / t)), c1 = Math.min(rows[0].length, Math.ceil((info.w - ox) / t));
      const r0 = Math.max(0, Math.floor(-oy / t)), r1 = Math.min(rows.length, Math.ceil((info.h - oy) / t));
      for (let r = r0; r < r1; r++) for (let c = c0; c < c1; c++) {
        const what = m.legend[rows[r][c]];
        if (!what) continue;
        const x = ox + c * t, y = oy + r * t;
        if (typeof what === "string") { g.fillStyle = what; g.fillRect(x, y, t, t); }
        else { const fr = sprites[what[1]]; if (fr) g.drawImage(fr[0], x, y, t, t); }
      }
    }

    function draw(f) {
      g.setTransform(1, 0, 0, 1, 0, 0);
      g.fillStyle = info.bg; g.fillRect(0, 0, info.w, info.h);
      for (const m in f.maps || {}) maps[m] = f.maps[m];
      for (const c of f.cmds) {
        const op = c[0];
        if (op === "sprite") {
          const fr = sprites[c[1]]; if (!fr) continue;
          const img = fr[c[4]] || fr[0], x = Math.round(c[2]), y = Math.round(c[3]);
          if (c[5]) { g.save(); g.translate(x + img.width, y); g.scale(-1, 1); g.drawImage(img, 0, 0); g.restore(); }
          else g.drawImage(img, x, y);
        } else if (op === "map") drawMap(c[1], Math.round(c[2]), Math.round(c[3]));
        else if (op === "shape") { g.save(); shape(c[1]); g.restore(); }
        else if (op === "picture") {
          const im = pictures[c[1]]; if (!im || !im.complete || !im.naturalWidth) continue;
          const x = Math.round(c[2]), y = Math.round(c[3]);
          if (c[4] != null) g.drawImage(im, x, y, c[4], c[5]); else g.drawImage(im, x, y);
        }
      }
    }

    async function tick(now) {
      if (!running) return;
      if (!last) last = now;
      acc = Math.min(acc + (now - last), STEP * 5);
      last = now;
      if (acc >= STEP && !busy) {
        acc -= STEP; busy = true;
        const input = { down: Array.from(down), pressed, clicked, mouse };
        pressed = []; clicked = false;
        try {
          frame = await step(input);
          draw(frame);
          if (!muted) for (const s of frame.sounds || []) sound.play(s, files);
          if (frame.music !== undefined && frame.music !== lastMusic) { lastMusic = frame.music; sound.music(frame.music, files); }
          if (frame.over) { over = true; running = false; if (opts.onOver) opts.onOver(); }
        } catch (err) {
          running = false;
          if (opts.onError) opts.onError(err && err.message ? err.message : String(err));
        }
        busy = false;
      }
      if (running) root.requestAnimationFrame(tick);
    }

    // ---- touch controls: on a phone or tablet, buttons on the screen press the keys the game uses ----
    let pad = null;
    function wantsTouch() {
      if (opts.touch === false) return false;
      if (opts.touch === true) return true;
      return !!(root.matchMedia && root.matchMedia("(pointer: coarse)").matches);
    }
    function makePad() {
      const doc = canvas.ownerDocument, used = info.keys && info.keys.length ? info.keys : ["left", "right", "up", "space"];
      const want = (k) => used.indexOf(k) >= 0;
      const LABEL = { left: "\u25C0", right: "\u25B6", up: "\u25B2", down: "\u25BC", space: "A", enter: "B" };
      const el = doc.createElement("div");
      el.className = "hl-touchpad";
      el.style.cssText = "position:fixed;left:0;right:0;bottom:0;display:flex;justify-content:space-between;align-items:flex-end;" +
        "padding:10px 14px;pointer-events:none;z-index:50;touch-action:none;user-select:none;-webkit-user-select:none";
      const left = doc.createElement("div"), right = doc.createElement("div");
      left.style.cssText = right.style.cssText = "display:flex;gap:10px;align-items:flex-end;pointer-events:none";
      const count = ["left", "right", "down", "up", "enter", "space"].filter(want).length;
      const size = Math.max(44, Math.min(64, Math.floor(((root.innerWidth || 360) - 28 - 10 * (count - 1)) / Math.max(1, count))));
      function btn(k, side) {
        const b = doc.createElement("button");
        b.type = "button"; b.textContent = LABEL[k]; b.setAttribute("aria-label", k + " button");
        b.style.cssText = "pointer-events:auto;touch-action:none;width:" + size + "px;height:" + size + "px;border-radius:" + size / 2 + "px;border:2px solid #ffffff88;" +
          "background:#00000066;color:#fff;font:bold " + Math.round(size / 3) + "px system-ui,sans-serif;padding:0";
        const press = (e) => { e.preventDefault(); sound.unlock(); if (!down.has(k)) { down.add(k); pressed.push(k); } b.style.background = "#ffffff55"; };
        const release = (e) => { e.preventDefault(); down.delete(k); b.style.background = "#00000066"; };
        b.addEventListener("pointerdown", press);
        ["pointerup", "pointercancel", "pointerleave"].forEach((ev) => b.addEventListener(ev, release));
        b.addEventListener("contextmenu", (e) => e.preventDefault());
        side.appendChild(b);
      }
      ["left", "right", "down"].filter(want).forEach((k) => btn(k, left));
      ["up", "enter", "space"].filter(want).forEach((k) => btn(k, right));
      el.appendChild(left); el.appendChild(right);
      doc.body.appendChild(el);
      return el;
    }

    const api = {
      start() {
        if (running) return;
        if (!pad && wantsTouch()) pad = makePad();
        running = true; last = 0; acc = STEP;
        root.addEventListener("keydown", onKeyDown);
        root.addEventListener("keyup", onKeyUp);
        root.addEventListener("blur", onBlur);
        canvas.addEventListener("mousemove", onMouseDrag);
        canvas.addEventListener("mousedown", onMouseDown);
        root.addEventListener("mouseup", onMouseUp);
        canvas.addEventListener("touchmove", onTouchMove, { passive: true });
        canvas.addEventListener("touchstart", onTouch, { passive: true });
        root.requestAnimationFrame(tick);
      },
      stop() {
        running = false;
        if (pad) { pad.remove(); pad = null; }
        sound.stopMusic();
        root.removeEventListener("keydown", onKeyDown);
        root.removeEventListener("keyup", onKeyUp);
        root.removeEventListener("blur", onBlur);
        canvas.removeEventListener("mousemove", onMouseDrag);
        canvas.removeEventListener("mousedown", onMouseDown);
        root.removeEventListener("mouseup", onMouseUp);
        canvas.removeEventListener("touchmove", onTouchMove);
        canvas.removeEventListener("touchstart", onTouch);
      },
      setMuted(m) { muted = !!m; sound.mute(muted); },
      get over() { return over; },
    };
    return api;
  }

  root.Arcade = Arcade;
})(typeof window !== "undefined" ? window : self);

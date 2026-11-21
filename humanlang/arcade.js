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
    let videoOn = null;  // while a video plays over the game: { box, video, finish }; the game waits until it ends
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
      if (videoOn) { if (k === "escape" || k === "space" || k === "enter") { e.preventDefault(); videoOn.finish(); } return; }
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
    function onClick(e) { if (videoOn) return; onMouse(e); clicked = true; sound.unlock(); canvas.focus(); }

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

    // ---- play the video "x.mp4": shown over the game, the game waits; click, tap, Escape, Space or Enter skips it ----
    function playVideo(name, done) {
      const src = files[name], doc = canvas.ownerDocument;
      if (!src) { done(); return; }
      const box = doc.createElement("div"), v = doc.createElement("video");
      box.className = "hl-video";
      box.style.cssText = "position:fixed;z-index:60;background:#000;display:flex;align-items:center;justify-content:center;cursor:pointer;overflow:hidden;touch-action:manipulation";
      v.src = src; v.playsInline = true; v.setAttribute("playsinline", ""); v.preload = "auto"; v.muted = muted;
      v.style.cssText = "width:100%;height:100%;object-fit:contain;display:block";
      const skip = doc.createElement("button");
      skip.type = "button"; skip.textContent = "Skip \u25B6"; skip.setAttribute("aria-label", "Skip the video");
      skip.style.cssText = "position:absolute;right:8px;bottom:8px;font:600 13px system-ui,sans-serif;color:#fff;background:#000a;border:1px solid #fff6;border-radius:6px;padding:4px 10px;cursor:pointer";
      const tap = doc.createElement("button");
      tap.type = "button"; tap.textContent = "\u25B6  Tap to play"; tap.hidden = true;
      tap.style.cssText = "position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font:700 20px system-ui,sans-serif;color:#fff;background:#1b6fe8;border:0;border-radius:30px;padding:12px 26px;cursor:pointer";
      box.append(v, skip, tap); doc.body.appendChild(box);
      let ended = false, raf = 0;
      const place = () => {   // sits exactly over the game screen, wherever the page puts it
        const r = canvas.getBoundingClientRect();
        box.style.left = r.left + "px"; box.style.top = r.top + "px"; box.style.width = r.width + "px"; box.style.height = r.height + "px";
        raf = root.requestAnimationFrame(place);
      };
      place();
      const finish = (quiet) => {
        if (ended) return; ended = true; videoOn = null;
        root.cancelAnimationFrame(raf); try { v.pause(); } catch (e) { /* gone already */ }
        v.removeAttribute("src"); try { v.load(); } catch (e) { /* ignore */ }
        box.remove();
        down.clear(); pressed = []; clicked = false;    // what was pressed to skip the video must not reach the game
        if (quiet === true) return;
        canvas.focus(); done();
      };
      videoOn = { box, video: v, finish };
      const go = () => { const p = v.play(); if (p && p.catch) p.catch(() => { tap.hidden = false; }); };  // a page nobody has clicked yet may not play sound: ask for a tap
      v.addEventListener("ended", () => finish());
      v.addEventListener("error", () => finish());
      skip.addEventListener("click", (e) => { e.stopPropagation(); sound.unlock(); finish(); });
      tap.addEventListener("click", (e) => { e.stopPropagation(); tap.hidden = true; v.muted = muted; go(); });
      box.addEventListener("click", () => { if (tap.hidden) { sound.unlock(); finish(); } });
      box.addEventListener("touchstart", (e) => { e.stopPropagation(); }, { passive: true });
      sound.stopMusic(); lastMusic = null;
      go();
    }

    async function tick(now) {
      if (!running) return;
      if (!last) last = now;
      acc = Math.min(acc + (now - last), STEP * 5);
      last = now;
      if (videoOn) { last = now; acc = 0; }
      if (acc >= STEP && !busy && !videoOn) {
        acc -= STEP; busy = true;
        const input = { down: Array.from(down), pressed, clicked, mouse };
        pressed = []; clicked = false;
        try {
          frame = await step(input);
          draw(frame);
          const f = frame, after = () => {
            if (!muted) for (const s of f.sounds || []) sound.play(s, files);
            if (f.music !== undefined && f.music !== lastMusic) { lastMusic = f.music; sound.music(f.music, files); }
            if (f.over) { over = true; running = false; if (opts.onOver) opts.onOver(); }
          };
          if (f.video) playVideo(f.video, after); else after();
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
    function padCss(doc) {
      if (doc.getElementById("hl-pad-css")) return;
      const st = doc.createElement("style");
      st.id = "hl-pad-css";
      // Thumbs rest at the bottom corners: the left thumb gets the way to run (a cross when up/down matter), the right thumb gets
      // the action buttons on a small arc, biggest one nearest the corner. Sizes shrink with the screen width (--u).
      st.textContent =
        ".hl-touchpad{--u:1;position:fixed;left:0;top:0;width:var(--vw,100vw);height:var(--vh,100vh);pointer-events:none;z-index:60;touch-action:none;user-select:none;-webkit-user-select:none}" +
        ".hl-rot .hl-touchpad{transform-origin:top left;transform:translateX(var(--vw,100vw)) rotate(90deg);width:var(--vh,100vh);height:var(--vw,100vw)}" +
        ".hl-pad{position:absolute;bottom:calc(16px + env(safe-area-inset-bottom,0px));pointer-events:none}" +
        ".hl-pad-l{left:calc(16px + env(safe-area-inset-left,0px))}.hl-pad-r{right:calc(16px + env(safe-area-inset-right,0px))}" +
        ".hl-b{position:absolute;box-sizing:border-box;border-radius:50%;border:2px solid rgba(255,255,255,.6);background:rgba(10,14,30,.5);color:#fff;" +
        "font:700 calc(22px * var(--u)) system-ui,sans-serif;padding:0;pointer-events:auto;touch-action:none;display:flex;align-items:center;justify-content:center;-webkit-tap-highlight-color:transparent}" +
        ".hl-b.on{background:rgba(255,255,255,.45)}";
      doc.head.appendChild(st);
    }
    function padScale() { return Math.max(0.72, Math.min(1, ((root.innerWidth || 400)) / 440)); }
    function makePad() {
      const doc = canvas.ownerDocument, used = info.keys && info.keys.length ? info.keys : ["left", "right", "up", "space"];
      const want = (k) => used.indexOf(k) >= 0;
      const LABEL = { left: "◀", right: "▶", up: "▲", down: "▼", space: "A", enter: "B" };
      padCss(doc);
      const el = doc.createElement("div");
      el.className = "hl-touchpad";
      el.style.setProperty("--u", String(padScale()));
      const held = new Map();                       // key -> how many fingers hold it
      const hold = (k) => { const n = held.get(k) || 0; held.set(k, n + 1); if (!n) { down.add(k); pressed.push(k); if (root.navigator && root.navigator.vibrate) root.navigator.vibrate(8); } };
      const drop = (k) => { const n = (held.get(k) || 1) - 1; if (n <= 0) { held.delete(k); down.delete(k); } else held.set(k, n); };
      function cluster(cls, w, h) {
        const c = doc.createElement("div");
        c.className = "hl-pad " + cls;
        c.style.width = "calc(" + w + "px * var(--u))"; c.style.height = "calc(" + h + "px * var(--u))";
        const btns = [], fingers = new Map();       // pointer id -> key it holds now
        const keyAt = (x, y) => {
          for (const b of btns) { const r = b.getBoundingClientRect(); if (x >= r.left - 8 && x <= r.right + 8 && y >= r.top - 8 && y <= r.bottom + 8) return b.dataset.k; }
          return null;
        };
        const move = (id, k) => { const old = fingers.get(id); if (old === k) return; if (old) { drop(old); const ob = btns.find((b) => b.dataset.k === old); if (ob && !held.has(old)) ob.classList.remove("on"); } if (k) { hold(k); fingers.set(id, k); btns.find((b) => b.dataset.k === k).classList.add("on"); } else fingers.delete(id); };
        c.add = (k, size, x, y, fromBottom, fromRight) => {
          const b = doc.createElement("button");
          b.type = "button"; b.className = "hl-b"; b.textContent = LABEL[k]; b.dataset.k = k; b.setAttribute("aria-label", k + " button");
          b.style.width = b.style.height = "calc(" + size + "px * var(--u))";
          b.style[fromRight ? "right" : "left"] = "calc(" + x + "px * var(--u))"; b.style.bottom = "calc(" + y + "px * var(--u))";
          b.addEventListener("pointerdown", (e) => { e.preventDefault(); sound.unlock(); try { b.setPointerCapture(e.pointerId); } catch (x_) { /* fine */ } move(e.pointerId, k); });
          b.addEventListener("pointermove", (e) => { if (fingers.has(e.pointerId)) { e.preventDefault(); move(e.pointerId, keyAt(e.clientX, e.clientY)); } });
          const up = (e) => { e.preventDefault(); move(e.pointerId, null); };
          b.addEventListener("pointerup", up); b.addEventListener("pointercancel", up);
          b.addEventListener("contextmenu", (e) => e.preventDefault());
          btns.push(b); c.appendChild(b);
        };
        el.appendChild(c);
        return c;
      }
      // left thumb: a cross when up or down are used (it rests in the middle), else just the two ways to run, big
      if (want("left") || want("right") || want("up") || want("down")) {
        if (want("up") || want("down")) {
          const L = cluster("hl-pad-l", 186, 186);
          if (want("up")) L.add("up", 60, 63, 126);
          if (want("left")) L.add("left", 60, 0, 63);
          if (want("right")) L.add("right", 60, 126, 63);
          if (want("down")) L.add("down", 60, 63, 0);
        } else {
          const L = cluster("hl-pad-l", 156, 76);
          if (want("left")) L.add("left", 72, 0, 0);
          if (want("right")) L.add("right", 72, 84, 0);
        }
      }
      // right thumb: the main action nearest the corner and the big one, the second action up and to the left on the thumb's arc
      const main = want("space") ? "space" : want("enter") ? "enter" : null;
      if (main) {
        const R = cluster("hl-pad-r", 178, 130);
        R.add(main, 88, 0, 0, true, true);
        if (main === "space" && want("enter")) R.add("enter", 68, 98, 52, true, true);
      }
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
        if (videoOn) videoOn.finish(true);
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
      setMuted(m) { muted = !!m; sound.mute(muted); if (videoOn) videoOn.video.muted = muted; },
      get over() { return over; },
    };
    return api;
  }

  root.Arcade = Arcade;
})(typeof window !== "undefined" ? window : self);

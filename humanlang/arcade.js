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
    return {
      unlock: ensure,
      play(name) {
        const c = ensure();
        if (c && bank[name]) bank[name](c, c.currentTime);
      },
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
        g.textBaseline = "top"; g.fillStyle = fill; g.fillText(n.text || "", n.at[0], n.at[1]);
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
          if (!muted) for (const s of frame.sounds || []) sound.play(s);
          if (frame.over) { over = true; running = false; if (opts.onOver) opts.onOver(); }
        } catch (err) {
          running = false;
          if (opts.onError) opts.onError(err && err.message ? err.message : String(err));
        }
        busy = false;
      }
      if (running) root.requestAnimationFrame(tick);
    }

    const api = {
      start() {
        if (running) return;
        running = true; last = 0; acc = STEP;
        root.addEventListener("keydown", onKeyDown);
        root.addEventListener("keyup", onKeyUp);
        root.addEventListener("blur", onBlur);
        canvas.addEventListener("mousemove", onMouse);
        canvas.addEventListener("mousedown", onClick);
        root.requestAnimationFrame(tick);
      },
      stop() {
        running = false;
        root.removeEventListener("keydown", onKeyDown);
        root.removeEventListener("keyup", onKeyUp);
        root.removeEventListener("blur", onBlur);
        canvas.removeEventListener("mousemove", onMouse);
        canvas.removeEventListener("mousedown", onClick);
      },
      setMuted(m) { muted = !!m; },
      get over() { return over; },
    };
    return api;
  }

  root.Arcade = Arcade;
})(typeof window !== "undefined" ? window : self);

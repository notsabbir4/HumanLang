(function () {
  const $ = (id) => document.getElementById(id);
  const games = window.HL_GAMES;
  const lobby = $("lobby"), stage = $("stage"), screen = $("screen"), status = $("gstatus");
  const restartBtn = $("restart"), backBtn = $("back"), title = $("gtitle"), tags = $("gtags");
  let worker = null, ready = false, running = false, current = null, answers = [], waiting = false;

  // ---- the lobby: one card per game ----
  // games are grouped by the HumanLang version they were made with, newest first (an old game stays as it was made)
  const vkey = (v) => String(v || "0").split(".").map((n) => +n || 0);
  const versions = [...new Set(games.map((g) => g.version || "older"))].sort((a, b) => {
    const x = vkey(a), y = vkey(b); for (let i = 0; i < 4; i++) { if ((y[i] || 0) !== (x[i] || 0)) return (y[i] || 0) - (x[i] || 0); } return 0; });
  const grids = {};
  for (const v of versions) {
    const sec = document.createElement("section"); sec.className = "ver-group";
    const h = document.createElement("h2"); h.className = "ver"; h.textContent = v === "older" ? "Older games" : "Made with HumanLang " + v;
    const grid = document.createElement("div"); grid.className = "game-grid";
    sec.append(h, grid); $("grid").appendChild(sec); grids[v] = grid;
  }
  for (const g of games) {
    const a = document.createElement("a");
    a.className = "game-card"; a.href = "#" + g.id;
    const h = document.createElement("h2"); h.textContent = g.title;
    const sub = document.createElement("span"); sub.className = "sub"; sub.textContent = g.subtitle || "";
    const p = document.createElement("p"); p.textContent = g.tagline || "";
    const t = document.createElement("div"); t.className = "tags";
    for (const x of g.tags || []) { const s = document.createElement("span"); s.textContent = x; t.appendChild(s); }
    const go = document.createElement("span"); go.className = "btn"; go.textContent = "Play";
    if (g.image) {
      const img = document.createElement("img");
      img.className = "thumb"; img.src = g.image; img.alt = ""; img.loading = "lazy";
      a.appendChild(img);
    }
    a.append(h, sub, p, t, go);
    const wrap = document.createElement("div"); wrap.className = "game-wrap";
    const ins = document.createElement("a"); ins.className = "inspect-link"; ins.href = "#" + g.id + "/inspect"; ins.textContent = "Inspect";
    ins.title = "See the code and how it works";
    wrap.append(a, ins);
    grids[g.version || "older"].appendChild(wrap);
  }

  function setStatus(text) { status.textContent = text; }

  // ---- the engine (the same one the playground uses) ----
  function startWorker() {
    ready = false; running = false;
    setStatus("Loading HumanLang... (the first time takes a few seconds)");
    worker = new Worker("worker.js");
    worker.onmessage = (e) => {
      const m = e.data;
      if (m.type === "ready") { ready = true; setStatus(""); if (current) play(); }
      else if (m.type === "error") setStatus("Could not load the game engine: " + m.message);
      else if (m.type === "gameinfo") arcadeInfo(m);
      else if (m.type === "gameframe") arcadeFrame(m);
      else if (m.type === "result") {
        running = false;
        if (m.need !== undefined) ask(m.out || "", m.need);
        else finish(m);
      }
    };
  }

  // ---- typing animation: text arrives letter by letter, so there is time to read it ----
  const speedBox = $("speed"), skipBtn = $("skip");
  const SPEEDS = { slow: [38, 420], normal: [22, 260], fast: [9, 90], instant: [0, 0] };  // [ms per letter, ms after each line]
  const calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let speed = calm ? "instant" : "normal";
  try { const saved = localStorage.getItem("hl-typing-speed"); if (saved && SPEEDS[saved]) speed = saved; } catch (e) {}
  speedBox.value = speed;
  speedBox.onchange = () => {
    speed = speedBox.value;
    try { localStorage.setItem("hl-typing-speed", speed); } catch (e) {}
    if (typing) finishTyping();
  };
  let typed = "", textNode = null, cursor = null, typing = null;  // typing = {rest, i, timer, done}

  function bottom() { screen.scrollTop = screen.scrollHeight; }
  function reset(text) {
    cancelTyping();
    screen.textContent = "";
    textNode = document.createTextNode(text);
    screen.appendChild(textNode);
    typed = text; screen.className = "";
  }
  function shown(text) { reset(text); }
  function cancelTyping() {
    if (typing) { clearTimeout(typing.timer); typing = null; }
    if (cursor) { cursor.remove(); cursor = null; }
    skipBtn.hidden = true;
  }
  function finishTyping() {
    if (!typing) return;
    const t = typing; clearTimeout(t.timer); typing = null;
    textNode.appendData(t.rest.slice(t.i)); typed += t.rest.slice(t.i);
    if (cursor) { cursor.remove(); cursor = null; }
    skipBtn.hidden = true; bottom();
    t.done();
  }
  // show `target` on the screen: what is already there stays, only the new part is typed
  function type(target, done) {
    if (!target.startsWith(typed)) reset("");           // should not happen; start the page over
    const rest = target.slice(typed.length);
    const [per, pause] = SPEEDS[speed];
    if (!rest || !per) { textNode.appendData(rest); typed = target; bottom(); done(); return; }
    cursor = document.createElement("span"); cursor.className = "cursor"; cursor.textContent = "\u258C";
    screen.appendChild(cursor);
    skipBtn.hidden = false; setStatus("Typing...  click the screen or press Space to skip ahead.");
    typing = { rest, i: 0, timer: 0, done };
    const step = () => {
      if (!typing) return;
      const ch = rest[typing.i++];
      textNode.appendData(ch); typed += ch; bottom();
      if (typing.i >= rest.length) { const d = typing.done; typing = null; cursor.remove(); cursor = null; skipBtn.hidden = true; d(); return; }
      let wait = per;
      if (ch === "\n") wait += rest[typing.i] === "\n" ? pause * 0.4 : pause;
      typing.timer = setTimeout(step, wait);
    };
    step();
  }
  screen.addEventListener("click", () => finishTyping());
  skipBtn.onclick = () => finishTyping();
  document.addEventListener("keydown", (e) => {
    if (typing && (e.key === " " || e.key === "Enter" || e.key === "Escape") && !(e.target && e.target.tagName === "INPUT")) {
      e.preventDefault(); finishTyping();
    }
  });

  function ask(before, question) {
    waiting = true; setStatus("...");
    type(before + question, () => askBox(before, question));
  }

  function askBox(before, question) {
    setStatus("Type your answer and press Enter.");
    const box = document.createElement("input");
    box.type = "text"; box.className = "answer"; box.autocomplete = "off"; box.spellcheck = false;
    box.setAttribute("aria-label", question.trim() || "Your answer");
    screen.appendChild(box); box.focus(); bottom();
    box.addEventListener("keydown", (e) => {
      if (e.key !== "Enter") return;
      e.preventDefault();
      answers.push(box.value);
      waiting = false;
      shown(before + question + box.value + "\n");  // the story so far stays on screen
      run();
    });
  }

  function finish(m) {
    let text = m.out || "";
    if (m.err) text += (text && !text.endsWith("\n") ? "\n" : "") + "\n" + m.err;
    setStatus("...");
    type(text, () => {
      screen.className = m.err ? "error" : "";
      setStatus(m.err ? "The game hit a problem. Press Play again to restart." : "The end. Press Play again to start over.");
      restartBtn.textContent = "Play again";
      bottom();
    });
  }

  // ---- arcade games: drawn on a canvas, one frame at a time (the engine is shared with the Playground) ----
  const abox = $("arcade-box"), acanvas = $("arcade-screen");
  let arcade = null, frameWaiting = null, starting = false, info = null;
  function stopArcade() { if (arcade) { arcade.stop(); arcade = null; } frameWaiting = null; starting = false; leaveLand(); }

  // ---- phones: the game always fits the screen, and "Landscape" fills it sideways (a phone is wider than tall that way) ----
  const phone = !!(window.matchMedia && matchMedia("(pointer: coarse)").matches);
  const docEl = document.documentElement;
  let land = false, forced = false, home = null;
  const landBtn = document.createElement("button"), exitBtn = document.createElement("button");
  landBtn.type = exitBtn.type = "button"; landBtn.id = "land-btn"; exitBtn.id = "land-exit";
  landBtn.textContent = "\u26F6  Play in landscape"; exitBtn.textContent = "\u2715"; exitBtn.setAttribute("aria-label", "Leave landscape");
  landBtn.hidden = exitBtn.hidden = true;
  abox.insertBefore(landBtn, abox.firstChild); abox.appendChild(exitBtn);
  function sizeCanvas() {
    if (!info) return;
    if (!phone) {                                  // computers: exactly as before
      const k = Math.max(1, Math.floor(Math.min(stage.clientWidth || 640, 900) / info.w));
      acanvas.style.width = info.w * k + "px"; acanvas.style.height = info.h * k + "px"; return;
    }
    const portrait = innerHeight > innerWidth;
    let W, H;
    if (land) { W = forced && portrait ? innerHeight : innerWidth; H = forced && portrait ? innerWidth : innerHeight; }
    else { W = Math.max(200, Math.min(stage.clientWidth || innerWidth, innerWidth) - 24); H = 1e5; }
    const k = Math.min(W / info.w, H / info.h);
    acanvas.style.width = Math.floor(info.w * k) + "px"; acanvas.style.height = Math.floor(info.h * k) + "px";
  }
  function layout() {
    const portrait = innerHeight > innerWidth;
    docEl.style.setProperty("--vw", innerWidth + "px"); docEl.style.setProperty("--vh", innerHeight + "px");
    if (phone && arcade && !land && !portrait && innerHeight < 560) enterLand(false);        // phone turned sideways: fill the screen
    if (land && !forced && portrait) leaveLand();                                              // turned back up: normal page again
    abox.classList.toggle("rot", land && forced && portrait);
    document.body.classList.toggle("hl-rot", land && forced && portrait);
    sizeCanvas();
  }
  function enterLand(user) {
    land = true; forced = !!user || forced;
    if (abox.parentNode !== document.body) { home = { p: abox.parentNode, n: abox.nextSibling }; document.body.appendChild(abox); }   // out of the page's layout: the game owns the whole screen
    abox.classList.add("land"); document.body.classList.add("hl-landing");
    exitBtn.hidden = false; landBtn.hidden = true;
    if (user) {
      // Android Chrome: full screen + lock to landscape. Where that is not possible (iPhone, or the lock is refused), the page turns the game sideways itself.
      (async () => {
        try { await (abox.requestFullscreen || abox.webkitRequestFullscreen).call(abox); } catch (e) { return; }
        const giveUp = async () => { try { await document.exitFullscreen(); } catch (e2) { /* fine */ } layout(); };
        try { await screen_orientation().lock("landscape"); setTimeout(() => { if (land && innerHeight > innerWidth) giveUp(); }, 700); }
        catch (e) { giveUp(); }
      })();
    }
    layout();
  }
  function screen_orientation() { return window.screen && window.screen.orientation; }
  function leaveLand() {
    if (!land) return;
    land = false; forced = false;
    abox.classList.remove("land", "rot"); document.body.classList.remove("hl-landing", "hl-rot");
    if (home) { home.p.insertBefore(abox, home.n); home = null; }
    exitBtn.hidden = true; landBtn.hidden = !phone || abox.hidden;
    try { if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen(); } catch (e) { /* fine */ }
    try { const o = screen_orientation(); if (o && o.unlock) o.unlock(); } catch (e) { /* fine */ }
    sizeCanvas();
  }
  landBtn.onclick = () => enterLand(true);
  exitBtn.onclick = () => leaveLand();
  addEventListener("resize", layout); addEventListener("orientationchange", () => setTimeout(layout, 120));
  document.addEventListener("fullscreenchange", () => setTimeout(layout, 100));
  function startArcade() {
    stopArcade();
    if (!ready) { setStatus("Loading HumanLang... (the first time takes a few seconds)"); return; }
    starting = true; setStatus("Starting the game...");
    const kinds = {}; for (const n in (current.files || {})) kinds[n] = current.files[n].kind;
    worker.postMessage({ type: "gamestart", code: current.code, assets: kinds });
  }
  function arcadeInfo(m) {
    starting = false;
    if (!current || current.kind !== "arcade") return;
    if (m.error) { setStatus(""); abox.hidden = true; screen.hidden = false; screen.className = "error"; screen.textContent = m.error; return; }
    info = m.info;
    sizeCanvas();
    arcade = Arcade(acanvas, m.info, (input) => new Promise((resolve, reject) => {
      frameWaiting = { resolve, reject };
      worker.postMessage({ type: "gameframe", input });
    }), {
      assets: Object.fromEntries(Object.entries(current.files || {}).map(([n, f]) => [n, f.url])),
      onError: (msg) => { setStatus("The game stopped with a problem."); screen.hidden = false; screen.className = "error"; screen.textContent = msg; },
      onOver: () => setStatus("Game over. Press Restart to play again."),
    });
    setStatus(phone ? "Use the buttons on the screen." : "Click the game, then use the keys."); if (!phone) acanvas.focus(); arcade.start();
    landBtn.hidden = !phone || land; layout();
    if (phone && !land) setTimeout(() => window.scrollTo(0, Math.max(0, abox.getBoundingClientRect().top + scrollY - 76)), 50);   // the game sits at the top, the thumbs' buttons at the bottom
  }
  function arcadeFrame(m) {
    const w = frameWaiting; frameWaiting = null; if (!w) return;
    const f = JSON.parse(m.json);
    if (f.error) w.reject(new Error(f.error)); else w.resolve(f);
  }

  function run() {
    if (!ready || running || !current) return;
    running = true; setStatus("...");
    worker.postMessage({ type: "run", code: current.code, inputs: answers, seed: 1 });
  }

  function play() {
    if (current && current.kind === "arcade") { startArcade(); return; }
    answers = []; waiting = false; shown(""); restartBtn.textContent = "Restart"; setStatus("");
    if (!ready) { setStatus("Loading HumanLang... (the first time takes a few seconds)"); return; }
    if (running) { worker.terminate(); startWorker(); return; }  // answered mid-run: start clean
    run();
  }

  // ---- showing a game ----
  const inspectBtn = $("inspect-btn"), inspectBox = $("inspect"), inspectBody = $("inspect-body");
  function setInspect(on) {
    inspectBox.hidden = !on; inspectBtn.setAttribute("aria-expanded", String(on));
    inspectBtn.textContent = on ? "Hide code" : "Inspect";
  }
  function fillInspect(g) {
    inspectBody.innerHTML = g.inspect || '<pre class="plain"></pre>';
    if (!g.inspect) inspectBody.firstChild.textContent = g.code;
    const edit = $("inspect-edit");
    edit.hidden = g.kind !== "arcade"; edit.href = "playground.html#example=" + encodeURIComponent(g.file);
    const lines = inspectBody.querySelectorAll(".listing li");
    for (const b of inspectBody.querySelectorAll(".step")) {
      b.onclick = () => {
        const from = +b.dataset.from, to = +b.dataset.to;
        for (const x of inspectBody.querySelectorAll(".step.on")) x.classList.remove("on");
        b.classList.add("on");
        lines.forEach((li, i) => li.classList.toggle("hot", i + 1 >= from && i + 1 <= to));
        if (lines[from - 1]) {
          const box = lines[from - 1].closest(".listing"), top = lines[from - 1].offsetTop;
          box.scrollTo({ top: Math.max(0, top - 24), behavior: calm ? "auto" : "smooth" });
        }
      };
    }
  }
  inspectBtn.onclick = () => {
    const open_ = inspectBox.hidden;
    if (current) history.replaceState(null, "", "#" + current.id + (open_ ? "/inspect" : ""));
    setInspect(open_);
    if (open_) inspectBox.scrollIntoView({ behavior: calm ? "auto" : "smooth", block: "start" });
  };

  function open(hash) {
    const [id, extra] = hash.split("/");
    const g = games.find((x) => x.id === id);
    stopArcade();
    if (!g) { current = null; cancelTyping(); lobby.hidden = false; stage.hidden = true; document.title = "Games - HumanLang"; return; }
    const same = current === g;
    current = g;
    const arc = g.kind === "arcade";
    abox.hidden = !arc; screen.hidden = arc; $("speed").parentElement.hidden = arc;
    $("arcade-keys").textContent = g.keys ? "Keys: " + g.keys : "";
    fillInspect(g); setInspect(extra === "inspect");
    lobby.hidden = true; stage.hidden = false;
    title.textContent = g.title + (g.subtitle ? " - " + g.subtitle : "");
    document.title = g.title + " - HumanLang Games";
    tags.textContent = (g.tags || []).join("  ·  ");
    const banner = $("gbanner");
    if (g.image) { banner.src = g.image; banner.hidden = false; } else banner.hidden = true;
    if (extra === "inspect") inspectBox.scrollIntoView(); else window.scrollTo(0, 0);
    if (!same) play();
  }
  restartBtn.onclick = () => { if (current && current.kind === "arcade") { startArcade(); return; } if (running) { worker.terminate(); running = false; startWorker(); } play(); };
  backBtn.onclick = () => { if (worker && running) { worker.terminate(); running = false; startWorker(); } location.hash = ""; };
  window.addEventListener("hashchange", () => open(location.hash.slice(1)));

  startWorker();
  open(location.hash.slice(1));
})();

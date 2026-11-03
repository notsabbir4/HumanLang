(function () {
  const $ = (id) => document.getElementById(id);
  const games = window.HL_GAMES;
  const lobby = $("lobby"), stage = $("stage"), screen = $("screen"), status = $("gstatus");
  const restartBtn = $("restart"), backBtn = $("back"), title = $("gtitle"), tags = $("gtags");
  let worker = null, ready = false, running = false, current = null, answers = [], waiting = false;

  // ---- the lobby: one card per game ----
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
    $("grid").appendChild(a);
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

  function run() {
    if (!ready || running || !current) return;
    running = true; setStatus("...");
    worker.postMessage({ type: "run", code: current.code, inputs: answers, seed: 1 });
  }

  function play() {
    answers = []; waiting = false; shown(""); restartBtn.textContent = "Restart"; setStatus("");
    if (!ready) { setStatus("Loading HumanLang... (the first time takes a few seconds)"); return; }
    if (running) { worker.terminate(); startWorker(); return; }  // answered mid-run: start clean
    run();
  }

  // ---- showing a game ----
  function open(id) {
    const g = games.find((x) => x.id === id);
    if (!g) { current = null; cancelTyping(); lobby.hidden = false; stage.hidden = true; document.title = "Games - HumanLang"; return; }
    current = g;
    lobby.hidden = true; stage.hidden = false;
    title.textContent = g.title + (g.subtitle ? " - " + g.subtitle : "");
    document.title = g.title + " - HumanLang Games";
    tags.textContent = (g.tags || []).join("  ·  ");
    const banner = $("gbanner");
    if (g.image) { banner.src = g.image; banner.hidden = false; } else banner.hidden = true;
    window.scrollTo(0, 0);
    play();
  }
  restartBtn.onclick = () => { if (running) { worker.terminate(); running = false; startWorker(); } play(); };
  backBtn.onclick = () => { if (worker && running) { worker.terminate(); running = false; startWorker(); } location.hash = ""; };
  window.addEventListener("hashchange", () => open(location.hash.slice(1)));

  startWorker();
  open(location.hash.slice(1));
})();

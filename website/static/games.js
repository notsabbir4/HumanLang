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

  function shown(text) { screen.textContent = text; screen.className = ""; }
  function bottom() { screen.scrollTop = screen.scrollHeight; }

  function ask(before, question) {
    waiting = true; setStatus("Type your answer and press Enter.");
    shown(before + question);
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
    shown(text);
    screen.className = m.err ? "error" : "";
    setStatus(m.err ? "The game hit a problem. Press Play again to restart." : "The end. Press Play again to start over.");
    restartBtn.textContent = "Play again";
    bottom();
  }

  function run() {
    if (!ready || running || !current) return;
    running = true; setStatus("...");
    worker.postMessage({ type: "run", code: current.code, inputs: answers, seed: 1 });
  }

  function play() {
    answers = []; waiting = false; shown(""); restartBtn.textContent = "Restart";
    if (!ready) { setStatus("Loading HumanLang... (the first time takes a few seconds)"); return; }
    if (running) { worker.terminate(); startWorker(); return; }  // answered mid-run: start clean
    run();
  }

  // ---- showing a game ----
  function open(id) {
    const g = games.find((x) => x.id === id);
    if (!g) { current = null; lobby.hidden = false; stage.hidden = true; document.title = "Games - HumanLang"; return; }
    current = g;
    lobby.hidden = true; stage.hidden = false;
    title.textContent = g.title + (g.subtitle ? " - " + g.subtitle : "");
    document.title = g.title + " - HumanLang Games";
    tags.textContent = (g.tags || []).join("  ·  ");
    window.scrollTo(0, 0);
    play();
  }
  restartBtn.onclick = () => { if (running) { worker.terminate(); running = false; startWorker(); } play(); };
  backBtn.onclick = () => { if (worker && running) { worker.terminate(); running = false; startWorker(); } location.hash = ""; };
  window.addEventListener("hashchange", () => open(location.hash.slice(1)));

  startWorker();
  open(location.hash.slice(1));
})();

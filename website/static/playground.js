(function () {
  const $ = (id) => document.getElementById(id);
  const code = $("code"), inputs = $("inputs"), out = $("out"), status = $("status");
  const runBtn = $("run"), stopBtn = $("stop"), shareBtn = $("share"), pick = $("examples");
  const examples = window.HL_EXAMPLES;
  const hl = $("hl"), gutter = $("gutter"), pos = $("pos"), took = $("took"), themeBtn = $("theme");
  const tabConsole = $("tab-console"), tabInput = $("tab-input"), inpane = $("inpane");
  const tabPreview = $("tab-preview"), prepane = $("prepane"), preview = $("preview"), pnote = $("pnote");
  let pending = false, liveTimer = null, lastPage = null, liveRun = false;
  let worker = null, ready = false, running = false, slowTimer = null, startedAt = 0;

  // ---- colours: the same words and colours as the docs ----
  const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const alt = (w) => w.slice().sort((a, b) => b.length - a.length).map((x) => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|");
  const W = window.HL_WORDS;
  const TOKEN = new RegExp(
    "(?<c>^[ \\t]*note:.*$)|(?<s>\"(?:\\\\.|[^\"\\\\])*\")|(?<n>\\b\\d+(?:\\.\\d+)?\\b)" +
    "|\\b(?<k>" + alt(W.k) + ")\\b|\\b(?<o>" + alt(W.o) + ")\\b|\\b(?<f>" + alt(W.f) + ")\\b|\\b(?<v>" + alt(W.v) + ")\\b", "gm");
  function colour(text) {
    let out = "", at = 0, m;
    TOKEN.lastIndex = 0;
    while ((m = TOKEN.exec(text)) !== null) {
      if (m[0] === "") { TOKEN.lastIndex++; continue; }
      out += esc(text.slice(at, m.index));
      const kind = Object.keys(m.groups).find((k) => m.groups[k] !== undefined);
      let t = esc(m[0]);
      if (kind === "s") t = t.replace(/(\{[^{}]*\})/g, '<span class="i">$1</span>');
      out += '<span class="' + kind + '">' + t + "</span>";
      at = m.index + m[0].length;
    }
    return out + esc(text.slice(at));
  }
  function refresh() {
    hl.innerHTML = colour(code.value) + "\n";
    const n = code.value.split("\n").length;
    if (gutter.dataset.n !== String(n)) {
      gutter.dataset.n = n;
      gutter.textContent = Array.from({ length: n }, (_, i) => i + 1).join("\n");
    }
    sync(); where();
  }
  function sync() { hl.scrollTop = code.scrollTop; hl.scrollLeft = code.scrollLeft; gutter.scrollTop = code.scrollTop; }
  function where() {
    const before = code.value.slice(0, code.selectionStart).split("\n");
    pos.textContent = "Ln " + before.length + ", Col " + (before[before.length - 1].length + 1);
  }

  // ---- tabs and theme ----
  function showTab(name) {
    $("out").hidden = name !== "console"; inpane.hidden = name !== "input"; prepane.hidden = name !== "preview";
    tabConsole.className = "tab" + (name === "console" ? " on" : "");
    tabInput.className = "tab" + (name === "input" ? " on" : "");
    tabPreview.className = "tab" + (name === "preview" ? " on" : "");
  }
  tabConsole.onclick = () => showTab("console"); tabInput.onclick = () => showTab("input"); tabPreview.onclick = () => showTab("preview");

  // ---- designs: a program that says "show a page" gets a live preview that follows the typing ----
  const hasPage = (text) => /^[ \t]*show a page\b/m.test(text);
  function showPage(html) {
    lastPage = html; tabPreview.hidden = false;
    if (preview.srcdoc !== html) preview.srcdoc = html;
    pnote.hidden = true;
  }
  // ---- games: a program that says "play a game" runs in the Preview tab, frame by frame ----
  const hasGame = (text) => /^[ \t]*play a game\b/m.test(text);
  const gamebox = $("gamebox"), screen = $("screen");
  let arcade = null, frameWaiting = null;
  function stopGame() { if (arcade) { arcade.stop(); arcade = null; } frameWaiting = null; }
  function startGame() {
    stopGame();
    running = true; runBtn.disabled = true; stopBtn.disabled = false;
    show("", false); took.textContent = ""; setStatus("Starting the game...");
    worker.postMessage({ type: "gamestart", code: code.value });
  }
  function gameInfo(m) {
    running = false; runBtn.disabled = false; stopBtn.disabled = true;
    if (m.error) { show(m.error, true); setStatus("The game has an error"); showTab("console"); return; }
    tabPreview.hidden = false; preview.hidden = true; gamebox.hidden = false; pnote.hidden = true;
    const k = Math.max(1, Math.floor(Math.min(prepane.clientWidth - 16 || 600, 960) / m.info.w));
    screen.style.width = m.info.w * k + "px"; screen.style.height = m.info.h * k + "px";
    arcade = Arcade(screen, m.info, (input) => new Promise((resolve, reject) => {
      frameWaiting = { resolve, reject };
      worker.postMessage({ type: "gameframe", input });
    }), {
      onError: (msg) => { show(msg, true); showTab("console"); setStatus("The game stopped with an error"); },
      onOver: () => setStatus("Game over (press Run to play again)"),
    });
    showTab("preview"); screen.focus(); arcade.start();
    setStatus("Playing: click the game, then use the keys");
  }
  function gameFrame(m) {
    const w = frameWaiting; frameWaiting = null; if (!w) return;
    const f = JSON.parse(m.json);
    if (f.error) w.reject(new Error(f.error)); else w.resolve(f);
  }
  function liveSoon() {
    clearTimeout(liveTimer);
    if (!hasPage(code.value)) return;
    liveTimer = setTimeout(() => { if (running) pending = true; else { liveRun = true; run(); } }, 600);
  }
  function setTheme(t) {
    document.documentElement.dataset.theme = t;
    themeBtn.textContent = t === "dark" ? "Light" : "Dark";
    try { localStorage.setItem("hl-theme", t); } catch (e) { /* private window: fine */ }
  }
  (function () {
    let t = null;
    try { t = localStorage.getItem("hl-theme"); } catch (e) { /* ignore */ }
    if (t !== "light" && t !== "dark") t = window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    setTheme(t);
  })();
  themeBtn.onclick = () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");

  function setStatus(text) { status.textContent = text; }
  function show(text, isError) { out.textContent = text; out.className = isError ? "error" : ""; }

  function startWorker() {
    ready = false; running = false;
    runBtn.disabled = true; stopBtn.disabled = true;
    setStatus("Loading HumanLang... (the first time takes a few seconds)");
    worker = new Worker("worker.js");
    worker.onmessage = (e) => {
      const m = e.data;
      if (m.type === "ready") { ready = true; runBtn.disabled = false; setStatus("Ready (Ctrl+Enter to run)"); }
      else if (m.type === "gameinfo") gameInfo(m);
      else if (m.type === "gameframe") gameFrame(m);
      else if (m.type === "error") { setStatus("Could not load the playground: " + m.message); }
      else if (m.type === "result" && m.need !== undefined) {
        // the program asked a question: show it in the output box, let the person type next to it,
        // remember the answer, and run again with it
        running = false; clearTimeout(slowTimer);
        if (liveRun) { liveRun = false; runBtn.disabled = false; stopBtn.disabled = true; setStatus("The preview needs answers: put them in the Answers tab, or press Run."); return; }
        stopBtn.disabled = false; setStatus("Waiting for your answer...");
        askHere(m.out || "", m.need);
      }
      else if (m.type === "result") {
        clearTimeout(slowTimer); running = false;
        runBtn.disabled = false; stopBtn.disabled = true;
        took.textContent = Math.round(performance.now() - startedAt) + " ms";
        let text = m.plain !== undefined ? m.plain : (m.out || "");
        if (m.err) text += (text && !text.endsWith("\n") ? "\n" : "") + m.err;
        if (m.page) {
          showPage(m.page);
          show(text, !!m.err);
          if (!liveRun) showTab("preview");
        } else {
          show(text || "(the program printed nothing)", !!m.err);
          if (!hasPage(code.value)) { tabPreview.hidden = true; if (!prepane.hidden) showTab("console"); lastPage = null; }
          else if (liveRun && lastPage && m.err) {
            pnote.textContent = "Showing your last working page. The Console tab says what to fix."; pnote.hidden = false;
          }
        }
        liveRun = false;
        if (pending) { pending = false; liveRun = true; run(); }
        if (m.warnings && m.warnings.length) {
          const box = document.createElement("div");
          box.className = "warn"; box.textContent = m.warnings.join("\n\n");
          out.appendChild(box);
        }
        setStatus(m.err ? "Finished with an error" : "Finished");
      }
    };
  }

  function askHere(before, question) {
    out.className = ""; out.textContent = before + question;
    const box = document.createElement("input");
    box.type = "text"; box.className = "answer"; box.setAttribute("aria-label", question.trim() || "Your answer");
    box.autocomplete = "off"; box.spellcheck = false;
    out.appendChild(box); box.focus();
    box.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        inputs.value += (inputs.value === "" ? "" : "\n") + box.value;
        out.textContent = before + question + box.value + "\n";  // keep the conversation on screen while it continues
        run(true);
      } else if (e.key === "Escape") { e.preventDefault(); stop(); }
    });
  }

  function run(again) {
    if (!ready || running) return;
    if (hasGame(code.value) && again !== true) { startGame(); return; }
    stopGame(); gamebox.hidden = true; preview.hidden = false;
    running = true; runBtn.disabled = true; stopBtn.disabled = false;
    if (again !== true && !liveRun) { show("", false); startedAt = performance.now(); took.textContent = ""; showTab("console"); }
    else if (liveRun) { startedAt = performance.now(); took.textContent = ""; }
    setStatus("Running...");
    slowTimer = setTimeout(() => setStatus("Still running... press Stop if it is stuck in a loop."), 3000);
    worker.postMessage({ type: "run", code: code.value, inputs: inputs.value === "" ? [] : inputs.value.split("\n") });
  }

  function stop() {
    clearTimeout(slowTimer); stopGame();
    worker.terminate();
    show("Stopped.", false);
    startWorker();
  }

  function loadExample(name) {
    const ex = examples[name];
    if (!ex) return;
    code.value = ex.code; inputs.value = ex.inputs || ""; show("", false); lastPage = null; tabPreview.hidden = true; showTab("console");
    pick.value = name; code.scrollTop = 0; code.scrollLeft = 0; refresh(); liveSoon();
  }

  function encode(text) { return btoa(String.fromCharCode(...new TextEncoder().encode(text))); }
  function decode(b64) { return new TextDecoder().decode(Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))); }

  for (const name of Object.keys(examples)) {
    const o = document.createElement("option"); o.value = name; o.textContent = name; pick.appendChild(o);
  }
  pick.onchange = () => loadExample(pick.value);
  runBtn.onclick = () => run(); stopBtn.onclick = stop;
  shareBtn.onclick = async () => {
    const link = location.origin + location.pathname + "#code=" + encodeURIComponent(encode(code.value)) +
      (inputs.value ? "&in=" + encodeURIComponent(encode(inputs.value)) : "");
    history.replaceState(null, "", link);
    try { await navigator.clipboard.writeText(link); setStatus("Link copied. Anyone with it sees your program."); }
    catch (e) { setStatus("Copy the link from your address bar."); }
  };
  code.addEventListener("input", refresh);
  code.addEventListener("input", liveSoon);
  code.addEventListener("scroll", sync);
  code.addEventListener("keyup", where); code.addEventListener("click", where);
  code.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const s = code.selectionStart;
      code.value = code.value.slice(0, s) + "    " + code.value.slice(code.selectionEnd);
      code.selectionStart = code.selectionEnd = s + 4; refresh();
    } else if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(); }
  });
  // editing the program means the dropdown no longer describes it
  code.addEventListener("input", () => {
    if (pick.value && examples[pick.value] && code.value !== examples[pick.value].code) pick.value = "";
  });

  const params = new URLSearchParams(location.hash.slice(1));
  try {
    if (params.get("code")) {
      const o = document.createElement("option"); o.value = ""; o.textContent = "(your program)"; pick.insertBefore(o, pick.firstChild); pick.value = ""; code.value = decode(params.get("code")); inputs.value = params.get("in") ? decode(params.get("in")) : ""; }
    else if (params.get("example") && examples[params.get("example")]) loadExample(params.get("example"));
    else loadExample("hello.hum");
  } catch (e) { loadExample("hello.hum"); }
  refresh();
  startWorker();
  const firstRun = setInterval(() => { if (ready) { clearInterval(firstRun); if (hasPage(code.value) || hasGame(code.value)) { liveRun = false; run(); } } }, 200);
})();

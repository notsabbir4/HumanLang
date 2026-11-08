(function () {
  const $ = (id) => document.getElementById(id);
  const code = $("code"), inputs = $("inputs"), out = $("out"), status = $("status");
  const runBtn = $("run"), stopBtn = $("stop"), shareBtn = $("share"), pick = $("examples");
  const examples = window.HL_EXAMPLES;
  const hl = $("hl"), gutter = $("gutter"), pos = $("pos"), took = $("took"), themeBtn = $("theme");
  const stepspane = $("stepspane"), tabSteps = $("tab-steps"), stepBtn = $("stepbtn");
  const filespane = $("filespane"), tabFiles = $("tab-files");
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
    stepspane.hidden = name !== "steps"; tabSteps.className = "tab" + (name === "steps" ? " on" : "");
    filespane.hidden = name !== "files"; tabFiles.className = "tab" + (name === "files" ? " on" : "");
    tabConsole.className = "tab" + (name === "console" ? " on" : "");
    tabInput.className = "tab" + (name === "input" ? " on" : "");
    tabPreview.className = "tab" + (name === "preview" ? " on" : "");
  }
  tabConsole.onclick = () => showTab("console"); tabInput.onclick = () => showTab("input"); tabPreview.onclick = () => showTab("preview"); tabFiles.onclick = () => showTab("files"); tabSteps.onclick = () => showTab("steps");

  // ---- Post to Community: open the GitHub post form with the program filled in ----
  $("postbtn").onclick = async () => {
    const text = code.value;
    if (!text.trim()) { setStatus("Write a program first, then post it."); return; }
    const named = /^[ \t]*(?:play a game|show a page)\s+titled\s+"([^"{}]{1,60})"/m.exec(text);
    const category = hasGame(text) ? "Games" : hasPage(text) ? "Design (pages and pictures)" : "Other";
    const q = { template: "community-post.yml", title: "Post: " + (named ? named[1] : "My HumanLang program"), category,
      description: "I made this with HumanLang. (Tell people what it does and how to use it.)" };
    let note = "Opened the post form with your program filled in. Check it, then press Submit.";
    const withCode = new URLSearchParams(Object.assign({}, q, { code: text })).toString();
    let url;
    if (withCode.length < 6000) url = (window.HL_REPO || "") + "/issues/new?" + withCode;
    else {
      url = (window.HL_REPO || "") + "/issues/new?" + new URLSearchParams(q).toString();
      let copied = false;
      try { await navigator.clipboard.writeText(text); copied = true; } catch (e) { /* no clipboard permission */ }
      note = copied ? "Your program is long, so I copied it. Paste it into the code box of the form that opened."
                    : "Your program is long. Copy it from the editor and paste it into the code box of the form that opened.";
    }
    window.open(url, "_blank", "noopener");
    setStatus(note);
  };

  // ---- step through: record the run, then walk it line by line ----
  let rec = null, at = 0;
  function showStep() {
    const n = rec.steps.length;
    $("steprange").max = Math.max(0, n - 1); $("steprange").value = at;
    $("stepcount").textContent = n ? "Step " + (at + 1) + " of " + n + (rec.truncated ? "+" : "") : "";
    const st = rec.steps[at], prev = at ? rec.steps[at - 1].vars : {};
    const cur = st ? st.line : 0;
    const lines = code.value.split("\n"), box = $("stepcode"); box.textContent = "";
    lines.forEach((t, i) => { const d = document.createElement("span"); d.className = "ln" + (i + 1 === cur ? " cur" : ""); d.textContent = (i + 1) + "  " + t; box.appendChild(d); });
    const here = box.querySelector(".cur"); if (here) here.scrollIntoView({ block: "nearest" });
    $("stepsays").textContent = st ? "Line " + st.line + ": " + st.says : (rec.error || "There is nothing to step through.");
    const tb = $("stepvars"); tb.textContent = "";
    const vars = st ? st.vars : {}, keys = Object.keys(vars);
    if (!keys.length) { const r = tb.insertRow(); r.insertCell().textContent = "(none yet)"; }
    keys.forEach((k) => { const r = tb.insertRow(), a = r.insertCell(), b = r.insertCell();
      a.textContent = k; b.textContent = vars[k]; if (prev[k] !== vars[k]) b.className = "ch"; });
    const upto = st ? st.out : rec.output.length;
    $("stepout").textContent = at >= n - 1 && !rec.error ? rec.output : rec.output.slice(0, upto);
    if (at >= n - 1 && rec.error) $("stepsays").textContent += (st ? "\n\n" : "") + rec.error;
  }
  const goStep = (k) => { if (!rec) return; at = Math.max(0, Math.min(rec.steps.length - 1, k)); showStep(); };
  $("stepnext").onclick = () => goStep(at + 1); $("stepback").onclick = () => goStep(at - 1);
  $("steprange").oninput = (e) => goStep(+e.target.value);
  stepBtn.onclick = () => {
    if (!ready || running) return;
    setStatus("Recording the steps..."); running = true;
    worker.postMessage({ type: "debug", code: code.value, inputs: inputs.value === "" ? [] : inputs.value.split("\n") });
  };

  // ---- your own files (pictures, sounds, music): kept in this browser's IndexedDB ----
  const MAX_FILE = 3 * 1024 * 1024, MAX_TOTAL = 16 * 1024 * 1024, MAX_FILES = 24;
  const KIND = (n) => /\.(png|jpe?g|gif|webp)$/i.test(n) ? "picture" : /\.(wav|mp3|ogg|m4a)$/i.test(n) ? "audio" : null;
  let myFiles = {};  // name -> { kind, url (a data: address), size }
  function dbOpen() {
    return new Promise((res, rej) => {
      let r; try { r = indexedDB.open("hl-files", 1); } catch (e) { rej(e); return; }
      r.onupgradeneeded = () => r.result.createObjectStore("files");
      r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
    });
  }
  async function dbDo(mode, fn) {
    try {
      const db = await dbOpen();
      return await new Promise((res, rej) => { const tx = db.transaction("files", mode), st = tx.objectStore("files"), q = fn(st);
        tx.oncomplete = () => res(q && q.result); tx.onerror = () => rej(tx.error); });
    } catch (e) { return null; }
  }
  const fileNote = (t) => { $("filenote").textContent = t || ""; };
  function renderFiles() {
    const ul = $("filelist"); ul.textContent = "";
    for (const name of Object.keys(myFiles)) {
      const f = myFiles[name], li = document.createElement("li");
      if (f.kind === "picture") { const im = document.createElement("img"); im.src = f.url; im.alt = ""; li.appendChild(im); }
      else { const b = document.createElement("button"); b.type = "button"; b.className = "btn ghost"; b.textContent = "Play";
        b.onclick = () => { const a = new Audio(f.url); a.play().catch(() => {}); }; li.appendChild(b); }
      const nm = document.createElement("span"); nm.className = "nm"; nm.textContent = name; li.appendChild(nm);
      const sz = document.createElement("span"); sz.className = "sz"; sz.textContent = Math.max(1, Math.round(f.size / 1024)) + " KB"; li.appendChild(sz);
      const rm = document.createElement("button"); rm.type = "button"; rm.className = "btn ghost"; rm.textContent = "Remove";
      rm.onclick = async () => { delete myFiles[name]; await dbDo("readwrite", (s) => s.delete(name)); renderFiles(); };
      li.appendChild(rm); ul.appendChild(li);
    }
  }
  const total = () => Object.values(myFiles).reduce((a, f) => a + f.size, 0);
  $("addfiles").onchange = async (e) => {
    const notes = [];
    for (const file of Array.from(e.target.files)) {
      const name = file.name.replace(/[^\w.\- ]/g, "_"), kind = KIND(name);
      if (!kind) { notes.push(name + ": I can use png, jpg, gif, webp, wav, mp3, ogg and m4a files."); continue; }
      if (file.size > MAX_FILE) { notes.push(name + " is bigger than 3 MB."); continue; }
      if (!(name in myFiles) && Object.keys(myFiles).length >= MAX_FILES) { notes.push("You can add up to " + MAX_FILES + " files."); continue; }
      if (total() - ((myFiles[name] || {}).size || 0) + file.size > MAX_TOTAL) { notes.push(name + ": that would be more than 16 MB in total."); continue; }
      const url = await new Promise((res) => { const r = new FileReader(); r.onload = () => res(r.result); r.readAsDataURL(file); });
      myFiles[name] = { kind, url, size: file.size };
      await dbDo("readwrite", (s) => s.put(myFiles[name], name));
    }
    e.target.value = ""; fileNote(notes.join(" ")); renderFiles();
  };
  (async () => {
    const db = await dbOpen().catch(() => null); if (!db) return;
    const tx = db.transaction("files", "readonly"), st = tx.objectStore("files"), keys = st.getAllKeys(), vals = st.getAll();
    tx.oncomplete = () => { keys.result.forEach((k, i) => { myFiles[k] = vals.result[i]; }); renderFiles(); };
  })();
  const fileKinds = () => JSON.stringify(Object.fromEntries(Object.entries(myFiles).map(([k, f]) => [k, f.kind])));
  const fileUrls = () => Object.fromEntries(Object.entries(myFiles).map(([k, f]) => [k, f.url]));

  // ---- designs: a program that says "show a page" gets a live preview that follows the typing ----
  const hasPage = (text) => /^[ \t]*show a page\b/m.test(text);
  function showPage(html) {
    lastPage = html; tabPreview.hidden = false;
    if (preview.srcdoc !== html) preview.srcdoc = html;
    pnote.hidden = true;
  }
  // ---- games: a program that says "play a game" runs in the Preview tab, frame by frame ----
  // what programs "remember" lives in this browser's storage
  const MEM = "hl-memory";
  const getStore = () => { try { return localStorage.getItem(MEM) || ""; } catch (e) { return ""; } };
  const putStore = (json) => { try { localStorage.setItem(MEM, json); } catch (e) { /* storage blocked: it just won't be remembered */ } };
  const hasLive = (text) => /^when the (button|input|box)\b/m.test(text) && hasPage(text);
  const hasGame = (text) => /^[ \t]*play a game\b/m.test(text);
  const gamebox = $("gamebox"), screen = $("screen");
  let arcade = null, frameWaiting = null;
  function stopGame() { if (arcade) { arcade.stop(); arcade = null; } frameWaiting = null; }
  function startGame() {
    stopGame();
    running = true; runBtn.disabled = true; stopBtn.disabled = false;
    show("", false); took.textContent = ""; setStatus("Starting the game...");
    worker.postMessage({ type: "gamestart", code: code.value, store: getStore(), assets: fileKinds() });
  }
  function gameInfo(m) {
    running = false; runBtn.disabled = false; stopBtn.disabled = true;
    if (m.error) { show(m.error, true); setStatus("The game has an error"); showTab("console"); return; }
    tabPreview.hidden = false; preview.hidden = true; gamebox.hidden = false; pnote.hidden = true;
    const k = Math.max(1, Math.floor(Math.min(prepane.clientWidth - 16 || 600, 960) / m.info.w));
    screen.style.width = m.info.w * k + "px"; screen.style.height = m.info.h * k + "px";
    arcade = Arcade(screen, Object.assign(m.info), (input) => new Promise((resolve, reject) => {
      frameWaiting = { resolve, reject };
      worker.postMessage({ type: "gameframe", input });
    }), {
      assets: fileUrls(),
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
      if (m.type === "ready") { ready = true; runBtn.disabled = false; stepBtn.disabled = false; setStatus("Ready (Ctrl+Enter to run)"); }
      else if (m.type === "memory") putStore(m.json);
      else if (m.type === "debugged") {
        running = false; rec = { steps: m.steps || [], output: m.output || "", error: m.error || null, truncated: !!m.truncated };
        at = 0; tabSteps.hidden = false; showTab("steps"); showStep(); setStatus("Use Next and Back to walk through your program");
      }
      else if (m.type === "livestarted") liveStarted(m);
      else if (m.type === "liveupdate") liveUpdate(m);
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
        if (m.memory) putStore(m.memory);
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

  // ---- live pages: clicks inside the preview come here, run in the worker, and the page is updated ----
  function liveStarted(m) {
    clearTimeout(slowTimer); running = false; runBtn.disabled = false; stopBtn.disabled = true;
    took.textContent = Math.round(performance.now() - startedAt) + " ms";
    if (m.error) { show(m.error, true); setStatus("Finished with an error"); showTab("console"); return; }
    if (m.page) { preview.srcdoc = ""; showPage(m.page); if (!liveRun) showTab("preview"); }
    show(m.out || "(the program printed nothing)", false);
    if (m.warnings && m.warnings.length) {
      const box = document.createElement("div"); box.className = "warn"; box.textContent = m.warnings.join("\n\n"); out.appendChild(box);
    }
    liveRun = false;
    setStatus(m.live ? "Live page: click its buttons in the Preview tab" : "Finished");
  }
  function liveUpdate(m) {
    if (m.error) { pnote.textContent = m.error; pnote.hidden = false; show(m.error, true); return; }
    pnote.hidden = true;
    if (m.out) show(m.out, false);
    preview.contentWindow.postMessage({ hl: "update", html: m.html }, "*");
  }
  window.addEventListener("message", (e) => {
    if (e.source === preview.contentWindow && e.data && e.data.hl === "event" && worker && ready)
      worker.postMessage({ type: "liveevent", msg: e.data.msg });
  });

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
    if (hasLive(code.value) && again !== true) {
      stopGame(); gamebox.hidden = true; preview.hidden = false; running = true; runBtn.disabled = true; stopBtn.disabled = false;
      if (!liveRun) { show("", false); took.textContent = ""; showTab("console"); }
      startedAt = performance.now(); setStatus("Running...");
      worker.postMessage({ type: "livestart", code: code.value, store: getStore() });
      return;
    }
    stopGame(); gamebox.hidden = true; preview.hidden = false;
    running = true; runBtn.disabled = true; stopBtn.disabled = false;
    if (again !== true && !liveRun) { show("", false); startedAt = performance.now(); took.textContent = ""; showTab("console"); }
    else if (liveRun) { startedAt = performance.now(); took.textContent = ""; }
    setStatus("Running...");
    slowTimer = setTimeout(() => setStatus("Still running... press Stop if it is stuck in a loop."), 3000);
    worker.postMessage({ type: "run", code: code.value, inputs: inputs.value === "" ? [] : inputs.value.split("\n"), store: getStore() });
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
    else if (params.get("post") && window.HLCommunity) {
      // a community post: fetch it (the program is only read here, then runs in your browser like any other)
      const o = document.createElement("option"); o.value = ""; o.textContent = "(community post #" + params.get("post") + ")"; pick.insertBefore(o, pick.firstChild); pick.value = "";
      code.value = 'note: loading community post #' + params.get("post") + ' ...';
      HLCommunity.getIssue(params.get("post")).then((issue) => {
        const p = issue && HLCommunity.parse(issue);
        code.value = p && p.verified ? p.code : 'note: there is no published community post with that ID.';
        refresh();
      }).catch((e) => { code.value = "note: I could not load the post (" + e.message + ")."; refresh(); });
    }
    else if (params.get("example") && examples[params.get("example")]) loadExample(params.get("example"));
    else loadExample("hello.hum");
  } catch (e) { loadExample("hello.hum"); }
  refresh();
  startWorker();
  const firstRun = setInterval(() => { if (ready) { clearInterval(firstRun); if (hasPage(code.value) || hasGame(code.value)) { liveRun = false; run(); } } }, 200);
})();

(function () {
  const $ = (id) => document.getElementById(id);
  const code = $("code"), inputs = $("inputs"), out = $("out"), status = $("status");
  const runBtn = $("run"), stopBtn = $("stop"), shareBtn = $("share"), pick = $("examples");
  const examples = window.HL_EXAMPLES;
  const hl = $("hl"), gutter = $("gutter"), pos = $("pos"), took = $("took"), themeBtn = $("theme");
  const tabConsole = $("tab-console"), tabInput = $("tab-input"), inpane = $("inpane");
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
    const c = name === "console";
    $("out").hidden = !c; inpane.hidden = c;
    tabConsole.className = "tab" + (c ? " on" : ""); tabInput.className = "tab" + (c ? "" : " on");
  }
  tabConsole.onclick = () => showTab("console"); tabInput.onclick = () => showTab("input");
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
      else if (m.type === "error") { setStatus("Could not load the playground: " + m.message); }
      else if (m.type === "result" && m.need !== undefined) {
        // the program asked a question: show it in the output box, let the person type next to it,
        // remember the answer, and run again with it
        running = false; clearTimeout(slowTimer);
        stopBtn.disabled = false; setStatus("Waiting for your answer...");
        askHere(m.out || "", m.need);
      }
      else if (m.type === "result") {
        clearTimeout(slowTimer); running = false;
        runBtn.disabled = false; stopBtn.disabled = true;
        took.textContent = Math.round(performance.now() - startedAt) + " ms";
        let text = m.plain !== undefined ? m.plain : (m.out || "");
        if (m.err) text += (text && !text.endsWith("\n") ? "\n" : "") + m.err;
        show(text || "(the program printed nothing)", !!m.err);
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
    running = true; runBtn.disabled = true; stopBtn.disabled = false;
    if (again !== true) { show("", false); startedAt = performance.now(); took.textContent = ""; showTab("console"); }
    setStatus("Running...");
    slowTimer = setTimeout(() => setStatus("Still running... press Stop if it is stuck in a loop."), 3000);
    worker.postMessage({ type: "run", code: code.value, inputs: inputs.value === "" ? [] : inputs.value.split("\n") });
  }

  function stop() {
    clearTimeout(slowTimer);
    worker.terminate();
    show("Stopped.", false);
    startWorker();
  }

  function loadExample(name) {
    const ex = examples[name];
    if (!ex) return;
    code.value = ex.code; inputs.value = ex.inputs || ""; show("", false);
    pick.value = name; code.scrollTop = 0; code.scrollLeft = 0; refresh();
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
    else loadExample("hello.hum");
  } catch (e) { loadExample("hello.hum"); }
  refresh();
  startWorker();
})();

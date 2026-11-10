/* Nina: the HumanLang coding assistant. The thinking happens on the server (Supabase function "nina"); the tools run
   HERE, in your browser: your project's files, checking and running programs. Nothing is read from your editor unless you
   press "Review my code" and allow it. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const btn = $("ninabtn"), drawer = $("nina"), code = $("code");
  if (!btn || !drawer) return;
  const CFG = window.HL_SUPABASE || {};
  const MAX_STEPS = 14, MAX_FILE = 100000, MAX_FILES = 40, HISTORY_LIMIT = 420000;
  const NAME_OK = /^[\w\- .]{1,60}\.(hum|txt|md)$/;
  let history = [], busy = false, files = {}, current = "main.hum", worker = null, workerReady = null, pending = new Map(), seq = 0, remaining = null;

  const el = (tag, attrs, ...kids) => {
    const e = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => { if (k === "class") e.className = v; else if (k === "text") e.textContent = v; else if (k.startsWith("on")) e[k] = v; else e.setAttribute(k, v); });
    kids.forEach((k) => e.appendChild(typeof k === "string" ? document.createTextNode(k) : k));
    return e;
  };

  // ---------------- the project (files kept in this browser) ----------------
  function db() {
    return new Promise((res, rej) => {
      let r; try { r = indexedDB.open("hl-project", 1); } catch (e) { rej(e); return; }
      r.onupgradeneeded = () => r.result.createObjectStore("files");
      r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
    });
  }
  async function loadFiles() {
    try {
      const d = await db(), tx = d.transaction("files", "readonly"), st = tx.objectStore("files"), k = st.getAllKeys(), v = st.getAll();
      await new Promise((res) => { tx.oncomplete = res; tx.onerror = res; });
      files = {}; (k.result || []).forEach((name, i) => { files[name] = v.result[i]; });
    } catch (e) { files = files || {}; }
  }
  async function putFile(name, text) {
    files[name] = text;
    try { const d = await db(); d.transaction("files", "readwrite").objectStore("files").put(text, name); } catch (e) { /* kept in memory for now */ }
  }
  async function removeFile(name) {
    delete files[name];
    try { const d = await db(); d.transaction("files", "readwrite").objectStore("files").delete(name); } catch (e) { /* ok */ }
  }
  const editorOpen = () => files[current] !== undefined;

  // ---------------- a second worker, so Nina's runs never disturb yours ----------------
  function startWorker() {
    if (workerReady) return workerReady;
    workerReady = new Promise((resolve, reject) => {
      worker = new Worker("worker.js");
      worker.onmessage = (e) => {
        const m = e.data;
        if (m.type === "ready") resolve();
        else if (m.type === "error") reject(new Error(m.message));
        else if (m.type === "nresult" && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
      };
    });
    return workerReady;
  }
  async function ask(type, extra) {
    await startWorker();
    const id = ++seq;
    return new Promise((resolve) => {
      pending.set(id, resolve);
      worker.postMessage(Object.assign({ type, id, files: JSON.stringify(files) }, extra));
      setTimeout(() => { if (pending.has(id)) { pending.delete(id); resolve({ err: "Timed out: the program ran too long." }); worker.terminate(); worker = null; workerReady = null; } }, 20000);
    });
  }

  // ---------------- tools Nina can use ----------------
  const trim = (t, n) => (t.length > n ? t.slice(0, n) + "\n...(cut)" : t);
  async function runTool(name, input) {
    input = input || {};
    const fname = String(input.name || "");
    const needName = () => (NAME_OK.test(fname) ? null : "A file name has letters, numbers, - _ . and space, and ends in .hum, .txt or .md.");
    switch (name) {
      case "list_files": return { text: Object.keys(files).length ? Object.entries(files).map(([n, t]) => n + " (" + t.length + " characters)").join("\n") : "The project has no files yet.", label: "listed the files" };
      case "read_file": { const bad = needName(); if (bad) return { text: bad, error: true };
        if (!(fname in files)) return { text: "There is no file called " + fname + ".", error: true };
        return { text: files[fname], label: "read " + fname }; }
      case "write_file": { const bad = needName(); if (bad) return { text: bad, error: true };
        const t = String(input.content == null ? "" : input.content);
        if (t.length > MAX_FILE) return { text: "That file is too big (limit " + MAX_FILE + " characters).", error: true };
        if (!(fname in files) && Object.keys(files).length >= MAX_FILES) return { text: "The project is full (" + MAX_FILES + " files).", error: true };
        await putFile(fname, t);
        if (fname === current && document.getElementById("collab-bar").hidden) { code.value = t; code.dispatchEvent(new Event("input", { bubbles: true })); }
        paintFiles(); return { text: "Saved " + fname + " (" + t.length + " characters).", label: "wrote " + fname }; }
      case "delete_file": { const bad = needName(); if (bad) return { text: bad, error: true };
        if (!(fname in files)) return { text: "There is no file called " + fname + ".", error: true };
        await removeFile(fname); paintFiles(); return { text: "Deleted " + fname + ".", label: "deleted " + fname }; }
      case "check_program": case "run_program": {
        const bad = needName(); if (bad) return { text: bad, error: true };
        if (!(fname in files)) return { text: "There is no file called " + fname + ".", error: true };
        if (name === "check_program") {
          const r = await ask("ncheck", { code: files[fname], name: fname });
          const parts = []; if (r.err) parts.push("MISTAKE:\n" + r.err); (r.warnings || []).forEach((w) => parts.push("HEADS-UP:\n" + w));
          return { text: parts.length ? parts.join("\n\n") : "No problems found by checking. (Checking cannot catch everything: run it too.)", label: "checked " + fname, error: !!r.err };
        }
        const r = await ask("nrun", { code: files[fname], name: fname, inputs: Array.isArray(input.answers) ? input.answers.map(String) : [] });
        const parts = []; if (r.out) parts.push("OUTPUT:\n" + trim(r.out, 4000));
        if (r.need) parts.push("The program stops to ask: " + r.need + "\nGive its answers in 'answers'.");
        if (r.err) parts.push("ERROR:\n" + r.err); (r.warnings || []).forEach((w) => parts.push("HEADS-UP:\n" + w));
        if (r.kind === "game") parts.push("(It is a game: it was started, not played. Check the code carefully.)"); if (r.kind === "page") parts.push("(It builds a page: it was built, not shown.)");
        return { text: parts.join("\n\n") || "It ran and printed nothing.", label: "ran " + fname, error: !!r.err };
      }
    }
    return { text: "I don't have a tool called " + name + ".", error: true };
  }

  // ---------------- talking to the server ----------------
  async function callNina() {
    const s = await HLAccount.session();
    if (!s) throw new Error("Sign in to talk to Nina.");
    const r = await fetch(CFG.url + "/functions/v1/nina", {
      method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + s.access_token, apikey: CFG.key },
      body: JSON.stringify({ messages: history }),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || "Nina could not answer (" + r.status + ").");
    remaining = data.remaining; return data;
  }
  function trimHistory() {
    while (JSON.stringify(history).length > HISTORY_LIMIT && history.length > 2) {
      history.shift();
      while (history.length && !(history[0].role === "user" && Array.isArray(history[0].content) && history[0].content.some((b) => b.type === "text"))) history.shift();
    }
  }

  async function converse(userText) {
    if (busy) return; busy = true; setBusy(true);
    addMsg("me", userText);
    history.push({ role: "user", content: [{ type: "text", text: userText }] });
    try {
      for (let step = 0; step < MAX_STEPS; step++) {
        trimHistory();
        const resp = await callNina();
        history.push({ role: "assistant", content: resp.content });
        const text = resp.content.filter((b) => b.type === "text").map((b) => b.text).join("\n").trim();
        resp.content.forEach((b) => {
          if (b.type === "server_tool_use" && b.input && b.input.query) addAct("searched the web: " + b.input.query);
          if (b.type === "web_search_tool_result" && Array.isArray(b.content)) addSources(b.content);
        });
        if (text) addMsg("nina", text);
        if (resp.stop_reason === "tool_use") {
          const results = [];
          for (const b of resp.content.filter((x) => x.type === "tool_use")) {
            const r = await runTool(b.name, b.input);
            addAct((r.error ? "✗ " : "✓ ") + (r.label || b.name));
            results.push({ type: "tool_result", tool_use_id: b.id, content: trim(r.text, 12000), is_error: !!r.error });
          }
          history.push({ role: "user", content: results });
          continue;
        }
        if (resp.stop_reason === "pause_turn") continue;           // the web search is still going: ask her to carry on
        break;
      }
    } catch (e) { addMsg("nina", "⚠ " + (e.message || e), true); history.pop(); }
    busy = false; setBusy(false); paintFiles();
  }

  // ---------------- the panel ----------------
  let box, input, sendBtn, list;
  function md(text) {               // a very small, safe formatter: code blocks, `code`, **bold**
    const frag = document.createDocumentFragment(), parts = text.split(/```/);
    parts.forEach((p, i) => {
      if (i % 2) { frag.appendChild(el("pre", {}, el("code", { text: p.replace(/^[a-z]*\n/i, "").replace(/\n$/, "") }))); return; }
      p.split(/(`[^`\n]+`|\*\*[^*\n]+\*\*)/).forEach((t) => {
        if (/^`[^`]+`$/.test(t)) frag.appendChild(el("code", { text: t.slice(1, -1) }));
        else if (/^\*\*[^*]+\*\*$/.test(t)) frag.appendChild(el("b", { text: t.slice(2, -2) }));
        else frag.appendChild(document.createTextNode(t));
      });
    });
    return frag;
  }
  function addMsg(who, text) { const m = el("div", { class: "m " + who }); m.appendChild(who === "nina" ? md(text) : document.createTextNode(text)); box.appendChild(m); box.scrollTop = box.scrollHeight; }
  function addAct(text) { box.appendChild(el("div", { class: "act", text })); box.scrollTop = box.scrollHeight; }
  function addSources(items) {
    const seen = new Set(), d = el("div", { class: "src" }, "Sources: ");
    items.filter((x) => x && x.url && /^https?:\/\//.test(x.url)).slice(0, 5).forEach((x) => { if (seen.has(x.url)) return; seen.add(x.url); d.appendChild(el("a", { href: x.url, target: "_blank", rel: "noopener noreferrer", text: (x.title || x.url).slice(0, 60) })); d.appendChild(document.createTextNode("  ")); });
    if (seen.size) { box.appendChild(d); box.scrollTop = box.scrollHeight; }
  }
  function setBusy(b) { if (sendBtn) { sendBtn.disabled = b; sendBtn.textContent = b ? "Working…" : "Send"; } }

  function paintFiles() {
    if (!list) return; list.textContent = "";
    const names = Object.keys(files);
    if (!names.length) { list.appendChild(el("li", { class: "muted", text: "No files yet. Ask Nina to build something, or save your program here." })); return; }
    names.forEach((n) => list.appendChild(el("li", {}, el("span", { text: n + (n === current ? "  (open)" : "") }), el("span", {},
      el("button", { class: "btn ghost", type: "button", text: "Open", onclick: () => { current = n; code.value = files[n]; code.dispatchEvent(new Event("input", { bubbles: true })); $("filetab").textContent = n; paintFiles(); } }),
      el("button", { class: "btn ghost", type: "button", text: "Delete", onclick: async () => { await removeFile(n); paintFiles(); } })))));
  }

  async function review() {
    let ok = false; try { ok = localStorage.getItem("hl-nina-review-ok") === "1"; } catch (e) { /* ask each time */ }
    if (!ok) {
      const remember = el("input", { type: "checkbox", id: "n-rem" });
      const ask = el("div", { class: "m nina" }, "Nina will read your program and its output, only that, to rate it. Allow?",
        el("div", { class: "ntools" },
          el("button", { class: "btn run", type: "button", text: "Allow", onclick: () => { if (remember.checked) { try { localStorage.setItem("hl-nina-review-ok", "1"); } catch (e) { /* ok */ } } ask.remove(); go(); } }),
          el("button", { class: "btn ghost", type: "button", text: "No", onclick: () => ask.remove() }),
          el("label", {}, remember, " Don't ask again")));
      box.appendChild(ask); box.scrollTop = box.scrollHeight; return;
    }
    go();
    function go() {
      const out = ($("out") && $("out").textContent || "").trim();
      converse("Review this program (" + current + ").\n\n```hum\n" + trim(code.value, 60000) + "\n```\n\nOutput of its last run:\n```\n" + trim(out, 3000) + "\n```");
    }
  }

  function panel(me) {
    drawer.textContent = "";
    drawer.appendChild(el("div", { class: "dhead" }, el("strong", { text: "Nina" }), el("span", { class: "muted", id: "n-left" }),
      el("span", {}, el("button", { class: "btn ghost", type: "button", text: "New chat", onclick: () => { if (!busy) { history = []; panel(me); } } }),
        el("button", { class: "btn ghost", type: "button", "aria-label": "Close", text: "Close", onclick: () => { drawer.hidden = true; btn.classList.remove("on"); } }))));
    if (!window.HLAccount || !HLAccount.configured) { drawer.appendChild(el("div", { class: "dbody" }, el("p", { text: "Nina is not switched on for this site yet." }))); return; }
    if (!me) {
      drawer.appendChild(el("div", { class: "dbody" }, el("p", { text: "Sign in with GitHub to talk to Nina. She helps with your HumanLang projects: she writes, checks, runs and reviews code, and can manage a whole project. You can write to her in English or Bangla (বাংলা)." }),
        el("button", { class: "btn run", type: "button", text: "Sign in with GitHub", onclick: async () => { try { await HLAccount.signIn(); } catch (e) { /* shown on the account page */ } } })));
      return;
    }
    box = el("div", { class: "nmsgs", "aria-live": "polite" });
    drawer.appendChild(box);
    addMsg("nina", "Nina here. Tell me what to build or fix. I can also review your code. (What you write to me, and code you let me read, is sent to an AI service. Never put passwords or private information in it.)");
    drawer.appendChild(el("div", { class: "ntools" },
      el("button", { class: "btn ghost", type: "button", text: "Review my code", onclick: () => { if (!busy) review(); } }),
      el("button", { class: "btn ghost", type: "button", text: "Save editor to project", onclick: async () => { if (!NAME_OK.test(current)) current = "main.hum"; await putFile(current, code.value); paintFiles(); addAct("✓ saved " + current); } })));
    input = el("textarea", { rows: "2", placeholder: "What should I do? (English or বাংলা)", "aria-label": "Message to Nina" });
    sendBtn = el("button", { class: "btn run", type: "button", text: "Send" });
    const send = () => { const t = input.value.trim(); if (!t || busy) return; input.value = ""; converse(t); };
    sendBtn.onclick = send;
    input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
    drawer.appendChild(el("div", { class: "nin" }, input, sendBtn));
    list = el("ul", {}); drawer.appendChild(el("div", { class: "nfiles" }, el("strong", { text: "Project files" }), list));
    paintFiles();
  }

  btn.onclick = () => {
    drawer.hidden = !drawer.hidden; btn.classList.toggle("on", !drawer.hidden);
    if (!drawer.hidden) { const c = $("collab"); if (c) c.hidden = true; loadFiles().then(init); }
  };
  let me = null;
  async function init() {
    try { me = window.HLAccount && HLAccount.configured ? await HLAccount.profile() : null; } catch (e) { me = null; }
    if (!drawer.hidden) panel(me);
  }
  if (window.HLAccount) HLAccount.onChange((p) => { me = p; if (!drawer.hidden) panel(p); });
})();

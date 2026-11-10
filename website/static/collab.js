/* Shared coding in the Playground: sign in, start or join a shared program, and everyone's edits, cursors and
   typing show up live. The text syncing is collab-core.js; this file is the sign-in, the room and the screen. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const btn = $("collabbtn"), drawer = $("collab"), bar = $("collab-bar"), code = $("code"), remote = $("remote");
  if (!btn || !drawer) return;
  const YJS = "https://cdn.jsdelivr.net/npm/yjs@13.6.18/+esm";
  let room = null, core = null, channel = null, me = null, Yjs = null, saveTimer = null, presenceIds = new Set(), sb = null, joining = false;

  const el = (tag, attrs, ...kids) => {
    const e = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => { if (k === "class") e.className = v; else if (k === "text") e.textContent = v; else if (k.startsWith("on")) e[k] = v; else e.setAttribute(k, v); });
    kids.forEach((k) => e.appendChild(typeof k === "string" ? document.createTextNode(k) : k));
    return e;
  };
  const say = (t) => { const s = $("status"); if (s) s.textContent = t; };

  // ---------------- the panel ----------------
  function panel() {
    drawer.textContent = "";
    const head = el("div", { class: "dhead" }, el("strong", { text: "Collaborate" }), el("button", { class: "btn ghost", type: "button", onclick: () => { drawer.hidden = true; }, "aria-label": "Close", text: "Close" }));
    drawer.appendChild(head);
    const body = el("div", { class: "dbody" });
    drawer.appendChild(body);
    if (!window.HLAccount || !HLAccount.configured) { body.appendChild(el("p", { text: "Accounts are not switched on for this site yet." })); return; }
    if (!me) {
      body.appendChild(el("p", { text: "Sign in with GitHub to code on the same program with other people, live. You will see who is where and what they type." }));
      body.appendChild(el("button", { class: "btn run", type: "button", text: "Sign in with GitHub", onclick: async () => { try { await HLAccount.signIn(); } catch (e) { say("Could not start sign-in."); } } }));
      return;
    }
    if (!room) {
      body.appendChild(el("p", { text: "Start a shared program from what is in the editor now, or join a friend's with their code." }));
      const name = el("input", { id: "c-name", maxlength: "60", placeholder: "Name (optional)", "aria-label": "Name of the shared program" });
      body.appendChild(name);
      body.appendChild(el("button", { class: "btn run", type: "button", text: "Start a shared program", onclick: () => start(name.value.trim()) }));
      body.appendChild(el("hr"));
      const codeIn = el("input", { id: "c-code", maxlength: "8", placeholder: "Code, like 7F3A9C21", "aria-label": "Code to join", autocapitalize: "characters" });
      body.appendChild(codeIn);
      body.appendChild(el("button", { class: "btn ghost", type: "button", text: "Join", onclick: () => join(codeIn.value) }));
      body.appendChild(el("p", { class: "muted", id: "c-note" }));
      return;
    }
    body.appendChild(el("p", {}, "You are in ", el("strong", { text: room.name }), "."));
    body.appendChild(el("p", { class: "muted", text: "Share this code. Anyone signed in can join with it:" }));
    const row = el("div", { class: "codebox" }, el("code", { text: room.code }),
      el("button", { class: "btn ghost", type: "button", text: "Copy link", onclick: async () => {
        const link = new URL("playground.html", location.href); link.search = "?room=" + room.code;
        try { await navigator.clipboard.writeText(link.href); say("Link copied."); } catch (e) { say(link.href); } } }));
    body.appendChild(row);
    body.appendChild(el("button", { class: "btn ghost", type: "button", text: room.owner ? "Close this shared program" : "Leave", onclick: leave }));
    body.appendChild(el("p", { class: "muted", text: "Everyone sees the same program. Press Run to run your own copy of it. It is saved while you work, so it is still there when you come back with the code." }));
  }
  const note = (t) => { const n = $("c-note"); if (n) n.textContent = t; else say(t); };

  // ---------------- people bar ----------------
  function paintBar(list) {
    bar.textContent = "";
    if (!room) { bar.hidden = true; return; }
    bar.hidden = false;
    const chip = (name, colour, extra) => bar.appendChild(el("span", { class: "who", style: "--c:" + colour }, el("i", {}), el("b", { text: name }), extra ? el("small", { text: extra }) : ""));
    chip("You", me.colour);
    list.forEach((p) => chip(p.name, p.colour, p.typing ? "typing…" : (p.line ? "line " + p.line : "")));
  }

  // ---------------- room ----------------
  async function libs() {
    if (!Yjs) Yjs = await import(YJS);
    if (!window.HLCollabCore) throw new Error("collab-core.js did not load");
    sb = await HLAccount.client();
  }

  async function start(name) {
    try {
      await libs();
      const { data, error } = await sb.from("rooms").insert({ owner_id: me.id, name: name || "Shared program", content: code.value }).select("id,code,name,owner_id").single();
      if (error) throw error;
      await enter(Object.assign(data, { owner: true }), true);
    } catch (e) { note("Could not start: " + (e.message || e)); }
  }
  async function join(codeText) {
    if (joining) return; joining = true;
    try {
      const c = (codeText || "").trim().toUpperCase();
      if (!/^[0-9A-F]{8}$/.test(c)) throw new Error("A code is 8 letters and numbers, like 7F3A9C21.");
      await libs();
      const { data, error } = await sb.rpc("join_room", { room_code: c });
      if (error) throw error;
      const r = Array.isArray(data) ? data[0] : data;
      const { data: full, error: e2 } = await sb.from("rooms").select("id,code,name,owner_id").eq("id", r.id).single();
      if (e2) throw e2;
      await enter(Object.assign(full, { owner: full.owner_id === me.id }), false);
    } catch (e) { note(e.message || String(e)); } finally { joining = false; }
  }

  async function enter(r, iCreated) {
    if (room) await leave(true);
    room = r;
    const { data: row } = await sb.from("rooms").select("content").eq("id", r.id).single();
    const dbText = row ? row.content : "";
    core = HLCollabCore.create({
      Y: Yjs, textarea: code, overlay: remote, me,
      send: (m) => { if (channel) channel.send({ type: "broadcast", event: "m", payload: { from: me.id, m } }); if (m.t === "u") soon(); },
    });
    core.onPeers(paintBar);
    channel = sb.channel("room:" + r.id, { config: { private: true, broadcast: { self: false }, presence: { key: me.id } } });
    channel.on("broadcast", { event: "m" }, ({ payload }) => { if (payload && payload.from !== me.id) { core.receive(payload.m, payload.from); if (payload.m && payload.m.t === "u") { soonSave(); } } });
    channel.on("presence", { event: "sync" }, () => {
      const state = channel.presenceState(); presenceIds = new Set(Object.keys(state));
      core.peers.forEach((_, id) => { if (!presenceIds.has(id)) core.forget(id); });
      paintBar(Array.from(core.peers, ([id, p]) => ({ id, name: p.name, colour: p.colour, line: null, typing: p.typing })));
    });
    channel.on("presence", { event: "join" }, () => core.announce(true));
    await new Promise((resolve) => {
      channel.subscribe(async (status) => {
        if (status === "SUBSCRIBED") { await channel.track({ name: me.display_name, colour: me.colour }); resolve(); }
        if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") { note("Could not connect to the live session."); resolve(); }
      });
    });
    // someone already here has the live text; if nobody answers, this is the first copy: start from the saved text
    const others = Object.keys(channel.presenceState()).filter((k) => k !== me.id).length;
    const hadState = new Promise((res) => { const t = setTimeout(() => res(false), others ? 2500 : 0); core.doc.once("update", () => { clearTimeout(t); res(true); }); });
    if (others) core.hello();
    if (!(others && await hadState)) core.seed(iCreated ? code.value : dbText, !others);
    core.announce(true);
    say("Shared program: " + r.name);
    $("filetab").textContent = r.name;
    btn.textContent = "Shared";
    btn.classList.add("on");
    panel(); paintBar([]);
    history.replaceState(null, "", "?room=" + r.code);
  }

  function soon() { soonSave(); }
  function soonSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(save, 4000);
  }
  async function save() {
    if (!room || !core) return;
    await sb.from("rooms").update({ content: core.text(), updated_at: new Date().toISOString() }).eq("id", room.id);
  }

  async function leave(quiet) {
    clearTimeout(saveTimer);
    if (room && core) { try { await save(); } catch (e) { /* ok */ } }
    const was = room;
    if (channel) { try { await sb.removeChannel(channel); } catch (e) { /* ok */ } channel = null; }
    if (core) { core.destroy(); core = null; }
    if (was && !quiet) {
      if (was.owner) await sb.from("rooms").delete().eq("id", was.id); else await sb.from("room_members").delete().eq("room_id", was.id).eq("user_id", me.id);
    }
    room = null; bar.hidden = true; bar.textContent = ""; remote.textContent = "";
    $("filetab").textContent = "main.hum"; btn.textContent = "Collaborate"; btn.classList.remove("on");
    history.replaceState(null, "", location.pathname);
    panel();
  }

  btn.onclick = () => { drawer.hidden = !drawer.hidden; if (!drawer.hidden) { const n = $("nina"); if (n) n.hidden = true; panel(); } };

  async function init() {
    if (!window.HLAccount || !HLAccount.configured) return;
    HLAccount.onChange(async (p) => { me = p ? Object.assign({}, p, { id: p.id, name: p.display_name }) : null; if (!me && room) await leave(true); panel(); });
    try { const p = await HLAccount.profile(); if (p) me = Object.assign({}, p, { name: p.display_name }); } catch (e) { /* signed out */ }
    const want = new URLSearchParams(location.search).get("room");
    if (want) { drawer.hidden = false; if (me) { panel(); join(want); } else { try { sessionStorage.setItem("hl-return", location.href); } catch (e) { /* ok */ } panel(); } }
  }
  window.addEventListener("pagehide", () => { if (room) save(); });
  init();
})();

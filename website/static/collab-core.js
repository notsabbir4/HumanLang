/* Shared coding: the part that does not need a server. It keeps a textarea in step with other people's copies of the
   same text (using Yjs), and draws where they are and what they just typed. Nothing here knows about the network:
   it is given a `send` function and is told what arrives. */
(function (root) {
  "use strict";
  const b64 = (u8) => { let s = ""; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000)); return btoa(s); };
  const unb64 = (s) => { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; };
  const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const lineOf = (text, i) => { let n = 1; for (let k = 0; k < i && k < text.length; k++) if (text.charCodeAt(k) === 10) n++; return n; };
  const EDIT_FADE = 3000, PEER_GONE = 15000, MAX_PEERS = 12;

  function create(opts) {
    const { Y, textarea, me, send, overlay } = opts;
    const doc = new Y.Doc(), ytext = doc.getText("code");
    const peers = new Map();            // id -> { name, colour, a, b (relative positions), typing, seen }
    const edits = [];                   // recent changes by other people: { id, from, to, at }
    let applying = false, myRel = null, typingUntil = 0, listeners = [];

    // ---- the first copy of the text must be identical for everyone, so it is made with a fixed author number ----
    function seed(text) {
      const real = doc.clientID; doc.clientID = 1;
      doc.transact(() => { if (text) ytext.insert(0, text); }, "seed");
      doc.clientID = real;
      show(ytext.toString());
    }

    function rel(i) { return Y.createRelativePositionFromTypeIndex(ytext, Math.max(0, Math.min(i, ytext.length))); }
    function abs(r) { try { const p = Y.createAbsolutePositionFromRelativePosition(r, doc); return p && p.type === ytext ? p.index : null; } catch (e) { return null; } }
    function remember() { myRel = { a: rel(textarea.selectionStart), b: rel(textarea.selectionEnd) }; }

    // text on screen := the shared text, keeping my own cursor where it was
    function show(text) {
      applying = true;
      const sx = textarea.scrollLeft, sy = textarea.scrollTop;
      let a = textarea.selectionStart, b = textarea.selectionEnd;
      if (myRel) { const na = abs(myRel.a), nb = abs(myRel.b); if (na !== null) a = na; if (nb !== null) b = nb; }
      textarea.value = text;
      try { textarea.setSelectionRange(Math.min(a, text.length), Math.min(b, text.length)); } catch (e) { /* not focused: fine */ }
      textarea.scrollLeft = sx; textarea.scrollTop = sy;
      applying = false;
      remember();
      textarea.dispatchEvent(new Event("input", { bubbles: true }));
    }

    // my typing := the smallest change between the shared text and what is on screen
    function onInput() {
      if (applying) return;
      const old = ytext.toString(), now = textarea.value;
      if (old === now) return;
      let p = 0; const max = Math.min(old.length, now.length);
      while (p < max && old.charCodeAt(p) === now.charCodeAt(p)) p++;
      let s = 0;
      while (s < max - p && old.charCodeAt(old.length - 1 - s) === now.charCodeAt(now.length - 1 - s)) s++;
      doc.transact(() => {
        if (old.length - p - s > 0) ytext.delete(p, old.length - p - s);
        if (now.length - p - s > 0) ytext.insert(p, now.slice(p, now.length - s));
      }, "local");
      typingUntil = Date.now() + 1500;
      remember(); announce();
    }

    ytext.observe((ev, tr) => {
      if (tr.origin === "local" || tr.origin === "seed") return;
      let pos = 0;
      for (const d of ev.delta) {                 // remember what the other person just typed (to colour it for a moment)
        if (d.retain) pos += d.retain;
        else if (d.insert) { edits.push({ id: tr.origin && tr.origin.from || "?", from: pos, to: pos + d.insert.length, at: Date.now() }); pos += d.insert.length; }
      }
      show(ytext.toString());
    });
    doc.on("update", (u, origin) => { if (origin !== "seed" && !(origin && origin.remote)) send({ t: "u", d: b64(u) }); });

    // ---- what arrives from other people ----
    function receive(m, from) {
      if (!m || typeof m !== "object") return;
      if (m.t === "u" && typeof m.d === "string") { Y.applyUpdate(doc, unb64(m.d), { remote: true, from }); }
      else if (m.t === "need") send({ t: "state", to: from, d: b64(Y.encodeStateAsUpdate(doc)) });
      else if (m.t === "state" && m.to === me.id && typeof m.d === "string") { Y.applyUpdate(doc, unb64(m.d), { remote: true, from }); }
      else if (m.t === "aw" && from !== me.id) {
        if (!peers.has(from) && peers.size >= MAX_PEERS) return;
        peers.set(from, { name: String(m.name || "Someone").slice(0, 40), colour: /^#[0-9a-f]{6}$/i.test(m.colour) ? m.colour : "#888888",
                          a: m.a, b: m.b, typing: !!m.typing, seen: Date.now() });
        changed();
      }
    }

    let last = 0, timer = null;
    function announce(force) {
      const now = Date.now();
      if (!force && now - last < 120) { if (!timer) timer = setTimeout(() => { timer = null; announce(true); }, 130); return; }
      last = now;
      if (!myRel) remember();
      send({ t: "aw", name: me.name, colour: me.colour, a: myRel.a, b: myRel.b, typing: now < typingUntil });
    }
    function changed() { render(); listeners.forEach((f) => f(list())); }
    function list() {
      const text = ytext.toString(), out = [];
      peers.forEach((p, id) => { const i = p.a ? abs(p.a) : null; out.push({ id, name: p.name, colour: p.colour, line: i === null ? null : lineOf(text, i), typing: p.typing && Date.now() - p.seen < 2500 }); });
      return out;
    }

    // ---- drawing other people's cursors, selections and fresh typing over the editor ----
    function layer(cls, colour) {
      const el = document.createElement("pre");
      el.className = "rpeer " + cls; el.setAttribute("aria-hidden", "true"); el.style.setProperty("--c", colour);
      return el;
    }
    function render() {
      if (!overlay) return;
      const text = textarea.value, now = Date.now(), frag = document.createDocumentFragment();
      peers.forEach((p, id) => {
        if (now - p.seen > PEER_GONE) { peers.delete(id); return; }
        const a = p.a ? abs(p.a) : null, b = p.b ? abs(p.b) : null;
        if (a === null) return;
        const lo = Math.min(a, b === null ? a : b), hi = Math.max(a, b === null ? a : b);
        const sel = layer("rsel", p.colour);
        sel.innerHTML = esc(text.slice(0, lo)) + (hi > lo ? "<mark>" + esc(text.slice(lo, hi)) + "</mark>" : "") + esc(text.slice(hi)) + "\n";
        frag.appendChild(sel);
        const car = layer("rcar", p.colour);
        car.innerHTML = esc(text.slice(0, b === null ? a : b)) + '<span class="rc"><i class="rl">' + esc(p.name) + "</i></span>" + "\n";
        frag.appendChild(car);
      });
      for (let i = edits.length - 1; i >= 0; i--) if (now - edits[i].at > EDIT_FADE) edits.splice(i, 1);
      const byId = new Map();
      edits.forEach((e) => { (byId.get(e.id) || byId.set(e.id, []).get(e.id)).push(e); });
      byId.forEach((list2, id) => {                // only still-valid ranges: positions are as they were when typed, so show them while fresh
        const p = peers.get(id); if (!p) return;
        const el = layer("redit", p.colour); let html = "", at = 0;
        list2.sort((x, y) => x.from - y.from).forEach((e) => {
          const f = Math.max(at, Math.min(e.from, text.length)), t = Math.max(f, Math.min(e.to, text.length));
          html += esc(text.slice(at, f)) + "<mark>" + esc(text.slice(f, t)) + "</mark>"; at = t;
        });
        el.innerHTML = html + esc(text.slice(at)) + "\n"; frag.appendChild(el);
      });
      overlay.textContent = ""; overlay.appendChild(frag);
      overlay.scrollTop = textarea.scrollTop; overlay.scrollLeft = textarea.scrollLeft;
      overlay.querySelectorAll(".rpeer").forEach((el) => { el.scrollTop = textarea.scrollTop; el.scrollLeft = textarea.scrollLeft; });
    }
    const tick = setInterval(() => { if (peers.size || edits.length) { render(); listeners.forEach((f) => f(list())); } }, 400);
    const heartbeat = setInterval(() => announce(true), 5000);

    const onSel = () => { if (!applying) { remember(); announce(); } };
    textarea.addEventListener("input", onInput);
    document.addEventListener("selectionchange", onSel);
    textarea.addEventListener("scroll", render);

    return {
      doc, ytext, seed, receive, announce, peers,
      text: () => ytext.toString(),
      hello: () => send({ t: "need" }),
      forget(id) { peers.delete(id); changed(); },
      onPeers(f) { listeners.push(f); },
      destroy() {
        clearInterval(tick); clearInterval(heartbeat); clearTimeout(timer);
        textarea.removeEventListener("input", onInput); document.removeEventListener("selectionchange", onSel);
        textarea.removeEventListener("scroll", render);
        if (overlay) overlay.textContent = "";
        doc.destroy();
      },
    };
  }
  root.HLCollabCore = { create, lineOf };
})(typeof window !== "undefined" ? window : globalThis);

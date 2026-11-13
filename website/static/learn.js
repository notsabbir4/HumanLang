/* Beginner+ as an interactive course. All the thinking is in learn-core.js; this file is the screens.
   Progress is kept in this browser only (localStorage). Everything still works when saving is not allowed. */
(function () {
  "use strict";
  const L = window.LearnCore;
  const root = document.getElementById("learn");
  if (!root || !L) return;
  const data = JSON.parse(document.getElementById("learn-data").textContent);
const Snd = window.HLSound || { play() {}, isMuted: () => true, setMuted() {} };
  const KEY = "hl-beginner", COURSE = "beginner-plus", PASS = 60;
  const unitsById = {}; data.units.forEach((u) => (unitsById[u.n] = u));

  // ---- saving ---------------------------------------------------------------------------------------
  function fresh() { return { v: 1, stats: L.newStats(), units: {}, exam: { best: null, tries: 0, grade: null, score: null }, name: "", seen: [] }; }
  let S = fresh();
  try { const x = JSON.parse(localStorage.getItem(KEY) || "null"); if (x && x.v === 1) S = Object.assign(fresh(), x); } catch (e) { /* no saving: fine */ }
  function unitState(n) { return S.units[n] || (S.units[n] = { parts: [], test: null }); }
  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(S));
      const all = JSON.parse(localStorage.getItem("hl-progress") || "{}") || {};
      all[COURSE] = data.units.filter((u) => (unitState(u.n).test || 0) >= PASS).map((u) => u.n);
      localStorage.setItem("hl-progress", JSON.stringify(all));
    } catch (e) { /* ignore */ }
  }
  const unitDone = (u) => (S.units[u.n] && S.units[u.n].test != null && S.units[u.n].test >= PASS);
  const allUnitsDone = () => data.units.every(unitDone);

  // ---- tiny helpers ---------------------------------------------------------------------------------
  function h(tag, attrs) {
    const e = document.createElement(tag);
    for (const k in attrs || {}) {
      const v = attrs[k];
      if (k === "class") e.className = v; else if (k === "html") e.innerHTML = v; else if (k === "text") e.textContent = v;
      else if (k.slice(0, 2) === "on") e.addEventListener(k.slice(2), v); else if (v !== false && v != null) e.setAttribute(k, v === true ? "" : v);
    }
    for (let i = 2; i < arguments.length; i++) { const c = arguments[i]; if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); }
    return e;
  }
  const codeBox = (html, label) => h("div", { class: "box code lbox", html: (label ? '<span class="tag">' + label + "</span>" : "") + "<pre><code>" + html + "</code></pre>" });
  const textBox = (text, cls, label) => { const b = h("div", { class: "box " + cls }); if (label) b.appendChild(h("span", { class: "tag", text: label })); const p = h("pre"); p.appendChild(h("code", { text })); b.appendChild(p); return b; };
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const skillName = (s) => data.skills[s] || s;
  function show(node) { root.innerHTML = ""; root.appendChild(node); window.scrollTo(0, 0); }
  const pctOf = (a, b) => (b ? Math.round((100 * a) / b) : 0);

  // ---- one exercise on the screen ---------------------------------------------------------------------
  // returns {node, get(), ready(), lock(result)}; onChange tells the player the answer may be ready
  function renderEx(ex, onChange, onEnter) {
    const wrap = h("div", { class: "ex" });
    let ans = null, locked = false;
    const set = (v) => { ans = v; onChange(); };
    const q = (t) => wrap.appendChild(h("p", { class: "q", text: t }));
    const typed = ex.inputs && ex.inputs.length && !/types?:/i.test(ex.q || "");
    const inputBox = () => typed && wrap.appendChild(textBox(ex.inputs.join("\n"), "input", "The person types"));
    let lock = () => { locked = true; };
    let ready = () => ans !== null && ans !== "";
    const KIND = { predict: "What will it show?", trace: "Follow the program", choose: "Question", type: "Type the output", fill: "Fill the gap", order: "Put in order", bug: "Find the bug", write: "Write a line" };
    wrap.appendChild(h("p", { class: "kind", text: KIND[ex.kind] }));

    if (ex.options) {
      if (ex.kind === "trace") q(ex.q || "After the last line has run, what is inside " + ex.var + "?");
      else q(ex.q || (ex.error ? "What does HL say?" : ex.kind === "choose" ? "" : "What does this program show?"));
      if (ex.html) wrap.appendChild(codeBox(ex.html));
      inputBox();
      const order = L.shuffle(ex.options.map((o, i) => i));
      const list = h("div", { class: "opts", role: "group" });
      const btns = order.map((i) => {
        const b = h("button", { type: "button", class: "opt" }, h("code", { text: ex.options[i].t === "" ? "(nothing)" : ex.options[i].t }));
        b.addEventListener("click", () => { if (locked) return; btns.forEach((x) => x.classList.remove("sel")); b.classList.add("sel"); Snd.play("tap"); set(i); });
        list.appendChild(b); return b;
      });
      wrap.appendChild(list);
      lock = (res) => { locked = true; btns.forEach((b, k) => { b.disabled = true; if (ex.options[order[k]].ok) b.classList.add("good"); else if (b.classList.contains("sel")) b.classList.add("bad"); }); };
    } else if (ex.kind === "type") {
      q(ex.q || "What does this program show?");
      wrap.appendChild(codeBox(ex.html)); inputBox();
      const ta = h("textarea", { class: "typed", rows: Math.max(2, ex.answer.split("\n").length), spellcheck: "false", autocapitalize: "off", autocomplete: "off", "aria-label": "Your answer", placeholder: "Type exactly what appears on the screen" });
      ta.addEventListener("input", () => set(ta.value.trim() ? ta.value : null));
      wrap.appendChild(ta);
      if (ex.inputs && ex.inputs.length) wrap.appendChild(h("p", { class: "tiny", text: "The screen also shows each question and what the person typed, like: Name? Sam" }));
      lock = () => { locked = true; ta.disabled = true; };
    } else if (ex.kind === "fill") {
      q(ex.q || "Fill the gap so the program works.");
      const gap = h("input", { class: "gap", type: "text", spellcheck: "false", autocapitalize: "off", autocomplete: "off", "aria-label": "The missing part", size: 8 });
      gap.addEventListener("input", () => set(gap.value.trim() ? gap.value : null));
      gap.addEventListener("keydown", (e) => { if (e.key === "Enter") onEnter(); });
      const box = codeBox(ex.html.replace("___", '<span data-gap></span>'));
      box.querySelector("[data-gap]").replaceWith(gap);
      wrap.appendChild(box); inputBox();
      lock = () => { locked = true; gap.disabled = true; };
    } else if (ex.kind === "order") {
      q(ex.q || "Put the lines in the right order.");
      let mix; do { mix = L.shuffle(ex.lines); } while (ex.lines.length > 1 && mix.join("\n") === ex.lines.join("\n"));
      const pool = h("div", { class: "tiles pool" }), done = h("div", { class: "tiles done" });
      let placed = [];
      const tile = (line, id) => h("button", { type: "button", class: "tile", "data-id": id }, h("code", { text: line }));
      const refresh = () => { ans = placed.length === ex.lines.length ? placed.map((p) => p.line) : null; onChange(); };
      const tiles = mix.map((line, id) => {
        const t = tile(line, id);
        t.addEventListener("click", () => {
          if (locked) return;
          const i = placed.findIndex((p) => p.id === id);
          Snd.play("tap"); if (i >= 0) { placed.splice(i, 1); pool.appendChild(t); } else { placed.push({ id, line }); done.appendChild(t); }
          done.classList.toggle("has", placed.length > 0); refresh();
        });
        pool.appendChild(t); return t;
      });
      wrap.appendChild(h("p", { class: "tiny", text: "Tap the lines in order. Tap a placed line to take it back." }));
      wrap.appendChild(done); wrap.appendChild(pool);
      if (ex.inputs && ex.inputs.length) inputBox();
      lock = () => { locked = true; tiles.forEach((t) => (t.disabled = true)); };
    } else if (ex.kind === "bug") {
      q(ex.q || "Tap the line that has the mistake.");
      if (ex.goal && !ex.q) { wrap.appendChild(textBox(ex.goal, "output", "It should show")); }
      inputBox();
      const list = h("div", { class: "buglines" });
      const rows = ex.lines.map((line, i) => {
        const b = h("button", { type: "button", class: "bugline" }, h("span", { class: "gut", text: String(i + 1) }), h("code", { text: line || " " }));
        b.addEventListener("click", () => { if (locked) return; rows.forEach((r) => r.classList.remove("sel")); b.classList.add("sel"); Snd.play("tap"); set(i + 1); });
        list.appendChild(b); return b;
      });
      wrap.appendChild(list);
      lock = () => { locked = true; rows.forEach((r, i) => { r.disabled = true; if (i + 1 === ex.bad) r.classList.add("good"); else if (r.classList.contains("sel")) r.classList.add("bad"); }); };
    } else if (ex.kind === "write") {
      q(ex.task);
      if (ex.ctx_html) wrap.appendChild(codeBox(ex.ctx_html, "Already written"));
      inputBox();
      const inp = h("input", { class: "writeline", type: "text", spellcheck: "false", autocapitalize: "off", autocomplete: "off", autocorrect: "off", "aria-label": "Your line of HumanLang", placeholder: "Type your line here" });
      inp.addEventListener("input", () => set(inp.value.trim() ? inp.value : null));
      inp.addEventListener("keydown", (e) => { if (e.key === "Enter") onEnter(); });
      wrap.appendChild(inp);
      lock = () => { locked = true; inp.disabled = true; };
    }
    const focus = wrap.querySelector("input,textarea");
    return { node: wrap, get: () => ans, ready: () => ready(), lock, focus: () => focus && focus.focus({ preventScroll: true }) };
  }

  // ---- the player: a list of exercises, one at a time -------------------------------------------------
  // cfg: {title, items, requeue, feedback, teach, onDone(summary), onQuit}
  function play(cfg) {
    let queue = cfg.items.slice(), pos = 0, firstTry = {}, requeued = {}, right = 0, miss = [], answered = {};
    const total = cfg.items.length;
    const fb = cfg.feedback !== false;
    const bar = h("i"), count = h("span", { class: "pcount" });
    const body = h("div", { class: "pbody" });
    const banner = h("div", { class: "banner", "aria-live": "polite" });
    const main = h("button", { type: "button", class: "btn big pmain" });
    const quit = h("button", { type: "button", class: "pquit", "aria-label": "Leave this lesson", title: "Leave", text: "✕", onclick: () => { if (window.confirm("Leave? Your answers in this round will not be counted.")) cfg.onQuit(); } });
    const screen = h("div", { class: "player" },
      h("div", { class: "ptop" }, quit, h("div", { class: "pbar" }, bar), count, soundBtn()),
      body, h("div", { class: "pfoot" }, banner, main));
    show(screen);
    document.onkeydown = (e) => { if (e.key === "Enter" && !e.shiftKey && e.target.tagName !== "TEXTAREA" && !main.disabled && e.target.tagName !== "BUTTON") { e.preventDefault(); main.click(); } };
    const progress = () => { const n = Object.keys(answered).length; bar.style.width = pctOf(n, total) + "%"; count.textContent = n + " / " + total; };

    function teachCard(then) {
      body.innerHTML = ""; banner.className = "banner"; banner.innerHTML = "";
      const card = h("div", { class: "teach", html: cfg.teach });
      body.appendChild(h("p", { class: "kind", text: cfg.title })); body.appendChild(card);
      main.textContent = "Got it! Let's practise"; main.disabled = false; main.onclick = then; bar.style.width = "0%"; count.textContent = "0 / " + total;
      window.scrollTo(0, 0); main.focus();
    }

    function next() {
      if (pos >= queue.length) { document.onkeydown = null; return finish(); }
      const ex = queue[pos];
      body.innerHTML = ""; banner.className = "banner"; banner.innerHTML = ""; body.dataset.ex = ex.id;
      const view = renderEx(ex, () => { main.disabled = !view.ready(); }, () => { if (view.ready() && !main.disabled) main.click(); });
      body.appendChild(view.node);
      main.textContent = fb ? "Check" : "Lock in"; main.disabled = true; main.className = "btn big pmain";
      progress(); window.scrollTo(0, 0);
      setTimeout(() => view.focus(), 30);
      main.onclick = () => {
        const res = L.check(ex, view.get());
        const first = !(ex.id in firstTry);
        if (first) { firstTry[ex.id] = res.ok; answered[ex.id] = true; if (res.ok) right++; else miss.push({ ex, res }); L.record(S.stats, ex, res); }
        else if (res.ok) L.record(S.stats, ex, res);
        progress(); save();
        if (!fb) { pos++; return next(); }
        view.lock(res);
        const good = res.ok;
        Snd.play(good ? "right" : "wrong");
        banner.className = "banner " + (good ? "good" : "bad");
        banner.innerHTML = "";
        banner.appendChild(h("b", { text: good ? ["Correct!", "Nice!", "Yes!", "Well done!"][Math.floor(Math.random() * 4)] : "Not quite" }));
        if (!good) {
          banner.appendChild(h("div", { class: "ans" }, h("span", { text: "Answer: " }), h("code", { text: res.right == null || res.right === "" ? "(nothing)" : res.right })));
          banner.appendChild(h("p", { text: ex.why }));
          const tip = res.tag && data.tags[res.tag];
          if (tip && tip !== ex.why) banner.appendChild(h("p", { class: "tip", text: "Tip: " + tip }));
          if (cfg.requeue && (requeued[ex.id] || 0) < 2) { requeued[ex.id] = (requeued[ex.id] || 0) + 1; queue.push(ex); }
        }
        main.textContent = "Continue"; main.className = "btn big pmain " + (good ? "good" : "bad");
        main.onclick = () => { Snd.play("next"); pos++; next(); }; main.focus();
      };
    }

    function finish() {
      cfg.onDone({ right, total, pct: pctOf(right, total), miss });
    }
    if (cfg.teach) teachCard(next); else next();
  }

  // ---- mistakes: what to tell the person -----------------------------------------------------------------
  function mistakeBlock(miss) {
    if (!miss.length) return h("p", { class: "perfect", text: "No mistakes. Perfect round!" });
    const tips = [], seen = {}, skills = {};
    miss.forEach((m) => {
      skills[m.ex.skill] = (skills[m.ex.skill] || 0) + 1;
      const t = (m.res.tag && data.tags[m.res.tag]) || m.ex.why;
      if (!seen[t]) { seen[t] = 1; tips.push(t); }
    });
    const box = h("div", { class: "mistakes" }, h("h3", { text: "Where you slipped" }));
    const sk = h("p", { class: "skillchips" });
    Object.keys(skills).forEach((s) => sk.appendChild(h("span", { class: "chip", text: skillName(s) + (skills[s] > 1 ? " x" + skills[s] : "") })));
    box.appendChild(sk);
    const ul = h("ul"); tips.slice(0, 5).forEach((t) => ul.appendChild(h("li", { text: t }))); box.appendChild(ul);
    return box;
  }
  function soundBtn() {
    const b = h("button", { type: "button", class: "soundbtn", "aria-label": "Sound effects" });
    const paint = () => { const off = Snd.isMuted(); b.textContent = off ? "🔇" : "🔊"; b.title = off ? "Sound is off. Tap to turn it on" : "Sound is on. Tap to turn it off"; b.setAttribute("aria-pressed", String(!off)); };
    b.addEventListener("click", () => { Snd.setMuted(!Snd.isMuted()); paint(); Snd.play("tap"); });
    paint(); return b;
  }
  function btnRow() { const r = h("div", { class: "btnrow" }); for (let i = 0; i < arguments.length; i++) if (arguments[i]) r.appendChild(arguments[i]); return r; }
  const btn = (text, fn, cls) => h("button", { type: "button", class: "btn " + (cls || ""), text, onclick: fn });

  // ---- screens --------------------------------------------------------------------------------------------
  function pathScreen() {
    document.onkeydown = null;
    const weak = L.weakSkills(S.stats, 5);
    const doneN = data.units.filter(unitDone).length;
    const el = h("div", { class: "learn" });
    el.appendChild(h("div", { class: "lhead" }, h("div", { class: "lhtop" }, h("h1", { text: "Beginner+" }), soundBtn()),
      h("p", { class: "lead", text: "Short lessons, quick questions, and a test after every unit. Your mistakes decide what you practise next. At the end you get a grade and a certificate." }),
      h("div", { class: "pbar wide", role: "progressbar", "aria-valuemin": 0, "aria-valuemax": data.units.length, "aria-valuenow": doneN }, h("i", { style: "width:" + pctOf(doneN, data.units.length) + "%" })),
      h("p", { class: "tiny", text: doneN + " of " + data.units.length + " units passed" })));
    if (weak.length) {
      el.appendChild(h("div", { class: "weak" }, h("b", { text: "Your weak spots: " }), h("span", { text: weak.map(skillName).join(", ") }),
        btnRow(btn("Practise my weak spots", startPractice, "good"))));
    }
    const path = h("ol", { class: "upath" });
    let nextUnit = data.units.find((u) => !unitDone(u));
    data.units.forEach((u) => {
      const st = unitState(u.n), done = unitDone(u);
      const dots = h("span", { class: "dots", "aria-hidden": "true" });
      u.parts.forEach((p, i) => dots.appendChild(h("i", { class: st.parts[i] ? "on" : "" })));
      const stat = done ? h("span", { class: "badge ok", text: "Test " + st.test + "%" }) : st.test != null ? h("span", { class: "badge", text: "Test " + st.test + "% · retry" }) : null;
      path.appendChild(h("li", { class: (done ? "udone " : "") + (nextUnit === u ? "unow" : "") },
        h("button", { type: "button", class: "unitcard", onclick: () => unitScreen(u) },
          h("span", { class: "un", text: done ? "✓" : String(u.n) }),
          h("span", { class: "ut" }, h("b", { text: u.title }), h("small", { text: u.blurb }), dots),
          stat, h("span", { class: "go", text: nextUnit === u ? "Start" : done ? "Review" : "Open" }))));
    });
    const ok = allUnitsDone(), ex = S.exam;
    path.appendChild(h("li", { class: "exam" + (ok ? "" : " locked") },
      h("button", { type: "button", class: "unitcard", disabled: !ok, onclick: examIntro },
        h("span", { class: "un", text: "★" }),
        h("span", { class: "ut" }, h("b", { text: "Final exam" }), h("small", { text: ok ? "25 questions from the whole course. It gives you your grade and certificate." : "Pass every unit test (" + PASS + "% or more) to open the exam." })),
        ex.grade ? h("span", { class: "badge " + (L.passed(ex.grade) ? "ok" : ""), text: ex.grade + " · " + ex.score + "%" }) : null,
        h("span", { class: "go", text: ok ? (ex.tries ? "Again" : "Start") : "Locked" }))));
    el.appendChild(path);
    if (ex.grade && L.passed(ex.grade)) el.appendChild(h("div", { class: "certcard" }, h("div", {}, h("b", { text: "You passed with grade " + ex.grade + "." }), h("p", { class: "tiny", text: "Your certificate is ready." })), btnRow(btn("See my certificate", certScreen, "good"))));
    el.appendChild(h("p", { class: "tiny foot" }, h("a", { href: "tutorial-all.html", text: "Read all chapters as plain pages" }), " · ",
      h("a", { href: "#", text: "Start over", onclick: (e) => { e.preventDefault(); if (window.confirm("Delete all your progress in Beginner+?")) { S = fresh(); save(); pathScreen(); } } })));
    show(el);
  }

  function unitScreen(u) {
    const st = unitState(u.n), el = h("div", { class: "learn" });
    el.appendChild(h("nav", { class: "crumbs" }, h("a", { href: "#", text: "Beginner+", onclick: (e) => { e.preventDefault(); pathScreen(); } }), " › Unit " + u.n));
    el.appendChild(h("h1", { text: "Unit " + u.n + ": " + u.title }));
    el.appendChild(h("p", { class: "lead", text: u.blurb }));
    const list = h("ol", { class: "upath parts" });
    let firstOpen = u.parts.findIndex((p, i) => !st.parts[i]);
    u.parts.forEach((p, i) => {
      list.appendChild(h("li", { class: st.parts[i] ? "udone" : firstOpen === i ? "unow" : "" },
        h("button", { type: "button", class: "unitcard", onclick: () => partRun(u, i) },
          h("span", { class: "un", text: st.parts[i] ? "✓" : String(i + 1) }),
          h("span", { class: "ut" }, h("b", { text: p.title }), h("small", { text: p.ex.length + " questions" })),
          h("span", { class: "go", text: st.parts[i] ? "Again" : "Start" }))));
    });
    const ready = st.parts.filter(Boolean).length === u.parts.length;
    list.appendChild(h("li", { class: "exam" + (ready ? "" : " locked") },
      h("button", { type: "button", class: "unitcard", disabled: !ready, onclick: () => testRun(u) },
        h("span", { class: "un", text: "?" }),
        h("span", { class: "ut" }, h("b", { text: "Unit test" }), h("small", { text: ready ? "A short test on this unit. Your mistakes decide what you practise next." : "Finish the parts above first." })),
        st.test != null ? h("span", { class: "badge " + (st.test >= PASS ? "ok" : ""), text: st.test + "%" }) : null,
        h("span", { class: "go", text: ready ? (st.test != null ? "Again" : "Start") : "Locked" }))));
    el.appendChild(list);
    show(el);
  }

  function partRun(u, pi) {
    const part = u.parts[pi];
    play({
      title: "Unit " + u.n + ": " + part.title, teach: part.teach, items: part.ex, requeue: true,
      onQuit: () => unitScreen(u),
      onDone: (r) => {
        const st = unitState(u.n); st.parts[pi] = true; save();
        // a part that went badly gets a short extra round on the same skills
        if (r.pct < 67) {
          const more = L.extra(data, part, 3, []);
          if (more.length) {
            const el = h("div", { class: "learn center" }, h("h2", { text: "Let's practise that a little more" }),
              h("p", { class: "lead", text: "You got " + r.right + " of " + r.total + " right the first time. That is fine. A few more questions on the same ideas will make it stick." }),
              mistakeBlock(r.miss), btnRow(btn("Practise", () => play({ title: "Extra practice", items: more, requeue: true, onQuit: () => unitScreen(u), onDone: (r2) => partDone(u, pi, r2, true) }), "big good")));
            return show(el);
          }
        }
        partDone(u, pi, r, false);
      },
    });
  }
  function partDone(u, pi, r, extra) {
    Snd.play(r.pct === 100 ? "perfect" : "part");
    const last = pi === u.parts.length - 1;
    const el = h("div", { class: "learn center" }, h("h2", { text: extra ? "Better!" : r.pct === 100 ? "Perfect!" : "Part complete" }),
      h("p", { class: "bigscore", text: r.right + " / " + r.total }), h("p", { class: "tiny", text: "right the first time" }), mistakeBlock(r.miss),
      btnRow(last ? btn("On to the unit test", () => testRun(u), "big good") : btn("Next part", () => partRun(u, pi + 1), "big good"), btn("Back to the unit", () => unitScreen(u), "ghost")));
    show(el);
  }

  function testRun(u) {
    play({
      title: "Unit " + u.n + " test", items: L.unitTest(u), requeue: false,
      onQuit: () => unitScreen(u),
      onDone: (r) => {
        const st = unitState(u.n); st.test = Math.max(st.test == null ? -1 : st.test, r.pct); save();
        const pass = r.pct >= PASS, weak = L.weakSkills(S.stats, 4);
        Snd.play(!pass ? "fail" : r.pct === 100 ? "perfect" : "pass");
        const el = h("div", { class: "learn center" }, h("h2", { text: pass ? (r.pct === 100 ? "Perfect test!" : "Unit " + u.n + " passed") : "Not quite there yet" }),
          h("p", { class: "bigscore", text: r.pct + "%" }), h("p", { class: "tiny", text: r.right + " of " + r.total + " right" }),
          h("p", { class: "lead", text: pass ? (weak.length ? "Good. A little practice on your weak spots will make you even stronger." : "You are doing very well.") : "You need " + PASS + "% to pass. Practise your mistakes, then try the test again." }),
          mistakeBlock(r.miss));
        const nx = unitsById[u.n + 1];
        el.appendChild(btnRow(
          weak.length ? btn("Practise my mistakes", startPractice, pass ? "big" : "big good") : null,
          pass && nx ? btn("Next unit", () => unitScreen(nx), "big good") : null,
          pass && !nx ? btn("Back to the path", pathScreen, "big good") : null,
          !pass ? btn("Try the test again", () => testRun(u), weak.length ? "" : "big good") : null,
          btn("Back to the path", pathScreen, "ghost")));
        show(el);
      },
    });
  }

  // practice built from the person's own mistakes
  function startPractice() {
    const items = L.practice(data, S.stats, 8, S.seen.slice(-40));
    const list = items.length ? items : L.practice(data, S.stats, 8, []);
    if (!list.length) return pathScreen();
    list.forEach((e) => S.seen.push(e.id)); S.seen = S.seen.slice(-80);
    const names = Array.from(new Set(list.map((e) => skillName(e.skill)))).join(", ");
    play({
      title: "Practice: " + names, items: list, requeue: true, onQuit: pathScreen,
      onDone: (r) => {
        save();
        const weak = L.weakSkills(S.stats, 4);
        Snd.play(weak.length ? "part" : "pass");
        const el = h("div", { class: "learn center" }, h("h2", { text: weak.length ? "Good work" : "Weak spots fixed!" }),
          h("p", { class: "bigscore", text: r.right + " / " + r.total }), h("p", { class: "tiny", text: "right the first time" }),
          h("p", { class: "lead", text: weak.length ? "Still to practise: " + weak.map(skillName).join(", ") + "." : "Nothing is weak right now. Nice." }), mistakeBlock(r.miss),
          btnRow(weak.length ? btn("More practice", startPractice, "big good") : null, btn("Back to the path", pathScreen, weak.length ? "ghost" : "big good")));
        show(el);
      },
    });
  }

  function examIntro() {
    const el = h("div", { class: "learn center" }, h("h1", { text: "Final exam" }),
      h("p", { class: "lead", text: "25 questions from the whole course. There is no feedback until the end, so take your time. Your grade is 60% this exam and 40% your unit tests." }),
      h("ul", { class: "gradetable" }, ...[["A+", "97 – 100"], ["A", "93 – 96"], ["A-", "90 – 92"], ["B", "80 – 89"], ["C", "70 – 79"], ["D", "60 – 69"], ["F", "below 60: fail"]].map((g) => h("li", {}, h("b", { text: g[0] }), " " + g[1]))),
      btnRow(btn("Start the exam", examRun, "big good"), btn("Not yet", pathScreen, "ghost")));
    show(el);
  }
  function examRun() {
    const items = L.examQuestions(data, null, S.exam.lastIds || []);
    play({
      title: "Final exam", items, requeue: false, feedback: false, onQuit: pathScreen,
      onDone: (r) => {
        const unitBest = data.units.map((u) => unitState(u.n).test);
        const score = L.finalScore(r.pct, unitBest), grade = L.letter(score);
        S.exam.tries++; S.exam.lastIds = items.map((e) => e.id);
        if (S.exam.score == null || score >= S.exam.score) { S.exam.date = null; S.exam.best = r.pct; S.exam.score = score; S.exam.grade = grade; }
        save();
        const pass = L.passed(grade);
        Snd.play(pass ? "grade" : "fail");
        const el = h("div", { class: "learn center" }, h("h2", { text: pass ? "You passed!" : "Not passed this time" }),
          h("div", { class: "grade g" + grade.replace("+", "p").replace("-", "m") }, h("span", { text: grade })),
          h("p", { class: "bigscore", text: score + "%" }), h("p", { class: "tiny", text: "Exam " + r.pct + "% (" + r.right + " of " + r.total + ") · unit tests average " + Math.round(unitBest.reduce((a, b) => a + (b || 0), 0) / unitBest.length) + "%" }),
          h("p", { class: "lead", text: pass ? "Well done. Your certificate is ready." : "Below 60% is a fail, but nothing is lost. Practise your weak spots, then take the exam again with new questions." }),
          mistakeBlock(r.miss),
          btnRow(pass ? btn("Get my certificate", certScreen, "big good") : btn("Practise my mistakes", startPractice, "big good"), btn(pass ? "Try for a better grade" : "Take the exam again", examIntro, "ghost"), btn("Back to the path", pathScreen, "ghost")));
        show(el);
      },
    });
  }

  // ---- the certificate ----------------------------------------------------------------------------------------
  function certData() {
    const ex = S.exam, unitBest = data.units.map((u) => unitState(u.n).test || 0);
    return { name: S.name.trim(), grade: ex.grade, score: ex.score, exam: ex.best, units: Math.round(unitBest.reduce((a, b) => a + b, 0) / unitBest.length), date: S.exam.date || new Date().toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" }) };
  }
  function certScreen() {
    if (!S.exam.grade || !L.passed(S.exam.grade)) return pathScreen();
    if (!S.exam.date) { S.exam.date = new Date().toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" }); save(); }
    const el = h("div", { class: "learn" });
    el.appendChild(h("nav", { class: "crumbs" }, h("a", { href: "#", text: "Beginner+", onclick: (e) => { e.preventDefault(); pathScreen(); } }), " › Certificate"));
    const name = h("input", { type: "text", class: "writeline", maxlength: 40, placeholder: "Your name", "aria-label": "Your name", value: S.name });
    const holder = h("div", { class: "certhold" });
    const draw = () => { holder.innerHTML = ""; const d = certData(); holder.appendChild(certHtml(d)); dl.disabled = pr.disabled = !d.name; };
    const dl = btn("Download certificate (PNG)", () => downloadPng(certData()), "good"), pr = btn("Print / save as PDF", () => window.print());
    name.addEventListener("input", () => { S.name = name.value; save(); draw(); });
    el.appendChild(h("h1", { text: "Your certificate" }));
    el.appendChild(h("label", { class: "namefield" }, h("span", { text: "Type your name as it should appear:" }), name));
    el.appendChild(holder); el.appendChild(btnRow(dl, pr, btn("Back", pathScreen, "ghost")));
    el.appendChild(h("p", { class: "tiny", text: "This certificate is made by the HumanLang website, in your browser. It shows what you did in the course. It is not an official qualification." }));
    show(el); draw();
  }
  function certHtml(d) {
    const c = document.createElement("canvas"); c.id = "cert"; c.className = "certcanvas"; c.setAttribute("role", "img");
    c.setAttribute("aria-label", "Certificate for " + (d.name || "your name") + ", Beginner+, grade " + d.grade);
    c.width = window.HLCertificate.W; c.height = window.HLCertificate.H;
    window.HLCertificate.ready((tpl) => { if (tpl) window.HLCertificate.draw(c, d, tpl); });
    return c;
  }
  function downloadPng(d) {
    window.HLCertificate.ready((tpl) => {
      if (!tpl) return window.alert("The certificate picture could not load. Check your connection and try again.");
      const c = document.createElement("canvas");
      window.HLCertificate.draw(c, d, tpl);
      c.toBlob((b) => { const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "humanlang-beginner-plus-certificate.png"; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000); });
    });
  }

  pathScreen();
})();

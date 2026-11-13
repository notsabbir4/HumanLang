(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const COLOURS = ["#6ea8ff", "#ff6b6b", "#ffb454", "#ffd93d", "#6bd98a", "#2dd4bf", "#b794ff", "#ff7ac6", "#9aa5b1", "#f97316"];
  const BADGES = ["", "🚀", "🎮", "🧩", "🌟", "🔥", "🐱", "🦊", "🌈", "💡", "🎨", "🎵", "🛰️", "🧠"];
  let profile = null, colour = "#6ea8ff", badge = "";

  function swatches() {
    const c = $("p-colours"), b = $("p-badges"); c.textContent = ""; b.textContent = "";
    COLOURS.forEach((v) => { const el = document.createElement("button"); el.type = "button"; el.className = "sw" + (v === colour ? " on" : ""); el.style.background = v; el.setAttribute("aria-label", "Colour " + v); el.onclick = () => { colour = v; swatches(); card(); }; c.appendChild(el); });
    BADGES.forEach((v) => { const el = document.createElement("button"); el.type = "button"; el.className = "sw badge" + (v === badge ? " on" : ""); el.textContent = v || "none"; el.onclick = () => { badge = v; swatches(); card(); }; b.appendChild(el); });
  }
  function card() {
    const box = $("pcard"); box.textContent = "";
    const live = Object.assign({}, profile, { display_name: $("p-name").value || "Coder", colour, badge, avatar_url: $("p-photo").checked ? (profile && profile.photo) : null });
    box.style.borderColor = colour;
    box.appendChild(HLAccount.avatar(live, 56));
    const t = document.createElement("div"); t.className = "pc-text";
    const n = document.createElement("strong"); n.textContent = (badge ? badge + " " : "") + live.display_name; t.appendChild(n);
    const g = document.createElement("span"); g.className = "muted"; g.textContent = profile && profile.github_login ? "@" + profile.github_login : ""; t.appendChild(g);
    const bio = document.createElement("p"); bio.textContent = $("p-bio").value; t.appendChild(bio);
    if ($("p-fav").value) { const f = document.createElement("small"); f.textContent = "Favourite: " + $("p-fav").value; t.appendChild(f); }
    box.appendChild(t);
  }

  async function rooms(c) {
    const ul = $("rooms"); ul.textContent = "";
    const { data, error } = await c.from("rooms").select("id,code,name,owner_id,updated_at").order("updated_at", { ascending: false }).limit(20);
    if (error || !data || !data.length) { const li = document.createElement("li"); li.className = "muted"; li.textContent = error ? "Could not load them." : "None yet. Open the Playground and press Collaborate."; ul.appendChild(li); return; }
    data.forEach((r) => {
      const li = document.createElement("li"), a = document.createElement("a");
      a.href = "playground.html?room=" + encodeURIComponent(r.code); a.textContent = r.name; li.appendChild(a);
      const code = document.createElement("code"); code.textContent = r.code; li.appendChild(code);
      ul.appendChild(li);
    });
  }

  async function savedList(c) {
    const ul = $("saved"); ul.textContent = "";
    const { data, error } = await c.from("saved_programs").select("id,name,kind,updated_at").order("updated_at", { ascending: false }).limit(100);
    if (error || !data || !data.length) { const li = document.createElement("li"); li.className = "muted"; li.textContent = error ? "Could not load them." : "Nothing saved yet."; ul.appendChild(li); return; }
    data.forEach((r) => {
      const li = document.createElement("li"), a = document.createElement("a");
      a.href = "playground.html#saved=" + encodeURIComponent(r.id); a.textContent = r.name; li.appendChild(a);
      const t = document.createElement("span"); t.className = "muted"; t.textContent = new Date(r.updated_at).toLocaleDateString(); li.appendChild(t);
      const d = document.createElement("a"); d.href = "#"; d.textContent = "Delete"; d.className = "del";
      d.onclick = async (e) => { e.preventDefault(); if (!confirm('Delete "' + r.name + '"? This cannot be undone.')) return; await c.from("saved_programs").delete().eq("id", r.id); savedList(c); };
      li.appendChild(d); ul.appendChild(li);
    });
  }

  // Beginner+ progress, from the account (or this browser if nothing is saved in the account yet)
  async function courses(c) {
    const box = $("courses"); if (!box || !window.LearnCore) return;
    let st = null, from = "";
    try { const { data } = await c.from("course_progress").select("data").eq("course", "beginner-plus").maybeSingle(); if (data) { st = data.data; from = "account"; } } catch (e) { /* offline */ }
    try { const local = JSON.parse(localStorage.getItem("hl-beginner") || "null"); if (local && local.v === 1) { st = LearnCore.merge(local, st); from = from || "browser"; } } catch (e) { /* none */ }
    const sum = LearnCore.summary(st, 10);
    box.textContent = "";
    const card = document.createElement("div"); card.className = "ccard";
    const t = document.createElement("strong"); t.textContent = "Beginner+"; card.appendChild(t);
    const bar = document.createElement("div"); bar.className = "pbar wide"; const i = document.createElement("i"); i.style.width = Math.round(sum.passed * 10) + "%"; bar.appendChild(i); card.appendChild(bar);
    const line = document.createElement("p"); line.className = "muted";
    line.textContent = !sum.started ? "Not started yet." : sum.passed + " of " + sum.total + " units passed" + (sum.grade ? " · Final grade " + sum.grade + (sum.score != null ? " (" + sum.score + "%)" : "") : "");
    card.appendChild(line);
    const a = document.createElement("a"); a.className = "btn run"; a.href = "course-beginner-plus.html";
    a.textContent = sum.certificate ? "See my certificate" : sum.started ? "Continue (unit " + sum.next + ")" : "Start Beginner+";
    card.appendChild(a); box.appendChild(card);
  }

  async function show() {
    if (!HLAccount.configured) { $("acct-out").hidden = false; $("signin").disabled = true; $("acct-note").textContent = "Accounts are not switched on for this site yet."; return; }
    let s = null;
    try { s = await HLAccount.session(); } catch (e) { /* offline */ }
    if (!s) { $("acct-out").hidden = false; $("acct-in").hidden = true; return; }
    // coming back from GitHub: go back to where the person was
    try { const back = sessionStorage.getItem("hl-return"); if (back) { sessionStorage.removeItem("hl-return"); if (new URL(back).origin === location.origin && !/account\.html/.test(back)) { location.replace(back); return; } } } catch (e) { /* stay here */ }
    $("acct-out").hidden = true; $("acct-in").hidden = false;
    profile = await HLAccount.profile(true);
    if (!profile) { $("pcard").textContent = "Your profile is not ready yet. Reload in a moment."; return; }
    profile.photo = s.user.user_metadata && /^https:\/\//.test(s.user.user_metadata.avatar_url || "") ? s.user.user_metadata.avatar_url : null;
    $("p-name").value = profile.display_name; $("p-bio").value = profile.bio; $("p-fav").value = profile.favourite;
    $("p-photo").checked = !!profile.avatar_url; $("p-photo").disabled = !profile.photo;
    colour = profile.colour; badge = profile.badge; swatches(); card();
    ["p-name", "p-bio", "p-fav", "p-photo"].forEach((id) => $(id).addEventListener("input", card));
    const c = await HLAccount.client(); rooms(c); savedList(c); courses(c);
  }

  $("signin").onclick = async () => { try { await HLAccount.signIn(); } catch (e) { $("acct-note").textContent = "Could not start sign-in: " + (e.message || e); } };
  $("signout").onclick = async () => { await HLAccount.signOut(); location.reload(); };
  $("pform").onsubmit = async (e) => {
    e.preventDefault();
    const c = await HLAccount.client(), s = await HLAccount.session();
    const row = { display_name: $("p-name").value.trim() || "Coder", bio: $("p-bio").value.trim(), favourite: $("p-fav").value.trim(), colour, badge,
                  avatar_url: $("p-photo").checked ? profile.photo : null, updated_at: new Date().toISOString() };
    const { error } = await c.from("profiles").update(row).eq("id", s.user.id);
    $("p-status").textContent = error ? "Could not save: " + error.message : "Saved.";
    if (!error) { await HLAccount.profile(true); location.reload(); }
  };
  show();
})();

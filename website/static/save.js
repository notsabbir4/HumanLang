/* Playground: download your program as a .hum file, and save it to your account (sign in with GitHub). */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const code = $("code"), dlBtn = $("dlbtn"), saveBtn = $("savebtn");
  if (!code || !dlBtn || !saveBtn) return;
  let saved = null;                                  // { id, name } once this program lives in the account
  const say = (t) => { const s = $("status"); if (s) s.textContent = t; };
  const clean = (n) => (n || "").replace(/\.hum$/i, "").replace(/[^\w\- ]+/g, "").trim().slice(0, 60);
  const fileName = () => (clean(saved && saved.name) || clean($("examples") && $("examples").value) || "my-program") + ".hum";
  const touch = () => code.dispatchEvent(new Event("input", { bubbles: true }));

  dlBtn.onclick = () => {
    const blob = new Blob([code.value.replace(/\r?\n/g, "\n")], { type: "text/plain;charset=utf-8" });
    const a = document.createElement("a"), url = URL.createObjectURL(blob);
    a.href = url; a.download = fileName(); document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    say("Downloaded " + a.download);
  };

  // a small box that asks for the name
  const dlg = document.createElement("dialog"); dlg.className = "askbox";
  dlg.innerHTML = '<form method="dialog"><h3>Save to your account</h3><label>Name <input id="sv-name" maxlength="60" required autocomplete="off"></label>' +
    '<p class="muted" id="sv-note"></p><div class="row"><button class="btn run" value="ok">Save</button><button class="btn ghost" value="cancel" formnovalidate>Cancel</button></div></form>';
  document.body.appendChild(dlg);
  const ask = (name, note) => new Promise((res) => {
    $("sv-name").value = name; $("sv-note").textContent = note || "";
    dlg.onclose = () => res(dlg.returnValue === "ok" ? clean($("sv-name").value) : null);
    dlg.returnValue = ""; if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    $("sv-name").focus(); $("sv-name").select();
  });

  async function save() {
    if (!window.HLAccount || !HLAccount.configured) { say("Saving needs accounts, which are not switched on here."); return; }
    let s = null; try { s = await HLAccount.session(); } catch (e) { /* offline */ }
    if (!s) {
      say("Sign in with GitHub to save your program on the website.");
      try { sessionStorage.setItem("hl-draft", code.value); } catch (e) { /* fine */ }
      try { await HLAccount.signIn(); } catch (e) { say("Could not start sign-in: " + (e.message || e)); }
      return;
    }
    const c = await HLAccount.client();
    let name = saved ? saved.name : null;
    if (!name) { name = await ask(clean($("examples") && $("examples").value) || "My program", "Saved programs are private to you. Find them on your Account page."); if (!name) return; }
    saveBtn.disabled = true; say("Saving...");
    const { data, error } = await c.from("saved_programs").upsert({ user_id: s.user.id, kind: "program", name, code: code.value }, { onConflict: "user_id,kind,name" }).select("id,name").single();
    saveBtn.disabled = false;
    if (error) { say("Could not save: " + error.message); return; }
    saved = { id: data.id, name: data.name }; say("Saved as \"" + data.name + "\". It is on your Account page.");
    history.replaceState(null, "", location.pathname + "#saved=" + data.id);
  }
  saveBtn.onclick = save;

  // opening a saved program (from the Account page), or a draft kept while signing in
  async function openSaved() {
    const id = new URLSearchParams(location.hash.slice(1)).get("saved");
    if (!id || !window.HLAccount || !HLAccount.configured) return;
    say("Opening your saved program...");
    try {
      const s = await HLAccount.session(); if (!s) { say("Sign in to open your saved programs."); return; }
      const c = await HLAccount.client();
      const { data, error } = await c.from("saved_programs").select("id,name,code").eq("id", id).maybeSingle();
      if (error || !data) { say("I could not find that saved program."); return; }
      saved = { id: data.id, name: data.name }; code.value = data.code; touch(); say("Opened \"" + data.name + "\".");
    } catch (e) { say("I could not open it (offline?)."); }
  }
  function backFromSignIn() {
    try { const d = sessionStorage.getItem("hl-draft"); if (d && !location.hash) { sessionStorage.removeItem("hl-draft"); code.value = d; touch(); say("Welcome back. Press Save again."); } } catch (e) { /* fine */ }
  }
  setTimeout(() => { openSaved(); backFromSignIn(); }, 300);
})();

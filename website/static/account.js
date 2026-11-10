/* The website account: sign in with GitHub (through Supabase). Loaded on every page; it only downloads the sign-in
   library when someone is signed in, or asks to sign in. */
(function () {
  "use strict";
  const CFG = window.HL_SUPABASE;
  const LIB = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.6/+esm";
  let clientPromise = null, listeners = [], current = { session: null, profile: null };

  const storedSession = () => {
    try { for (let i = 0; i < localStorage.length; i++) if (/^sb-.*-auth-token$/.test(localStorage.key(i))) return true; } catch (e) { /* no storage */ }
    return false;
  };

  function client() {
    if (!CFG || !CFG.url) return Promise.reject(new Error("Accounts are not set up on this site."));
    if (!clientPromise) {
      clientPromise = import(LIB).then((m) => m.createClient(CFG.url, CFG.key, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, flowType: "pkce" } }));
    }
    return clientPromise;
  }

  async function session() { const c = await client(); const { data } = await c.auth.getSession(); return data.session; }

  async function profile(force) {
    if (current.profile && !force) return current.profile;
    const c = await client(), s = await session();
    if (!s) return null;
    let { data } = await c.from("profiles").select("*").eq("id", s.user.id).maybeSingle();
    if (!data) {                           // the account was made a moment ago: the profile row can take a second
      await new Promise((r) => setTimeout(r, 900));
      ({ data } = await c.from("profiles").select("*").eq("id", s.user.id).maybeSingle());
    }
    current.profile = data;
    return data;
  }

  async function signIn() {
    const c = await client();
    try { sessionStorage.setItem("hl-return", location.href); } catch (e) { /* fine */ }
    const { error } = await c.auth.signInWithOAuth({ provider: "github", options: { redirectTo: new URL("account.html", location.href).href } });
    if (error) throw error;
  }
  async function signOut() {
    const c = await client(); await c.auth.signOut(); current = { session: null, profile: null };
    paintChip(null); listeners.forEach((f) => f(null));
  }

  function initials(name) { return (name || "?").trim().slice(0, 1).toUpperCase(); }
  function avatar(p, size) {
    const el = document.createElement("span");
    el.className = "avatar"; el.style.cssText = `width:${size}px;height:${size}px;background:${(p && p.colour) || "#6ea8ff"}`;
    if (p && p.avatar_url) { const im = document.createElement("img"); im.src = p.avatar_url; im.alt = ""; im.referrerPolicy = "no-referrer"; el.appendChild(im); }
    else el.textContent = p && p.badge ? p.badge : initials(p && p.display_name);
    return el;
  }

  function paintChip(p) {
    const chip = document.getElementById("acct"); if (!chip) return;
    chip.textContent = "";
    if (!p) { chip.textContent = "Sign in"; chip.classList.remove("in"); return; }
    chip.classList.add("in"); chip.appendChild(avatar(p, 24));
    const t = document.createElement("span"); t.textContent = p.display_name; chip.appendChild(t);
  }

  async function boot() {
    if (!CFG || !storedSession() && !/[?&]code=/.test(location.search)) return;
    try {
      const c = await client();
      c.auth.onAuthStateChange(async (ev, s) => {
        if (ev === "SIGNED_OUT") { current = { session: null, profile: null }; paintChip(null); listeners.forEach((f) => f(null)); }
        if (ev === "SIGNED_IN" || ev === "TOKEN_REFRESHED") { current.session = s; }
      });
      const p = await profile(true); paintChip(p); listeners.forEach((f) => f(p));
    } catch (e) { /* offline or blocked: the page still works, just signed out */ }
  }

  window.HLAccount = { client, session, profile, signIn, signOut, avatar, onChange: (f) => listeners.push(f), configured: !!(CFG && CFG.url) };
  boot();
})();

(function () {
  const $ = (id) => document.getElementById(id);
  const C = window.HL_COMMUNITY, L = window.HLCommunity;
  const officialNames = new Map(C.official.map((a) => [a.login.toLowerCase(), a]));
  const banned = new Set(C.banned.map((b) => b.toLowerCase()));
  let posts = [], category = "All", query = "", live = false;
  const calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const TICK = '<svg class="tick" viewBox="0 0 24 24" role="img" aria-label="Official HumanLang profile"><title>Official HumanLang profile</title><path fill="#1d9bf0" d="M22.5 12.5l-2.2-2.5.3-3.3-3.2-.8-1.7-2.8-3 1.3-3-1.3-1.7 2.8-3.2.8.3 3.3L1.5 12.5l2.2 2.5-.3 3.3 3.2.8 1.7 2.8 3-1.3 3 1.3 1.7-2.8 3.2-.8-.3-3.3z"/><path fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" d="M7.8 12.4l2.9 2.9 5.6-5.8"/></svg>';
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function who(p) {
    const o = officialNames.get(p.author.toLowerCase());
    const name = o ? o.name : p.author;
    const link = `https://github.com/${encodeURIComponent(p.author)}`;
    return `<a class="by" href="${link}" rel="noopener"><img src="${esc(o && o.avatar ? o.avatar : p.avatar)}" alt="" width="24" height="24" loading="lazy"><span>${esc(name)}</span>${o ? TICK : ""}</a>`;
  }
  function team(p) {
    return p.together.length ? `<span class="with">with ${p.together.map((n) => `<a href="https://github.com/${encodeURIComponent(n)}" rel="noopener">@${esc(n)}</a>`).join(", ")}</span>` : "";
  }
  function ago(iso) {
    const d = new Date(iso), days = Math.round((Date.now() - d) / 864e5);
    return days < 1 ? "today" : days === 1 ? "yesterday" : days < 30 ? days + " days ago" : d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  }

  // ---- code with colours (a small copy of the website's highlighter) ----
  const KW = new RegExp("\\b(" + C.keywords.sort((a, b) => b.length - a.length).map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")\\b", "g");
  function paint(line) {
    if (/^\s*note:/.test(line)) return `<span class="c">${esc(line)}</span>`;
    const parts = line.split(/("(?:\\.|[^"\\])*")/);
    return parts.map((t, i) => i % 2 ? `<span class="s">${esc(t)}</span>`
      : esc(t).replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="n">$1</span>').replace(KW, '<span class="k">$1</span>')).join("");
  }
  const listing = (code) => `<ol class="listing">${code.split("\n").map((l, i) => `<li>${paint(l) || " "}</li>`).join("")}</ol>`;

  // ---- the list ----
  // the 4:5 picture of a post: the poster's thumbnail, or one we make from the title
  function thumb(p) {
    if (p.thumb) return `<span class="thumb"><img src="${esc(p.thumb)}" alt="" loading="lazy" referrerpolicy="no-referrer"></span>`;
    const hue = (p.id * 47) % 360, words = p.title.split(/\s+/).filter(Boolean);
    const initials = (words.length > 1 ? words[0][0] + words[1][0] : (words[0] || "?").slice(0, 2)).toUpperCase();
    return `<span class="thumb gen" style="--h:${hue}"><b>${esc(initials)}</b><i>${esc(p.category)}</i></span>`;
  }
  function card(p) {
    return `<article class="post${officialNames.has(p.author.toLowerCase()) ? " official" : ""}">
<a class="thumb-link" href="#${p.id}" aria-label="Open post #${p.id}">${thumb(p)}</a>
<header><a class="pid" href="#${p.id}" title="Post ID">#${p.id}</a><span class="cat">${esc(p.category)}</span></header>
<h3><a href="#${p.id}">${esc(p.title)}</a></h3>
<p class="desc">${esc(p.description.length > 170 ? p.description.slice(0, 170).trim() + "..." : p.description)}</p>
<footer>${who(p)}${team(p)}<span class="when">${ago(p.date)}</span></footer></article>`;
  }
  function visible() {
    const q = query.trim().toLowerCase().replace(/^#/, "");
    return posts.filter((p) => !banned.has(p.author.toLowerCase())
      && (category === "All" || (category === "From HumanLang" ? officialNames.has(p.author.toLowerCase()) : p.category === category))
      && (!q || String(p.id) === q || (p.title + " " + p.description + " " + p.author + " " + p.category).toLowerCase().includes(q)));
  }
  function renderList() {
    const list = visible();
    $("posts").innerHTML = list.length ? list.map(card).join("") : '<p class="empty">Nothing here yet. Be the first to post something in this category!</p>';
    $("count").textContent = list.length + (list.length === 1 ? " post" : " posts");
  }
  function chips() {
    const cats = ["All", "From HumanLang", ...C.categories];
    $("chips").innerHTML = cats.map((c) => `<button type="button" class="chip${c === category ? " on" : ""}" data-c="${esc(c)}">${esc(c)}</button>`).join("");
    for (const b of $("chips").querySelectorAll(".chip")) b.onclick = () => { category = b.dataset.c; chips(); renderList(); };
  }

  // ---- one post ----
  async function showPost(id) {
    const box = $("detail");
    $("browse").hidden = true; box.hidden = false; window.scrollTo(0, 0);
    box.innerHTML = `<p><a href="#" class="back">&larr; All posts</a></p><p class="status">Looking for post #${esc(id)}...</p>`;
    let p = posts.find((x) => String(x.id) === String(id));
    if (!p) {
      try {
        const issue = await L.getIssue(id);
        if (!issue) { box.innerHTML = `<p><a href="#" class="back">&larr; All posts</a></p><h2>Post #${esc(id)}</h2><p>There is no community post with this ID.</p>`; return; }
        p = L.parse(issue);
      } catch (e) {
        box.innerHTML = `<p><a href="#" class="back">&larr; All posts</a></p><p>I could not reach GitHub just now (${esc(e.message)}). Try again in a minute, or open <a href="https://github.com/${L.REPO}/issues/${esc(id)}">the post on GitHub</a>.</p>`;
        return;
      }
    }
    document.title = `#${p.id} ${p.title} - HumanLang Community`;
    if (banned.has(p.author.toLowerCase()) || p.labels.includes("removed")) {
      box.innerHTML = `<p><a href="#" class="back">&larr; All posts</a></p><h2>Post #${p.id}</h2><p>This post was removed by a moderator.</p>`; return;
    }
    if (!p.verified) {
      box.innerHTML = `<p><a href="#" class="back">&larr; All posts</a></p><h2>Post #${p.id}</h2><p>This post is not published yet: ${p.labels.includes("possible-copy") ? "a moderator is checking it." : p.labels.includes("needs-fix") ? "it needs a fix (the bot wrote what to change on the post)." : "the bot is still checking it. Come back in a few minutes."}</p>`;
      return;
    }
    const official = officialNames.has(p.author.toLowerCase());
    box.innerHTML = `<p><a href="#" class="back">&larr; All posts</a></p>
<article class="post big${official ? " official" : ""}">
<div class="big-thumb">${thumb(p)}</div>
<header><span class="pid">Post ID #${p.id}</span><span class="cat">${esc(p.category)}</span></header>
<h2>${esc(p.title)}</h2>
<footer class="meta">${who(p)}${team(p)}<span class="when">${ago(p.date)}</span></footer>
${p.writes ? '<p class="warn"><strong>Heads up:</strong> this program writes to files on your computer when you run it.</p>' : ""}
<div class="body">${esc(p.description).replace(/\n/g, "<br>")}</div>
<p class="actions"><a class="btn run" href="playground.html#post=${p.id}">Run it in the Playground</a>
<button class="btn ghost" id="copy" type="button">Copy the code</button>
<a class="btn ghost" href="${esc(p.url)}" rel="noopener">Comments on GitHub (${p.comments})</a></p>
<h3>The code</h3>${listing(p.code)}</article>`;
    $("copy").onclick = async (e) => {
      try { await navigator.clipboard.writeText(p.code); e.target.textContent = "Copied!"; } catch (err) { e.target.textContent = "Select the code and copy it"; }
      setTimeout(() => (e.target.textContent = "Copy the code"), 1800);
    };
  }

  function route() {
    const h = location.hash.slice(1).replace(/^#?/, "");
    if (/^\d+$/.test(h)) showPost(h);
    else { $("detail").hidden = true; $("browse").hidden = false; document.title = "Community - HumanLang"; if (h === "rules") $("rules").scrollIntoView(); }
  }

  // ---- go ----
  $("find").onsubmit = (e) => {
    e.preventDefault();
    const v = $("findid").value.trim().replace(/^#/, "");
    if (/^\d+$/.test(v)) location.hash = v; else { query = v; renderList(); }
  };
  $("q").oninput = () => { query = $("q").value; renderList(); };
  window.addEventListener("hashchange", route);
  chips();
  posts = C.snapshot.map((i) => L.parse(i)).filter((p) => p.verified);
  renderList(); route();
  L.getPosts().then((issues) => {
    posts = issues.map((i) => L.parse(i)).filter((p) => p.verified);
    live = true; $("note").textContent = ""; renderList();
    if (/^\d+$/.test(location.hash.slice(1))) route();
  }).catch(() => { $("note").textContent = "Showing the last saved list (GitHub did not answer, so the newest posts may be missing)."; });
})();

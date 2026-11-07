/* Reading a community post (a GitHub issue made with the "Community post" form). Shared by the Community page and the Playground. */
(function (root) {
  "use strict";
  const REPO = "notsabbir4/HumanLang";
  const HIDE = ["removed", "banned", "possible-copy", "needs-fix"];

  function fields(body) {
    const out = {}; let name = null, buf = [];
    for (const line of String(body || "").replace(/\r\n/g, "\n").split("\n")) {
      const m = line.match(/^###\s+(.*?)\s*$/);
      if (m) { if (name !== null) out[name] = buf.join("\n").trim(); name = m[1]; buf = []; }
      else buf.push(line);
    }
    if (name !== null) out[name] = buf.join("\n").trim();
    return out;
  }
  function codeOf(text) {
    const m = /```[ \t]*\w*[ \t]*\n([\s\S]*?)\n?```/.exec(text || "");
    return (m ? m[1] : text || "").replace(/^\n+|\n+$/g, "");
  }
  function people(text) {
    const t = String(text || "").replace(/_No response_/g, "");
    return (t.match(/@?[A-Za-z0-9][A-Za-z0-9-]{0,38}/g) || []).map((p) => p.replace(/^@/, ""))
      .filter((p) => !["and", "no", "none", "nobody", "me"].includes(p.toLowerCase()));
  }
  function parse(issue) {
    const f = fields(issue.body), names = (issue.labels || []).map((l) => l.name);
    return {
      id: issue.number, title: String(issue.title || "").replace(/^Post:\s*/i, ""), author: issue.user.login,
      avatar: issue.user.avatar_url, date: issue.created_at, updated: issue.updated_at, url: issue.html_url,
      category: f["Category"] || "Other", description: (f["What is it? (describe your work)"] || "").replace(/_No response_/g, ""),
      code: codeOf(f["Your HumanLang code"]), together: people(f["Made together with (optional)"]), labels: names,
      verified: names.includes("verified-hl") && !names.some((n) => HIDE.includes(n)), writes: names.includes("writes-files"),
      comments: issue.comments || 0,
    };
  }
  async function getIssue(n) {
    const r = await fetch(`https://api.github.com/repos/${REPO}/issues/${encodeURIComponent(n)}`, { headers: { Accept: "application/vnd.github+json" } });
    if (r.status === 404) return null;
    if (!r.ok) throw new Error("GitHub said " + r.status);
    const issue = await r.json();
    if (issue.pull_request || !(issue.labels || []).some((l) => l.name === "community")) return null;
    return issue;
  }
  async function getPosts() {
    const out = [];
    for (let page = 1; page <= 5; page++) {
      const r = await fetch(`https://api.github.com/repos/${REPO}/issues?labels=community,verified-hl&state=open&per_page=100&page=${page}`,
        { headers: { Accept: "application/vnd.github+json" } });
      if (!r.ok) throw new Error("GitHub said " + r.status);
      const batch = await r.json();
      out.push(...batch.filter((i) => !i.pull_request));
      if (batch.length < 100) break;
    }
    return out;
  }
  root.HLCommunity = { REPO, fields, codeOf, people, parse, getIssue, getPosts };
})(window);

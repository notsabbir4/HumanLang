/* Home page: a button that takes you back into the course you were doing, with your progress.
   It uses this browser's saved progress; with none, newcomers are offered Beginner+. */
(function () {
  "use strict";
  const box = document.getElementById("home-course");
  if (!box || !window.LearnCore) return;

  function read(co) { try { const x = JSON.parse(localStorage.getItem(co.key) || "null"); return x && x.v === 1 ? x : null; } catch (e) { return null; } }

  function paint(co, sum) {
    box.textContent = "";
    const a = document.createElement("a"); a.className = "hc-link"; a.href = co.file;
    const t = document.createElement("strong"), s = document.createElement("span");
    if (!sum.started) { t.textContent = "Start " + co.name; s.textContent = "A free interactive course with questions, tests, a grade and a certificate."; }
    else if (sum.certificate) { t.textContent = co.name + " complete: grade " + sum.grade; s.textContent = "See your certificate."; }
    else if (sum.allPassed) { t.textContent = "Take the " + co.name + " final exam"; s.textContent = "All " + sum.total + " units passed. One exam to go."; }
    else { t.textContent = "Continue " + co.name; s.textContent = "Unit " + sum.next + " of " + sum.total + " · " + sum.passed + " passed"; }
    a.appendChild(t); a.appendChild(s);
    if (sum.started && !sum.certificate) { const bar = document.createElement("div"); bar.className = "pbar"; const i = document.createElement("i"); i.style.width = Math.round((100 * sum.passed) / sum.total) + "%"; bar.appendChild(i); a.appendChild(bar); }
    box.appendChild(a); box.hidden = false;
  }

  // the course used most recently that is not finished; else the one used most recently; else Beginner+
  const all = LearnCore.COURSES.map((co) => { const st = read(co), sum = LearnCore.summary(st, co.units); return { co, st, sum, t: (st && st.t) || 0 }; });
  const started = all.filter((x) => x.sum.started).sort((a, b) => b.t - a.t);
  const open = started.filter((x) => !x.sum.certificate);
  const pick = open[0] || started[0] || all[0];
  paint(pick.co, pick.sum);

  // nothing in this browser, but signed in: ask the account (only then is the sign-in library loaded)
  const signedIn = (() => { try { for (let i = 0; i < localStorage.length; i++) if (/^sb-.*-auth-token$/.test(localStorage.key(i))) return true; } catch (e) { /* ignore */ } return false; })();
  if (!started.length && signedIn && window.HLAccount && HLAccount.configured) {
    HLAccount.client().then(async (c) => {
      const { data } = await c.from("course_progress").select("course,data");
      const rows = (data || []).map((r) => { const co = LearnCore.COURSES.find((x) => x.id === r.course); return co ? { co, sum: LearnCore.summary(r.data, co.units), t: r.data.t || 0 } : null; }).filter((x) => x && x.sum.started);
      rows.sort((a, b) => (a.sum.certificate - b.sum.certificate) || (b.t - a.t));
      if (rows[0]) paint(rows[0].co, rows[0].sum);
    }).catch(() => { /* offline: keep the default button */ });
  }
})();

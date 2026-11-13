/* Home page: a button that takes you back into the Beginner+ course, with your progress.
   Uses this browser's saved progress; if there is none and you are signed in, it asks your account. */
(function () {
  "use strict";
  const box = document.getElementById("home-course");
  if (!box || !window.LearnCore) return;
  const total = parseInt(box.getAttribute("data-total"), 10) || 10;

  function paint(sum) {
    box.textContent = "";
    const a = document.createElement("a"); a.className = "hc-link"; a.href = "course-beginner-plus.html";
    const t = document.createElement("strong"), s = document.createElement("span");
    if (!sum.started) { t.textContent = "Start Beginner+"; s.textContent = "A free interactive course with questions, tests, a grade and a certificate."; }
    else if (sum.certificate) { t.textContent = "Beginner+ complete: grade " + sum.grade; s.textContent = "See your certificate."; }
    else if (sum.allPassed) { t.textContent = "Take the Beginner+ final exam"; s.textContent = "All " + sum.total + " units passed. One exam to go."; }
    else { t.textContent = "Continue Beginner+"; s.textContent = "Unit " + sum.next + " of " + sum.total + " · " + sum.passed + " passed"; }
    a.appendChild(t); a.appendChild(s);
    if (sum.started && !sum.certificate) { const bar = document.createElement("div"); bar.className = "pbar"; const i = document.createElement("i"); i.style.width = Math.round((100 * sum.passed) / sum.total) + "%"; bar.appendChild(i); a.appendChild(bar); }
    box.appendChild(a); box.hidden = false;
  }

  let st = null;
  try { const x = JSON.parse(localStorage.getItem("hl-beginner") || "null"); if (x && x.v === 1) st = x; } catch (e) { /* no saving */ }
  paint(LearnCore.summary(st, total));

  // nothing in this browser, but signed in: ask the account (only then is the sign-in library loaded)
  const signedIn = (() => { try { for (let i = 0; i < localStorage.length; i++) if (/^sb-.*-auth-token$/.test(localStorage.key(i))) return true; } catch (e) { /* ignore */ } return false; })();
  if (!LearnCore.summary(st, total).started && signedIn && window.HLAccount && HLAccount.configured) {
    HLAccount.client().then(async (c) => {
      const { data } = await c.from("course_progress").select("data").eq("course", "beginner-plus").maybeSingle();
      if (data) paint(LearnCore.summary(data.data, total));
    }).catch(() => { /* offline: keep the default button */ });
  }
})();

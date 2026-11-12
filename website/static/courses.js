/* Course progress is kept in this browser only (localStorage). Everything works without it. */
(function () {
  "use strict";
  const KEY = "hl-progress";
  function load() { try { return JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { return {}; } }
  function save(d) { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) { /* private window: no saving, no problem */ } }
  const data = load();
  const doneOf = (id) => (Array.isArray(data[id]) ? data[id] : []);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));

  // a lesson page: "Next" marks the lesson as done
  const lesson = document.getElementById("lesson");
  if (lesson) {
    const id = lesson.dataset.course, d = doneOf(id);
    $$("[data-lesson]", lesson).forEach((a) => { if (d.indexOf(+a.dataset.lesson) >= 0) a.classList.add("ok"); });
    const next = document.getElementById("next");
    if (next) next.addEventListener("click", () => {
      const k = +next.dataset.done, cur = doneOf(id);
      if (cur.indexOf(k) < 0) cur.push(k);
      data[id] = cur; save(data);
    });
    return;
  }

  // a course page: ticks, and where to continue
  const list = document.getElementById("lessons");
  if (list) {
    const id = list.dataset.course, total = +list.dataset.total, d = doneOf(id);
    $$("li", list).forEach((li) => { if (d.indexOf(+li.dataset.lesson) >= 0) li.classList.add("ok"); });
    let first = 1; while (first <= total && d.indexOf(first) >= 0) first++;
    const btn = document.getElementById("continue");
    if (btn && d.length) {
      if (first > total) { btn.textContent = "Do it again"; btn.href = "lesson-" + id + "-1.html"; }
      else { btn.textContent = "Continue with lesson " + first; btn.href = "lesson-" + id + "-" + first + ".html"; }
    }
    const done = document.getElementById("done");
    if (done && (d.length >= total || location.hash === "#done")) done.hidden = false;
    return;
  }

  // the picker: how far each course is
  $$("a.course[data-course]").forEach((a) => {
    const n = doneOf(a.dataset.course).length, total = +a.dataset.total;
    if (!n) return;
    const p = a.querySelector("[data-prog]"), go = a.querySelector(".cgo");
    if (p) p.textContent = n >= total ? "Finished" : n + " of " + total + " done";
    if (go) go.textContent = n >= total ? "Review →" : "Continue →";
    a.classList.add(n >= total ? "full" : "part");
  });
})();

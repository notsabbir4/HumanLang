/* The thinking behind the Beginner+ course: no page, no storage, so it can be tested on its own.
   Check answers, remember mistakes, pick extra practice, work out the grade. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.LearnCore = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const norm = (s) => String(s == null ? "" : s).replace(/[“”]/g, '"').replace(/[‘’]/g, "'")
    .replace(/ /g, " ").trim().replace(/[ \t]+/g, " ");
  const normLines = (s) => norm(String(s)).split(/\r?\n/).map((l) => l.trim().replace(/[ \t]+/g, " ")).join("\n").trim();

  function matchWrong(list, text) {
    for (const w of list || []) {
      try { if (new RegExp(w[0], "i").test(text)) return w[1]; } catch (e) { /* a bad pattern never breaks the lesson */ }
    }
    return null;
  }

  // answer: a string (typed / filled / written), an option index (predict, trace, choose), a line number (bug), an array of lines (order)
  function check(ex, answer) {
    switch (ex.kind) {
      case "predict": case "trace": case "choose": {
        const o = ex.options[answer];
        return o && o.ok ? { ok: true } : { ok: false, tag: o ? o.tag : null, right: (ex.options.find((x) => x.ok) || {}).t };
      }
      case "type": {
        const ok = normLines(answer) === normLines(ex.answer);
        return ok ? { ok: true } : { ok: false, tag: null, right: ex.answer };
      }
      case "fill": {
        const a = norm(answer);
        if (ex.accept.some((x) => norm(x) === a)) return { ok: true };
        return { ok: false, tag: matchWrong(ex.wrong, a), right: ex.accept[0] };
      }
      case "write": {
        const a = norm(answer);
        if (ex.accept.some((x) => norm(x) === a)) return { ok: true };
        return { ok: false, tag: matchWrong(ex.wrong, a), right: ex.accept[0] };
      }
      case "order": {
        const ok = Array.isArray(answer) && answer.length === ex.lines.length && answer.every((l, i) => l === ex.lines[i]);
        return ok ? { ok: true } : { ok: false, tag: "order-mixed", right: ex.lines.join("\n") };
      }
      case "bug":
        return answer === ex.bad ? { ok: true } : { ok: false, tag: null, right: "line " + ex.bad + ": " + ex.fix };
    }
    return { ok: false };
  }

  // ---- what the person is good and bad at -----------------------------------------------------------
  function newStats() { return { skills: {}, tags: {} }; }
  function skill(stats, s) { return stats.skills[s] || (stats.skills[s] = { right: 0, wrong: 0, need: 0 }); }

  function record(stats, ex, result) {
    const k = skill(stats, ex.skill);
    if (result.ok) { k.right++; k.need = Math.max(0, k.need - 1); }
    else {
      k.wrong++; k.need += 2;
      const t = result.tag || "other";
      stats.tags[t] = (stats.tags[t] || 0) + 1;
    }
  }

  // skills that still need work, the worst first
  function weakSkills(stats, limit) {
    return Object.keys(stats.skills).filter((s) => stats.skills[s].need > 0)
      .sort((a, b) => stats.skills[b].need - stats.skills[a].need).slice(0, limit || 99);
  }

  function shuffle(a, rnd) {
    a = a.slice(); rnd = rnd || Math.random;
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); const t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }

  function allExercises(data) {
    const out = [];
    data.units.forEach((u) => { u.parts.forEach((p) => p.ex.forEach((e) => out.push(e))); u.bank.forEach((e) => out.push(e)); });
    return out;
  }

  // n practice exercises for the weakest skills; never one in `avoid` (ids) unless there is nothing else
  function practice(data, stats, n, avoid, rnd) {
    avoid = avoid || [];
    const weak = weakSkills(stats, 4);
    const pool = allExercises(data);
    let pick = [];
    weak.forEach((s) => { pick = pick.concat(shuffle(pool.filter((e) => e.skill === s && avoid.indexOf(e.id) < 0), rnd)); });
    pick = shuffle(pick, rnd);
    // interleave: take round-robin by skill so one skill does not take over
    const bySkill = {};
    pick.forEach((e) => (bySkill[e.skill] = bySkill[e.skill] || []).push(e));
    const out = [];
    while (out.length < n && Object.keys(bySkill).some((s) => bySkill[s].length)) {
      Object.keys(bySkill).forEach((s) => { if (out.length < n && bySkill[s].length) out.push(bySkill[s].shift()); });
    }
    return out;
  }

  // extra questions on the same skills as a part (used when a part went badly)
  function extra(data, part, n, avoid, rnd) {
    const skills = [];
    part.ex.forEach((e) => { if (skills.indexOf(e.skill) < 0) skills.push(e.skill); });
    const seen = part.ex.map((e) => e.id).concat(avoid || []);
    const pool = shuffle(allExercises(data).filter((e) => skills.indexOf(e.skill) >= 0 && seen.indexOf(e.id) < 0), rnd);
    return pool.slice(0, n);
  }

  function unitTest(unit, rnd) { return shuffle(unit.bank, rnd).slice(0, 8); }

  // 25 questions: every unit gets a fair share (2 or 3), taken from the banks
  function examQuestions(data, rnd, avoid) {
    avoid = avoid || [];
    const per = data.units.map((u) => shuffle(u.bank.filter((e) => avoid.indexOf(e.id) < 0).concat(u.bank.filter((e) => avoid.indexOf(e.id) >= 0)), rnd));
    const out = [];
    for (let round = 0; out.length < 25 && round < 4; round++) {
      per.forEach((q) => { if (out.length < 25 && q[round]) out.push(q[round]); });
    }
    return shuffle(out, rnd);
  }

  // ---- the grade --------------------------------------------------------------------------------------
  function letter(score) {
    if (score >= 97) return "A+";
    if (score >= 93) return "A";
    if (score >= 90) return "A-";
    if (score >= 80) return "B";
    if (score >= 70) return "C";
    if (score >= 60) return "D";
    return "F";
  }
  // 60% final exam + 40% average of the best unit test of every unit
  function finalScore(examPct, unitBest) {
    const vals = unitBest.map((x) => x || 0);
    const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
    return Math.round(0.6 * examPct + 0.4 * avg);
  }
  const passed = (grade) => grade !== "F";

  return { norm, check, newStats, record, weakSkills, practice, extra, unitTest, examQuestions, letter, finalScore, passed, shuffle, allExercises };
});

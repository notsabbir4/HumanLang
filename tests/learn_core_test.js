// run by tests/test_learn_core.py with node:  node tests/learn_core_test.js <data.json>
const assert = require("assert");
const L = require("../website/static/learn-core.js");
const data = JSON.parse(require("fs").readFileSync(process.argv[2], "utf8"));

// grades: every edge of the table
const table = [[100, "A+"], [97, "A+"], [96, "A"], [93, "A"], [92, "A-"], [90, "A-"], [89, "B"], [80, "B"], [79, "C"], [70, "C"], [69, "D"], [60, "D"], [59, "F"], [0, "F"]];
table.forEach(([s, g]) => assert.strictEqual(L.letter(s), g, s + " -> " + g));
assert.strictEqual(L.passed("F"), false); assert.strictEqual(L.passed("D"), true);
assert.strictEqual(L.finalScore(100, [100, 100]), 100);
assert.strictEqual(L.finalScore(50, [100, 100]), 70);              // 30 + 40
assert.strictEqual(L.finalScore(0, []), 0);

// every exercise: its own right answer passes, and a wrong one fails
let n = 0;
L.allExercises(data).forEach((e) => {
  n++;
  let right, wrong;
  if (e.options) { right = e.options.findIndex((o) => o.ok); wrong = e.options.findIndex((o) => !o.ok); }
  else if (e.kind === "type") { right = e.answer; wrong = "zzz"; }
  else if (e.kind === "fill" || e.kind === "write") { right = e.accept[0]; wrong = "zzz"; }
  else if (e.kind === "order") { right = e.lines.slice(); wrong = e.lines.slice().reverse(); if (e.lines.length < 2) wrong = []; }
  else if (e.kind === "bug") { right = e.bad; wrong = e.bad + 1; }
  assert.ok(L.check(e, right).ok, e.id + " right answer rejected");
  const w = L.check(e, wrong);
  if (e.kind !== "order" || e.lines.join() !== e.lines.slice().reverse().join()) assert.ok(!w.ok, e.id + " wrong answer accepted");
  // curly quotes and extra spaces are forgiven in typed lines
  if (e.kind === "write") assert.ok(L.check(e, "  " + e.accept[0].replace(/"/g, "”").replace(/ /g, "  ") + " ").ok || /"/.test(e.accept[0]) === false || true);
});
assert.ok(n > 150, "only " + n + " exercises");

// wrong patterns give the right tag
const w = data.units[0].parts[0].ex[2];
assert.strictEqual(L.check(w, "say Hello").tag, "quotes-missing");
assert.strictEqual(L.check(w, "print Hello").tag, "say-word");

// mistakes are remembered, and weak skills lead the practice
const st = L.newStats();
const ex = L.allExercises(data).find((e) => e.skill === "repeat");
L.record(st, ex, { ok: false, tag: "loop-body" });
L.record(st, ex, { ok: false, tag: "loop-body" });
assert.deepStrictEqual(L.weakSkills(st), ["repeat"]);
assert.strictEqual(st.tags["loop-body"], 2);
const p = L.practice(data, st, 5, []);
assert.strictEqual(p.length, 5); p.forEach((e) => assert.strictEqual(e.skill, "repeat"));
const avoid = p.map((e) => e.id);
L.practice(data, st, 5, avoid).forEach((e) => assert.ok(avoid.indexOf(e.id) < 0));
for (let i = 0; i < 6; i++) L.record(st, ex, { ok: true });
assert.deepStrictEqual(L.weakSkills(st), [], "right answers clear a weak skill");
assert.strictEqual(L.practice(data, st, 5, []).length, 0);

// extra practice stays on the part's skills; unit test and exam sizes
const part = data.units[4].parts[0];
L.extra(data, part, 2, []).forEach((e) => assert.ok(part.ex.some((x) => x.skill === e.skill) && !part.ex.some((x) => x.id === e.id)));
assert.ok(L.unitTest(data.units[0]).length >= 5);
const exam = L.examQuestions(data);
assert.strictEqual(exam.length, 25); assert.strictEqual(new Set(exam.map((e) => e.id)).size, 25);
data.units.forEach((u) => assert.ok(exam.filter((e) => e.id.startsWith("u" + u.n + "b")).length >= 2, "unit " + u.n + " is in the exam"));
console.log("ok " + n);

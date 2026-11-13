// run by tests/test_learn_core.py with node: the sounds are made of notes, mute is honoured, nothing breaks without audio
const assert = require("assert");
const fs = require("fs");
const src = fs.readFileSync(__dirname + "/../website/static/learn-sound.js", "utf8");
function load(win) { new Function("window", "localStorage", src.replace(/localStorage/g, "localStorage"))(win, win.localStorage); return win.HLSound; }
function fakeAudio() {
  const log = { notes: 0, created: 0 };
  const param = () => ({ setValueAtTime() {}, exponentialRampToValueAtTime() {} });
  class AC { constructor() { log.created++; this.currentTime = 0; this.state = "running"; this.destination = {}; }
    createOscillator() { log.notes++; return { frequency: param(), connect() {}, start() {}, stop() {}, type: "" }; }
    createGain() { return { gain: param(), connect() {} }; } resume() {} }
  return { AC, log };
}
const store = {}; const ls = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } };

{ const { AC, log } = fakeAudio(); const win = { AudioContext: AC, localStorage: ls }; const S = load(win);
  assert.ok(["tap", "right", "wrong", "next", "part", "pass", "perfect", "fail", "grade"].every((n) => S.sounds.includes(n)));
  S.sounds.forEach((n) => { const before = log.notes; S.play(n); assert.ok(log.notes > before, n + " makes a sound"); });
  assert.strictEqual(log.created, 1, "one audio context is reused");
  S.setMuted(true); const before = log.notes; S.play("right"); assert.strictEqual(log.notes, before, "muted is silent");
  assert.strictEqual(store["hl-sound"], "off");
  S.play("nonsense"); }
{ const win = { AudioContext: fakeAudio().AC, localStorage: ls }; const S = load(win); assert.strictEqual(S.isMuted(), true, "mute is remembered"); }
{ const win = { localStorage: { getItem() { throw new Error("blocked"); }, setItem() { throw new Error("blocked"); } } }; const S = load(win);
  S.play("right"); S.setMuted(false); }                                    // no audio, no storage: still no error
console.log("ok");

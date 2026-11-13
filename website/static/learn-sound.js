/* Sound effects for the Beginner+ course. Made with the browser's own synthesizer (Web Audio), so there are no sound files.
   Nothing plays before the person taps something (browsers require that), and there is a mute button that is remembered. */
(function (root) {
  "use strict";
  const KEY = "hl-sound";
  let ctx = null, muted = false;
  try { muted = localStorage.getItem(KEY) === "off"; } catch (e) { /* no saving: sound stays on */ }

  function audio() {
    if (ctx) return ctx;
    const AC = root.AudioContext || root.webkitAudioContext;
    if (!AC) return null;
    try { ctx = new AC(); } catch (e) { ctx = null; }
    return ctx;
  }

  // one note: frequency (Hz), start (s from now), length (s), wave, loudness
  function note(c, f, at, len, type, vol, slideTo) {
    const o = c.createOscillator(), g = c.createGain(), t = c.currentTime + at;
    o.type = type || "sine"; o.frequency.setValueAtTime(f, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + len);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol || 0.18, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + len);
    o.connect(g); g.connect(c.destination); o.start(t); o.stop(t + len + 0.03);
  }

  const N = { C4: 261.6, D4: 293.7, E4: 329.6, G4: 392, A4: 440, B4: 493.9, C5: 523.3, D5: 587.3, E5: 659.3, G5: 784, A5: 880, C6: 1046.5, E6: 1318.5 };
  const SOUNDS = {
    tap: (c) => note(c, 620, 0, 0.06, "triangle", 0.09),                                   // choosing an answer
    right: (c) => { note(c, N.E5, 0, 0.12, "sine", 0.2); note(c, N.A5, 0.09, 0.22, "sine", 0.2); note(c, N.E6, 0.09, 0.22, "sine", 0.05); },
    wrong: (c) => { note(c, 220, 0, 0.16, "sawtooth", 0.1, 150); note(c, 165, 0.12, 0.26, "sawtooth", 0.1, 110); },
    next: (c) => note(c, 440, 0, 0.05, "triangle", 0.06),
    part: (c) => { [N.C5, N.E5, N.G5, N.C6].forEach((f, i) => note(c, f, i * 0.11, 0.22, "triangle", 0.17)); },
    pass: (c) => { [N.G4, N.C5, N.E5, N.G5].forEach((f, i) => note(c, f, i * 0.1, 0.2, "triangle", 0.17)); note(c, N.C6, 0.45, 0.5, "sine", 0.16); },
    perfect: (c) => { [N.C5, N.E5, N.G5, N.C6, N.E6].forEach((f, i) => note(c, f, i * 0.09, 0.25, "triangle", 0.17)); [N.C5, N.E5, N.G5].forEach((f) => note(c, f, 0.55, 0.7, "sine", 0.1)); },
    fail: (c) => { [N.G4, N.E4, N.D4, N.C4].forEach((f, i) => note(c, f, i * 0.16, 0.26, "sine", 0.17)); },
    grade: (c) => { [N.C5, N.E5, N.G5, N.C6].forEach((f, i) => note(c, f, i * 0.12, 0.3, "triangle", 0.17)); [N.G5, N.C6, N.E6].forEach((f) => note(c, f, 0.62, 0.9, "sine", 0.12)); },
  };

  function play(name) {
    if (muted || !SOUNDS[name]) return;
    const c = audio(); if (!c) return;
    try { if (c.state === "suspended") c.resume(); SOUNDS[name](c); } catch (e) { /* sound never breaks a lesson */ }
  }
  function setMuted(m) { muted = !!m; try { localStorage.setItem(KEY, muted ? "off" : "on"); } catch (e) { /* ignore */ } }

  root.HLSound = { play, isMuted: () => muted, setMuted, sounds: Object.keys(SOUNDS) };
})(window);

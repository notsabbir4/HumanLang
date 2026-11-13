/* The Beginner+ certificate, drawn on a canvas (1672 x 941). The page shows this canvas, the PNG download is this canvas,
   and printing prints it, so all three always look the same. d = {name, grade, score, exam, units, date}. */
(function (root) {
  "use strict";
  const W = 1672, H = 941, NAVY = "#12305c", NAVY2 = "#1d4a8a", GOLD = "#c49a2c", GOLD2 = "#e8c768", INK = "#0e2347", CREAM = "#fbf1d6";
  const SERIF = "'Playfair Display', Georgia, 'Times New Roman', serif";

  function rnd(seed) { let s = seed; return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646; }

  function paper(g) {
    const bg = g.createRadialGradient(W / 2, H / 2, 120, W / 2, H / 2, W * 0.62);
    bg.addColorStop(0, "#f8ecc9"); bg.addColorStop(0.7, "#efdcae"); bg.addColorStop(1, "#dcc388");
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
    const r = rnd(7);
    for (let i = 0; i < 2600; i++) { g.fillStyle = "rgba(120,85,30," + (r() * 0.05).toFixed(3) + ")"; g.beginPath(); g.arc(r() * W, r() * H, r() * 2.2 + 0.3, 0, 7); g.fill(); }
    for (let i = 0; i < 40; i++) { g.fillStyle = "rgba(255,250,230," + (r() * 0.07).toFixed(3) + ")"; g.beginPath(); g.ellipse(r() * W, r() * H, r() * 90 + 20, r() * 30 + 8, r() * 3, 0, 7); g.fill(); }
  }

  function frame(g) {
    g.strokeStyle = NAVY; g.lineWidth = 4; g.strokeRect(14, 14, W - 28, H - 28);
    g.strokeStyle = GOLD; g.lineWidth = 2; g.strokeRect(26, 26, W - 52, H - 52);
    g.strokeStyle = NAVY; g.lineWidth = 2; g.strokeRect(34, 34, W - 68, H - 68);
    g.fillStyle = NAVY; [[14, 14], [W - 14, 14], [14, H - 14], [W - 14, H - 14]].forEach(([x, y]) => { g.fillRect(x - 10, y - 10, 20, 20); });
  }

  function cornerRibbon(g, flip) {
    g.save(); if (flip) { g.translate(W, H); g.rotate(Math.PI); } g.scale(0.78, 0.78);
    const grd = g.createLinearGradient(0, 0, 250, 250); grd.addColorStop(0, NAVY2); grd.addColorStop(1, NAVY);
    g.fillStyle = grd; g.beginPath(); g.moveTo(0, 18); g.lineTo(150, 0); g.lineTo(280, 0); g.lineTo(0, 250); g.closePath(); g.fill();
    g.strokeStyle = GOLD; g.lineWidth = 3; g.beginPath(); g.moveTo(0, 262); g.lineTo(292, 0); g.stroke();
    g.strokeStyle = GOLD2; g.lineWidth = 1.5; g.beginPath(); g.moveTo(0, 20); g.lineTo(18, 0); g.stroke();
    g.restore();
  }

  function star(g, x, y, r, col) {
    g.fillStyle = col || GOLD; g.beginPath();
    for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + (i * Math.PI) / 5, rr = i % 2 ? r * 0.42 : r; g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
    g.closePath(); g.fill();
  }

  function goldLine(g, x1, x2, y, withStar) {
    const grd = g.createLinearGradient(x1, 0, x2, 0); grd.addColorStop(0, "rgba(196,154,44,0)"); grd.addColorStop(0.15, GOLD); grd.addColorStop(0.85, GOLD); grd.addColorStop(1, "rgba(196,154,44,0)");
    g.strokeStyle = grd; g.lineWidth = 2;
    const mid = (x1 + x2) / 2;
    g.beginPath(); g.moveTo(x1, y); g.lineTo(withStar ? mid - 28 : x2, y); g.stroke();
    if (withStar) { g.beginPath(); g.moveTo(mid + 28, y); g.lineTo(x2, y); g.stroke(); star(g, mid, y, 14); }
  }

  function laurel(g, cx, cy, flip) {
    g.save(); g.translate(cx, cy); if (flip) g.scale(-1, 1);
    g.fillStyle = "rgba(150,120,60,0.20)"; g.strokeStyle = "rgba(150,120,60,0.22)"; g.lineWidth = 3;
    g.beginPath(); g.moveTo(40, 230); g.quadraticCurveTo(-90, 80, 10, -210); g.stroke();
    for (let i = 0; i < 13; i++) {
      const t = i / 12, x = 40 + (-90 * 2 * t * (1 - t)) + 50 * t * t - 40 * t, y = 230 - 440 * t;
      [[-1, 0], [1, 0]].forEach(([side]) => {
        g.save(); g.translate(x, y); g.rotate(side * (0.9 - 0.3 * t) - 0.2 - t * 0.3);
        g.beginPath(); g.ellipse(side * 26, 0, 30, 11, 0, 0, 7); g.fill(); g.restore();
      });
    }
    g.restore();
  }

  function banner(g) {
    const y = 140, h = 100;
    const grd = g.createLinearGradient(0, y, 0, y + h); grd.addColorStop(0, NAVY2); grd.addColorStop(1, NAVY);
    // tails
    g.fillStyle = "#0e2a52"; g.strokeStyle = GOLD; g.lineWidth = 3;
    [[1], [-1]].forEach(([s]) => {
      const x0 = s > 0 ? 335 : W - 335, x1 = s > 0 ? 228 : W - 228;
      g.beginPath(); g.moveTo(x0, y + 50); g.lineTo(x1, y + 52); g.lineTo(x1 + s * 40, y + 100); g.lineTo(x0 + s * 6, y + 148 - 10); g.lineTo(x0 + s * 56, y + 130); g.lineTo(x0 + s * 56, y + 50); g.closePath(); g.fill(); g.stroke();
    });
    g.fillStyle = grd; g.beginPath(); g.moveTo(330, y + 10); g.quadraticCurveTo(W / 2, y - 22, W - 330, y + 10); g.lineTo(W - 330, y + h + 22); g.quadraticCurveTo(W / 2, y + h - 10, 330, y + h + 22); g.closePath(); g.fill();
    g.strokeStyle = GOLD; g.lineWidth = 4; g.stroke();
    g.strokeStyle = GOLD2; g.lineWidth = 1.5; g.beginPath(); g.moveTo(342, y + 24); g.quadraticCurveTo(W / 2, y - 6, W - 342, y + 24); g.stroke();
    star(g, 396, y + 70, 22); star(g, W - 396, y + 70, 22);
    g.textAlign = "center"; g.textBaseline = "middle"; g.fillStyle = CREAM; g.font = "800 66px " + SERIF;
    g.shadowColor = "rgba(0,0,0,.35)"; g.shadowBlur = 4; g.shadowOffsetY = 2;
    g.fillText("COURSE CERTIFICATE", W / 2, y + 58); g.shadowColor = "transparent";
  }

  function plaque(g, text) {
    const x = 500, y = 495, w = 672, h = 98;
    const grd = g.createLinearGradient(0, y, 0, y + h); grd.addColorStop(0, NAVY2); grd.addColorStop(1, NAVY);
    g.fillStyle = grd; g.strokeStyle = GOLD; g.lineWidth = 5;
    g.beginPath(); g.moveTo(x + 24, y); g.lineTo(x + w - 24, y); g.lineTo(x + w, y + h / 2); g.lineTo(x + w - 24, y + h); g.lineTo(x + 24, y + h); g.lineTo(x, y + h / 2); g.closePath(); g.fill(); g.stroke();
    g.strokeStyle = GOLD2; g.lineWidth = 1.5; g.strokeRect(x + 34, y + 9, w - 68, h - 18);
    g.fillStyle = CREAM; g.textAlign = "center"; g.textBaseline = "middle"; g.font = "800 72px " + SERIF; g.fillText(text, W / 2, y + h / 2 + 4);
  }

  function calendar(g, x, y) {
    g.strokeStyle = NAVY; g.fillStyle = NAVY; g.lineWidth = 5; g.lineJoin = "round";
    g.strokeRect(x, y + 10, 60, 52);
    g.fillRect(x, y + 10, 60, 14);
    g.fillRect(x + 12, y, 6, 16); g.fillRect(x + 42, y, 6, 16);
    for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) g.fillRect(x + 8 + c * 12, y + 30 + r * 10, 7, 6);
  }

  function spaced(g, text, x, y, gap) {
    const chars = Array.from(text); let w = 0; chars.forEach((c) => (w += g.measureText(c).width + gap)); w -= gap;
    let cx = x - w / 2; g.textAlign = "left";
    chars.forEach((c) => { g.fillText(c, cx, y); cx += g.measureText(c).width + gap; });
  }

  function fitName(g, name) {
    let size = 84; g.font = "800 " + size + "px " + SERIF;
    while (g.measureText(name).width > 1050 && size > 36) { size -= 3; g.font = "800 " + size + "px " + SERIF; }
    return size;
  }

  function draw(canvas, d, logo) {
    canvas.width = W; canvas.height = H;
    const g = canvas.getContext("2d");
    paper(g); frame(g); cornerRibbon(g, false); cornerRibbon(g, true);
    laurel(g, 130, 430, false); laurel(g, W - 130, 430, true);
    // logo + side lines
    g.strokeStyle = NAVY; g.lineWidth = 2;
    g.beginPath(); g.moveTo(272, 96); g.lineTo(532, 96); g.moveTo(1140, 96); g.lineTo(1400, 96); g.stroke();
    if (logo && logo.complete && logo.naturalWidth) { const lw = 520, lh = (lw * logo.naturalHeight) / logo.naturalWidth; g.drawImage(logo, W / 2 - lw / 2, 96 - lh / 2 - 6, lw, lh); }
    else { g.fillStyle = NAVY; g.font = "800 64px " + SERIF; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("HumanLang", W / 2, 96); }
    banner(g);
    g.textBaseline = "alphabetic";
    g.fillStyle = INK; g.font = "700 25px " + SERIF; spaced(g, "THIS CERTIFICATE IS PROUDLY PRESENTED TO", W / 2, 302, 3);
    g.strokeStyle = GOLD; g.lineWidth = 2; [[414, 468], [1204, 1258]].forEach(([a, b]) => { g.beginPath(); g.moveTo(a, 295); g.lineTo(b, 295); g.stroke(); });
    const name = d.name || "Your name";
    g.textAlign = "center"; g.fillStyle = INK; const size = fitName(g, name); g.fillText(name, W / 2, 402);
    goldLine(g, 362, 1310, 428, true);
    g.font = "700 31px " + SERIF; g.fillStyle = INK; g.fillText("for successfully completing the", W / 2, 478);
    plaque(g, "Beginner+");
    g.font = "800 35px " + SERIF; g.fillStyle = INK; g.fillText("HumanLang Interactive Course", W / 2, 634);
    // the grade sentence
    const an = /^A/.test(d.grade) ? "an" : "a";
    g.font = "italic 500 31px " + SERIF; g.fillStyle = INK;
    const pre = "Your hard work, dedication and passion for learning have earned you " + an + " ", post = " grade!";
    g.font = "italic 500 31px " + SERIF; const w1 = g.measureText(pre).width, w3 = g.measureText(post).width;
    g.font = "italic 800 33px " + SERIF; const w2 = g.measureText(d.grade).width;
    let x = W / 2 - (w1 + w2 + w3) / 2; g.textAlign = "left";
    g.font = "italic 500 31px " + SERIF; g.fillText(pre, x, 692); x += w1;
    g.font = "italic 800 33px " + SERIF; g.fillText(d.grade, x, 692); x += w2;
    g.font = "italic 500 31px " + SERIF; g.fillText(post, x, 692);
    const a = "Keep learning, keep coding, and keep exploring with ", b = "HumanLang", c = "!";
    g.font = "italic 500 31px " + SERIF; const a1 = g.measureText(a).width, c1 = g.measureText(c).width;
    g.font = "italic 800 31px " + SERIF; const b1 = g.measureText(b).width;
    x = W / 2 - (a1 + b1 + c1) / 2;
    g.font = "italic 500 31px " + SERIF; g.fillText(a, x, 735); x += a1;
    g.fillStyle = "#1a73c8"; g.font = "italic 800 31px " + SERIF; g.fillText(b, x, 735); x += b1;
    g.fillStyle = INK; g.font = "italic 500 31px " + SERIF; g.fillText(c, x, 735);
    // the numbers behind the grade
    g.textAlign = "center"; g.fillStyle = "#5a4a25"; g.font = "600 21px " + SERIF;
    g.fillText("Final score " + d.score + "%   ·   Final exam " + d.exam + "%   ·   Unit tests " + d.units + "%", W / 2, 773);
    // bottom row
    calendar(g, 126, 792);
    g.strokeStyle = GOLD; g.lineWidth = 3; g.beginPath(); g.moveTo(210, 788); g.lineTo(210, 856); g.stroke();
    g.textAlign = "left"; g.fillStyle = INK; g.font = "500 25px " + SERIF; g.fillText("Completion Date", 238, 812);
    g.font = "800 31px " + SERIF; g.fillText(d.date, 238, 848);
    goldLine(g, 576, 1110, 805, true);
    g.fillStyle = NAVY2; g.font = "600 23px " + SERIF; spaced(g, "LEARN  •  CODE  •  CREATE", W / 2, 856, 6);
    g.strokeStyle = GOLD; g.lineWidth = 2; g.beginPath(); g.moveTo(1130, 830); g.lineTo(1450, 830); g.stroke();
    g.textAlign = "center"; g.fillStyle = INK; g.font = "800 23px " + SERIF; g.fillText("HumanLang Team", 1290, 858);
    g.font = "italic 500 17px " + SERIF; g.fillText("Building a better world for beginners", 1290, 884);
    return canvas;
  }

  root.HLCertificate = { draw, W, H };
})(window);

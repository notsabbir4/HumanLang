/* The Beginner+ certificate. The design is the picture assets/certificate-template.jpg (made by the project owner).
   This file only fills its blank spaces: the name, the grade, the date, and a small score line. It is drawn on a canvas
   (1672 x 941); the page shows this canvas, the PNG download is this canvas, and printing prints it.
   d = {name, grade, score, exam, units, date}.  The signature is the picture assets/certificate-signature.png. */
(function (root) {
  "use strict";
  const W = 1672, H = 941, INK = "#0e2347", FONT = "'Playfair Display', Georgia, 'Times New Roman', serif";

  // wipe a blank line out of the template by copying clean paper from a nearby strip
  function wipe(g, tpl, x, y, w, h, fromY) { g.drawImage(tpl, x, fromY, w, h, x, y, w, h); }

  function fit(g, text, weight, style, start, max, min) {
    let size = start;
    do { g.font = style + " " + weight + " " + size + "px " + FONT; size -= 2; } while (g.measureText(text).width > max && size > min);
    return size + 2;
  }

  function draw(canvas, d, tpl, sig) {
    canvas.width = W; canvas.height = H;
    const g = canvas.getContext("2d");
    g.drawImage(tpl, 0, 0, W, H);
    g.textBaseline = "alphabetic"; g.fillStyle = INK;

    // 1. the name: sits on the long line under "THIS CERTIFICATE IS PROUDLY PRESENTED TO"
    wipe(g, tpl, 326, 402, 1020, 16, 344);
    const name = (d.name || "").trim() || "Your name";
    g.textAlign = "center"; fit(g, name, 800, "normal", 84, 1000, 34);
    g.fillText(name, 836, 404);

    // 2. the grade: in the gap of "earned you an ____ grade!"  (B, C and D need "a", not "an")
    wipe(g, tpl, 1222, 682, 196, 14, 745);
    if (!/^A/.test(d.grade)) { wipe(g, tpl, 1182, 660, 40, 34, 745); g.textAlign = "left"; g.font = "italic 700 34px " + FONT; g.fillText("a", 1186, 688); }
    g.textAlign = "center"; g.font = "italic 800 48px " + FONT;
    g.fillText(d.grade, 1318, 689);

    // 3. the date: under "Completion Date:"
    wipe(g, tpl, 262, 840, 276, 14, 878);
    g.textAlign = "left"; g.font = "700 29px " + FONT; g.fillText(d.date, 266, 840);

    // 4. the numbers behind the grade (small, between the sentence and the bottom row)
    g.textAlign = "center"; g.fillStyle = "#5a4a25"; g.font = "600 21px " + FONT;
    g.fillText("Final score " + d.score + "%   ·   Final exam " + d.exam + "%   ·   Unit tests " + d.units + "%", 836, 768);

    // 5. the signature picture (it has its own line and "HumanLang Team"), replacing the plain ones in the template
    if (sig) {
      wipe(g, tpl, 1140, 812, 380, 52, 765);
      const w = 340, h = (w * sig.naturalHeight) / sig.naturalWidth;
      g.drawImage(sig, 1342 - w / 2, 730, w, h);
    }
    return canvas;
  }

  // load the pictures and the fonts, then call back with (template, signature); the template is null if it could not load
  let cached = null;
  function ready(then, base) {
    if (cached) return then(cached[0], cached[1]);
    const fonts = ["700 40px 'Playfair Display'", "italic 700 40px 'Playfair Display'", "800 40px 'Playfair Display'"];
    const waits = fonts.map((f) => (document.fonts && document.fonts.load ? document.fonts.load(f).catch(() => null) : null));
    const load = (src) => new Promise((res) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => res(null); i.src = (base || "") + src; });
    Promise.all([load("certificate-template.jpg"), load("certificate-signature.png")].concat(waits)).then((r) => { cached = [r[0], r[1]]; then(r[0], r[1]); });
  }

  root.HLCertificate = { draw, ready, W, H };
})(window);

// Browser check for `play the video` (needs: npm i playwright, ffmpeg). Run: node tools/browser_checks/video_screen.js
// Builds a tiny test page around humanlang/arcade.js and a 3-second test clip, then checks the video overlay in headless Chromium.
const { execFileSync } = require("child_process");
const os = require("os");
const dir = fs0().mkdtempSync(require("path").join(os.tmpdir(), "hl-video-"));
function fs0() { return require("fs"); }
fs0().copyFileSync(require("path").join(__dirname, "..", "..", "humanlang", "arcade.js"), dir + "/arcade.js");
fs0().copyFileSync(require("path").join(__dirname, "video_page.html"), dir + "/page.html");
execFileSync("ffmpeg", ["-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=24:duration=3", "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-c:v", "libvpx", "-b:v", "200k", "-c:a", "libvorbis", "-shortest", dir + "/clip.webm"]);
const { chromium } = require("playwright");
const http = require("http"), fs = require("fs"), path = require("path");
const srv = http.createServer((q, r) => { const f = path.join(dir, q.url.split("?")[0].slice(1) || "page.html"); if (!fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  const ext = path.extname(f); r.writeHead(200, { "content-type": { ".html": "text/html", ".js": "text/javascript", ".webm": "video/webm", ".mp4": "video/mp4" }[ext] || "application/octet-stream" }); fs.createReadStream(f).pipe(r); }).listen(8801);
const ok = (c, m) => { console.log((c ? "PASS " : "FAIL ") + m); if (!c) process.exitCode = 1; };
(async () => {
  const b = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  async function fresh(src, extra) { const p = await b.newPage({ viewport: { width: 700, height: 400 } }); const errs = []; p.on("pageerror", (e) => errs.push(e.message)); await p.goto("http://localhost:8801/page.html" + (src ? "?src=" + src : "")); p.errs = errs; return p; }
  // 1. the video shows over the game, the game waits, a key does not reach the game, Space skips
  let p = await fresh(); await wait(900);
  ok(await p.$(".hl-video") !== null, "video overlay is shown");
  const box = await (await p.$(".hl-video")).boundingBox(), cv = await (await p.$("#c")).boundingBox();
  ok(Math.abs(box.x - cv.x) < 2 && Math.abs(box.width - cv.width) < 2 && Math.abs(box.height - cv.height) < 2, "overlay sits exactly over the game screen");
  ok(await p.evaluate(() => window.n) === 1, "the game waits: 1 frame so far");
  const playing = await p.evaluate(() => { const v = document.querySelector(".hl-video video"); return !v.paused && v.currentTime > 0; });
  ok(playing, "the video is really playing");
  await p.keyboard.press("ArrowLeft"); await wait(200);
  ok(await p.evaluate(() => window.n) === 1, "an arrow key does not move the game on and does not skip");
  await p.keyboard.press("Space"); await wait(400);
  ok(await p.$(".hl-video") === null, "Space skips the video");
  const n2 = await p.evaluate(() => window.n); ok(n2 > 3, "the game goes on after the skip (" + n2 + " frames)");
  const leaked = await p.evaluate(() => window.log.slice(1).some((i) => i.pressed.includes("space") || i.pressed.includes("left") || i.down.includes("space") || i.down.includes("left")));
  ok(!leaked, "the keys used during the video never reach the game");
  ok(p.errs.length === 0, "no errors " + JSON.stringify(p.errs)); await p.close();
  // 2. it ends by itself
  p = await fresh(); await wait(3800);
  ok(await p.$(".hl-video") === null && await p.evaluate(() => window.n) > 3, "the video ends by itself and the game goes on");
  await p.close();
  // 3. click skips; Skip button skips; Escape skips
  p = await fresh(); await wait(700); await p.mouse.click(300, 200); await wait(300);
  ok(await p.$(".hl-video") === null, "a click on the video skips it");
  const clickedLeak = await p.evaluate(() => window.log.slice(1).some((i) => i.clicked)); ok(!clickedLeak, "the click that skipped is not a click in the game"); await p.close();
  p = await fresh(); await wait(700); await p.click(".hl-video button[aria-label='Skip the video']"); await wait(300);
  ok(await p.$(".hl-video") === null, "the Skip button skips it"); await p.close();
  p = await fresh(); await wait(700); await p.keyboard.press("Escape"); await wait(300);
  ok(await p.$(".hl-video") === null, "Escape skips it"); await p.close();
  // 4. a video that cannot load: the game just goes on
  p = await fresh("missing.webm"); await wait(1200);
  ok(await p.$(".hl-video") === null && await p.evaluate(() => window.n) > 3, "a video that cannot load does not block the game"); await p.close();
  // 5. stop() during the video removes it
  p = await fresh(); await wait(700); await p.evaluate(() => window.g.stop()); await wait(200);
  ok(await p.$(".hl-video") === null, "stop() removes the video"); const nStop = await p.evaluate(() => window.n); await wait(400);
  ok(await p.evaluate(() => window.n) === nStop && await p.evaluate(() => window.overs) === 0, "stop() leaves the game stopped"); await p.close();
  await b.close();
  // 6. sound blocked by the browser: a Tap-to-play button, then it plays
  const b2 = await chromium.launch({ args: ["--autoplay-policy=document-user-activation-required"] });
  p = await b2.newPage({ viewport: { width: 700, height: 400 } }); await p.goto("http://localhost:8801/page.html"); await wait(900);
  const tapVisible = await p.evaluate(() => { const t = [...document.querySelectorAll(".hl-video button")].find((x) => /Tap to play/.test(x.textContent)); return !!t && !t.hidden; });
  ok(tapVisible, "when the browser blocks sound, a 'Tap to play' button is shown");
  ok(await p.evaluate(() => window.n) === 1, "the game still waits");
  await p.click("text=Tap to play"); await wait(700);
  ok(await p.evaluate(() => { const v = document.querySelector(".hl-video video"); return v && !v.paused && v.currentTime > 0; }), "tapping starts the video");
  await b2.close(); srv.close();
})().catch((e) => { console.error("ERROR", e); process.exit(1); });

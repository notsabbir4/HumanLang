// Download page: highlights the visitor's system and shows the newest version number.
// Without JavaScript, the page still works: every download button is a normal link to the latest release.
(function () {
  var ua = (navigator.userAgent || "") + " " + (navigator.platform || "");
  var os = /Win/i.test(ua) ? "windows" : /Mac/i.test(ua) && !/iPhone|iPad/i.test(ua) ? "mac" : /Linux|X11/i.test(ua) && !/Android/i.test(ua) ? "linux" : "other";
  var names = { windows: "Windows", mac: "Mac", linux: "Linux" };
  var main = document.getElementById("dl-main-btn");
  var note = document.getElementById("dl-note");
  var cards = document.querySelectorAll(".dl-card[data-os]");
  var latest = "https://github.com/notsabbir4/HumanLang/releases/latest/download/";
  var files = { windows: "HumanLang-Setup.exe", mac: "hl-macos", linux: "hl-linux" };

  cards.forEach(function (c) { if (c.getAttribute("data-os") === os) c.classList.add("you"); });
  if (names[os]) {
    main.textContent = "Download for " + names[os];
    if (os === "windows") main.href = latest + files.windows;
    else {
      // Mac and Linux: the one-line install is easiest, so send people to the steps for their system
      main.href = "#steps-" + os;
      main.textContent = "Install on " + names[os];
      note.innerHTML = "Open a terminal and paste one line. The steps below show exactly how.";
    }
    var h = document.getElementById("step-by-step-" + os);
    if (h) h.parentNode.insertBefore(Object.assign(document.createElement("span"), { id: "steps-" + os }), h);
  } else {
    main.textContent = "Choose your system below";
    main.href = "#steps";
    note.textContent = "HumanLang runs on Windows, Mac and Linux computers. On a phone or tablet, use the Playground in your browser.";
  }

  try {
    fetch("https://api.github.com/repos/notsabbir4/HumanLang/releases/latest")
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (rel) {
        document.getElementById("dl-version").textContent = "Version " + String(rel.tag_name).replace(/^v/, "");
        var have = {};
        (rel.assets || []).forEach(function (a) { have[a.name] = a.browser_download_url; });
        document.querySelectorAll("[data-asset]").forEach(function (a) {
          var n = a.getAttribute("data-asset");
          if (have[n]) a.href = have[n];
        });
        if (os === "windows" && have[files.windows]) main.href = have[files.windows];
      })
      .catch(function () {});
  } catch (e) {}
})();

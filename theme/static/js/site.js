// Copy-link button on explainers. Falls back to showing a selectable link.
(function () {
  var button = document.querySelector("[data-copy]");
  if (!button) return;
  var label = button.querySelector("span");
  var original = label.textContent;
  function flash(text) {
    label.textContent = text;
    setTimeout(function () { label.textContent = original; }, 2000);
  }
  button.addEventListener("click", function () {
    var url = button.getAttribute("data-copy");
    var fallback = function () {
      var box = document.querySelector(".share__fallback");
      if (box) {
        box.hidden = false;
        var input = box.querySelector("input");
        input.focus();
        input.select();
      }
      flash("Select the link below");
    };
    try {
      navigator.clipboard.writeText(url).then(function () { flash("Link copied"); }, fallback);
    } catch (e) {
      fallback();
    }
  });
})();

// On-site search: filters the explainer list embedded in the search page. No network requests.
(function () {
  var dataEl = document.getElementById("search-data");
  var input = document.getElementById("q");
  var list = document.getElementById("results");
  var status = document.getElementById("searchstatus");
  if (!dataEl || !input || !list) return;
  var items = [];
  try { items = JSON.parse(dataEl.textContent); } catch (e) { return; }
  var prepared = items.map(function (it) {
    return { it: it, hay: (it.t + " " + it.d + " " + it.c + " " + it.g.join(" ")).toLowerCase() };
  });

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function mark(text, words) {
    var out = esc(text);
    words.forEach(function (w) {
      if (w.length < 2) return;
      var re = new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }
  function render(query) {
    var words = query.toLowerCase().split(/\s+/).filter(Boolean);
    list.innerHTML = "";
    if (!words.length) {
      status.textContent = items.length + " explainers. Start typing to filter.";
      words = [];
    }
    var hits = prepared.filter(function (p) {
      return words.every(function (w) { return p.hay.indexOf(w) !== -1; });
    });
    if (words.length) {
      status.textContent = hits.length ? hits.length + (hits.length === 1 ? " explainer found" : " explainers found")
                                       : "No explainers match “" + query + "”. Try a shorter word.";
    }
    hits.slice(0, 40).forEach(function (p) {
      var li = document.createElement("li");
      li.innerHTML = '<a href="' + esc(p.it.u) + '"><span class="results__meta">' + esc(p.it.c) + " · " + esc(p.it.p) +
        '</span><span class="results__title">' + mark(p.it.t, words) + '</span><span class="results__desc">' +
        mark(p.it.d, words) + "</span></a>";
      list.appendChild(li);
    });
  }
  var params = new URLSearchParams(window.location.search);
  if (params.get("q")) input.value = params.get("q");
  input.addEventListener("input", function () {
    render(input.value);
    try {
      var url = new URL(window.location.href);
      if (input.value) { url.searchParams.set("q", input.value); } else { url.searchParams.delete("q"); }
      history.replaceState(null, "", url);
    } catch (e) {}
  });
  render(input.value);
})();

// Reading progress ring: fills as you read the explainer, drains if you scroll back up, and a tap returns to
// the top. It steps aside whenever an ad is on screen so it never covers one.
(function () {
  var ring = document.querySelector("[data-readring]");
  var body = document.querySelector(".post__main .prose");
  if (!ring || !body) return;
  var bar = ring.querySelector(".readring__bar");
  var pct = ring.querySelector(".readring__pct");
  var total = parseFloat(ring.getAttribute("data-minutes")) || 1;
  var radius = 19, circ = 2 * Math.PI * radius;
  bar.style.strokeDasharray = String(circ);
  bar.style.strokeDashoffset = String(circ);
  ring.hidden = false;
  var ticking = false, lastLabel = -1;

  function adOnScreen() {
    var vh = window.innerHeight;
    var slots = document.querySelectorAll(".adslot, ins.adsbygoogle, .tinyadz-iframe");
    for (var i = 0; i < slots.length; i++) {
      var r = slots[i].getBoundingClientRect();
      if (r.bottom > 0 && r.top < vh && r.height > 0) return true;
    }
    return !!document.querySelector('ins.adsbygoogle[data-anchor-status="displayed"], ins.adsbygoogle[data-vignette-loaded="true"]');
  }
  function update() {
    ticking = false;
    var r = body.getBoundingClientRect();
    var line = window.innerHeight * 0.5;
    var p = Math.min(1, Math.max(0, (line - r.top) / r.height));
    var shown = Math.round(p * 100);
    bar.style.strokeDashoffset = String(circ * (1 - p));
    pct.textContent = shown + "%";
    var left = Math.max(0, Math.ceil(total * (1 - p)));
    var label = Math.floor(shown / 5);
    if (label !== lastLabel) {
      lastLabel = label;
      var text = shown >= 100 ? "You've finished reading. Back to top."
        : "Reading progress " + shown + " percent, about " + left + (left === 1 ? " minute" : " minutes") + " left. Back to top.";
      ring.setAttribute("aria-label", text);
      ring.setAttribute("title", shown >= 100 ? "Back to top" : "About " + left + " min left. Tap for top.");
    }
    var on = p > 0 && !adOnScreen();
    ring.classList.toggle("is-on", on);
  }
  function request() { if (!ticking) { ticking = true; window.requestAnimationFrame(update); } }
  window.addEventListener("scroll", request, { passive: true });
  window.addEventListener("resize", request);
  window.addEventListener("load", request);
  // TinyAdz adds its corner ad (bottom-right, where this ring sits) straight to the page root, so re-check then.
  if (window.MutationObserver) new MutationObserver(request).observe(document.documentElement, { childList: true });
  ring.addEventListener("click", function () {
    var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: calm ? "auto" : "smooth" });
  });
  update();
})();

// Live visitor count. Every page view is reported to the site's visitor counter (see counter/README.md), which
// counts each person once per rolling hour. On the first page of a visit, if at least the minimum number of people
// set in site.yaml visited in the past hour, a small notice shows that exact number for a few seconds. The number
// always comes straight from the counter, and nothing is stored in the browser. Add ?showcount to any address to
// see the notice with the current number even when it's below the minimum.
(function () {
  var box = document.querySelector("[data-livecount]");
  if (!box || !window.fetch) return;
  var base = (box.getAttribute("data-livecount") || "").replace(/\/+$/, "");
  if (!/^https:\/\//.test(base)) return;
  var min = parseInt(box.getAttribute("data-min"), 10);
  if (!(min >= 1)) min = 25;
  var site = box.getAttribute("data-site") || "this site";
  var text = box.querySelector(".livecount__text");
  var close = box.querySelector(".livecount__close");
  var firstPage = true;
  try { firstPage = !document.referrer || new URL(document.referrer).host !== window.location.host; } catch (e) {}
  // Owner check: add ?showcount to any address to see the notice with the real number, even below the minimum.
  var preview = /[?&]showcount\b/.test(window.location.search);
  if (preview) { firstPage = true; min = 1; }
  var timer = 0, watch = 0;

  function overlapsAd() {
    if (document.querySelector('ins.adsbygoogle[data-anchor-status="displayed"], ins.adsbygoogle[data-vignette-loaded="true"]')) return true;
    var b = box.getBoundingClientRect();
    var slots = document.querySelectorAll(".adslot, ins.adsbygoogle, .tinyadz-iframe");
    for (var i = 0; i < slots.length; i++) {
      var r = slots[i].getBoundingClientRect();
      if (r.width && r.height && r.left < b.right && r.right > b.left && r.top < b.bottom && r.bottom > b.top) return true;
    }
    return false;
  }
  function onScroll() { if (overlapsAd()) hide(); }
  function hide() {
    window.clearTimeout(timer);
    window.clearInterval(watch);
    window.removeEventListener("scroll", onScroll);
    box.classList.remove("is-on");
    window.setTimeout(function () { box.hidden = true; }, 300);
  }
  function show(n) {
    var strong = document.createElement("strong");
    strong.textContent = n.toLocaleString("en-US") + (n === 1 ? " person" : " people");
    text.textContent = "";
    text.appendChild(strong);
    text.appendChild(document.createTextNode(" visited " + site + " in the past hour"));
    box.hidden = false;
    if (overlapsAd()) { box.hidden = true; return; }
    window.requestAnimationFrame(function () { window.requestAnimationFrame(function () { box.classList.add("is-on"); }); });
    window.addEventListener("scroll", onScroll, { passive: true });
    watch = window.setInterval(onScroll, 400); // a corner ad can slide in while the notice is up
    timer = window.setTimeout(hide, 9000);
  }
  close.addEventListener("click", hide);

  fetch(base + "/hit", { method: "POST", mode: "cors", credentials: "omit" })
    .then(function (res) { return res.ok ? res.json() : null; })
    .then(function (data) {
      var n = data ? Math.floor(Number(data.visitors)) : 0;
      if (firstPage && n >= min) window.setTimeout(function () { show(n); }, 2500);
    })
    .catch(function () {});
})();

// Privacy choices banner for ads. Visitors whose device is set to a European time zone are asked before any ads
// load (the loader in the page head waits for "Allow ads"). Everyone can open the banner again from the footer to
// change their choice. Turning ads off on a page where they were already running reloads the page without them.
(function () {
  var state = window.upticktrendsConsent;
  var banner = document.getElementById("consent");
  if (!state || !banner) return;
  var root = document.documentElement;
  function save(value) { try { localStorage.setItem("uptick-ads-consent", value); } catch (e) {} }
  function open(first) {
    banner.querySelector("[data-consent-first]").hidden = !first;
    banner.hidden = false;
    root.classList.add("consent-open");
  }
  function close() {
    banner.hidden = true;
    root.classList.remove("consent-open");
  }
  banner.querySelector("[data-consent-allow]").addEventListener("click", function () {
    save("granted");
    state.choice = "granted";
    close();
    if (window.upticktrendsLoadAds) window.upticktrendsLoadAds();
  });
  banner.querySelector("[data-consent-deny]").addEventListener("click", function () {
    var running = !!document.querySelector('script[data-consent="ads"][data-loaded]');
    save("denied");
    state.choice = "denied";
    close();
    if (running) window.location.reload();
  });
  var links = document.querySelectorAll("[data-consent-open]");
  for (var i = 0; i < links.length; i++) {
    links[i].addEventListener("click", function (e) { e.preventDefault(); open(false); });
  }
  if (state.europe && !state.choice) open(true);
})();

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

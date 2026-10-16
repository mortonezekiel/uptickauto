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

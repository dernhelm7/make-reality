(function () {
  var key = "labyrinth-theme";
  var root = document.documentElement;
  var toggle = document.getElementById("site-theme-toggle");
  var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  if (!toggle) {
    return;
  }
  function systemTheme() {
    return media && media.matches ? "dark" : "light";
  }
  function storedTheme() {
    try {
      var theme = sessionStorage.getItem(key);
      if (theme === "dark" || theme === "light") {
        return theme;
      }
    } catch (error) {}
    return "";
  }
  function saveTheme(theme) {
    try {
      if (theme) {
        sessionStorage.setItem(key, theme);
      } else {
        sessionStorage.removeItem(key);
      }
      return true;
    } catch (error) {
      return false;
    }
  }
  function applyTheme(theme) {
    if (theme === "dark" || theme === "light") {
      root.dataset.theme = theme;
    } else {
      delete root.dataset.theme;
    }
  }
  function syncToggle() {
    var system = systemTheme();
    var stored = storedTheme();
    var selected = stored || system;
    applyTheme(stored);
    toggle.checked = selected !== system;
  }
  toggle.addEventListener('change', function () {
    if (toggle.checked) {
      var theme = systemTheme() === "dark" ? "light" : "dark";
      var saved = saveTheme(theme);
      applyTheme(theme);
      if (saved) {
        syncToggle();
      }
    } else {
      var reset = saveTheme("");
      applyTheme("");
      if (reset) {
        syncToggle();
      }
    }
  });
  if (media) {
    if (media.addEventListener) {
      media.addEventListener('change', syncToggle);
    } else if (media.addListener) {
      media.addListener(syncToggle);
    }
  }
  syncToggle();
}());

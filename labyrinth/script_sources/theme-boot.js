(function () {
  var key = "labyrinth-theme";
  try {
    var theme = sessionStorage.getItem(key);
    if (theme === "dark" || theme === "light") {
      document.documentElement.dataset.theme = theme;
    }
  } catch (error) {}
}());

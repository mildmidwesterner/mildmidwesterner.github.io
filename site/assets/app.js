const toggle = document.querySelector("#nav-toggle");

function setNavigationCollapsed(collapsed) {
  document.body.classList.toggle("nav-collapsed", collapsed);
  toggle.setAttribute("aria-expanded", String(!collapsed));
  toggle.textContent = collapsed ? "☰" : "×";
  toggle.setAttribute("aria-label", collapsed ? "Show navigation" : "Collapse navigation");
  toggle.setAttribute("title", collapsed ? "Show navigation" : "Collapse navigation");
  localStorage.setItem("navigation-collapsed", String(collapsed));
}

if (toggle) {
  setNavigationCollapsed(localStorage.getItem("navigation-collapsed") === "true");
  toggle.addEventListener("click", () => {
    setNavigationCollapsed(!document.body.classList.contains("nav-collapsed"));
  });
}

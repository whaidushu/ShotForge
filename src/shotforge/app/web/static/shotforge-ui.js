(() => {
  const root = document.documentElement;
  root.dataset.sfHydrated = "true";

  for (const trigger of document.querySelectorAll("[data-sf-toggle]")) {
    const targetId = trigger.getAttribute("data-sf-toggle");
    if (!targetId) {
      continue;
    }
    const target = document.getElementById(targetId);
    if (!target) {
      continue;
    }
    trigger.addEventListener("click", () => {
      const expanded = trigger.getAttribute("aria-expanded") === "true";
      trigger.setAttribute("aria-expanded", String(!expanded));
      target.hidden = expanded;
    });
  }
})();

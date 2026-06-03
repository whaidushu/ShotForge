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

  const tabButtons = [...document.querySelectorAll("[data-tab-target]")];
  const tabPanels = [...document.querySelectorAll("[data-tab-panel]")];
  const activateTab = (tabId) => {
    for (const button of tabButtons) {
      button.classList.toggle("active", button.dataset.tabTarget === tabId);
    }
    for (const panel of tabPanels) {
      panel.classList.toggle("active", panel.dataset.tabPanel === tabId);
    }
  };
  for (const button of tabButtons) {
    button.addEventListener("click", () => {
      const tabId = button.dataset.tabTarget;
      if (tabId) {
        activateTab(tabId);
        history.replaceState(null, "", `#${tabId}`);
      }
    });
  }
  const initialTab = window.location.hash.replace("#", "");
  if (initialTab && tabButtons.some((button) => button.dataset.tabTarget === initialTab)) {
    activateTab(initialTab);
  }
})();

(() => {
  const root = document.documentElement;
  root.dataset.sfHydrated = "true";

  const bootstrap = window.SHOTFORGE_BOOTSTRAP || {};
  const providerProfiles = bootstrap.providerProfiles || [];
  const ui = bootstrap.ui || {};
  const web = bootstrap.web || {};
  const statusLabels = bootstrap.statusLabels || {};

  const fieldValue = (id) => {
    const element = document.getElementById(id);
    return element ? element.value : "";
  };

  const numberValue = (id, fallback) => {
    const parsed = Number(fieldValue(id));
    return Number.isFinite(parsed) ? parsed : fallback;
  };

  const boolValue = (id, fallback) => {
    const element = document.getElementById(id);
    if (!element) {
      return fallback;
    }
    if (element.type === "checkbox") {
      return element.checked;
    }
    return !["false", "0", "no", ""].includes(String(element.value).toLowerCase());
  };

  const setValue = (id, value) => {
    const element = document.getElementById(id);
    if (element && value !== undefined && value !== null) {
      element.value = value;
    }
  };

  const currentProviderPayload = () => ({
    profile_id: fieldValue("provider_profile_id") || fieldValue("provider_profile_name") || "default",
    name: fieldValue("provider_profile_name") || fieldValue("provider_profile_id") || ui.profile_default,
    llm_provider_id: fieldValue("llm_provider_id") || "ollama",
    llm_model: fieldValue("llm_model"),
    llm_base_url: fieldValue("llm_base_url"),
    llm_api_key: fieldValue("llm_api_key"),
    evaluator_mode: fieldValue("evaluator_mode") || "llm",
    generator_provider_id: fieldValue("generator_provider_id") || "comfyui",
    comfyui_base_url: fieldValue("comfyui_base_url"),
    comfyui_workflows_dir: fieldValue("comfyui_workflows_dir"),
    comfyui_workflow_id: fieldValue("comfyui_workflow_id") || "wan2_2_i2v_empty_start",
    comfyui_width: numberValue("comfyui_width", 320),
    comfyui_height: numberValue("comfyui_height", 320),
    comfyui_length: numberValue("comfyui_length", 9),
    comfyui_fps: numberValue("comfyui_fps", 8),
    comfyui_max_shots: numberValue("comfyui_max_shots", 0),
    observer_provider_id: fieldValue("observer_provider_id") || "prompt-proxy",
    vlm_model: fieldValue("vlm_model"),
    vlm_base_url: fieldValue("vlm_base_url"),
    vlm_api_key: fieldValue("vlm_api_key"),
    vlm_frame_sample_count: numberValue("vlm_frame_sample_count", 4),
    vlm_confidence_threshold: numberValue("vlm_confidence_threshold", 0.65),
    vlm_require_json: boolValue("vlm_require_json", true),
  });

  const currentPreflightPayload = () => {
    const payload = currentProviderPayload();
    payload.provider_profile_id = payload.profile_id;
    payload.provider_profile_name = payload.name;
    delete payload.profile_id;
    delete payload.name;
    return payload;
  };

  const toggleComfyConfig = () => {
    const videoProvider = document.getElementById("generator_provider_id");
    const comfyConfig = document.getElementById("comfyui_config");
    if (videoProvider && comfyConfig) {
      comfyConfig.classList.toggle("hidden", videoProvider.value !== "comfyui");
    }
  };

  const toggleVlmConfig = () => {
    const observerProvider = document.getElementById("observer_provider_id");
    const vlmConfig = document.getElementById("vlm_config");
    if (observerProvider && vlmConfig) {
      vlmConfig.classList.toggle("hidden", observerProvider.value === "prompt-proxy");
    }
  };

  const syncProfileFields = () => {
    const providerProfileSelect = document.getElementById("provider_profile_id");
    if (!providerProfileSelect) {
      return;
    }
    const profile = providerProfiles.find((item) => item.profile_id === providerProfileSelect.value);
    if (!profile) {
      return;
    }
    setValue("provider_profile_name", profile.name);
    setValue("llm_provider_id", profile.llm_provider_id);
    setValue("llm_model", profile.llm_model);
    setValue("llm_base_url", profile.llm_base_url);
    setValue("evaluator_mode", profile.evaluator_mode);
    setValue("generator_provider_id", profile.generator_provider_id);
    setValue("comfyui_base_url", profile.comfyui_base_url);
    setValue("comfyui_workflows_dir", profile.comfyui_workflows_dir);
    setValue("comfyui_workflow_id", profile.comfyui_workflow_id);
    setValue("comfyui_width", profile.comfyui_width);
    setValue("comfyui_height", profile.comfyui_height);
    setValue("comfyui_length", profile.comfyui_length);
    setValue("comfyui_fps", profile.comfyui_fps);
    setValue("comfyui_max_shots", profile.comfyui_max_shots);
    setValue("observer_provider_id", profile.observer_provider_id);
    setValue("vlm_model", profile.vlm_model);
    setValue("vlm_base_url", profile.vlm_base_url);
    setValue("vlm_frame_sample_count", profile.vlm_frame_sample_count);
    setValue("vlm_confidence_threshold", profile.vlm_confidence_threshold);
    const vlmRequireJson = document.getElementById("vlm_require_json");
    if (vlmRequireJson) {
      if (vlmRequireJson.type === "checkbox") {
        vlmRequireJson.checked = profile.vlm_require_json !== false;
      } else {
        vlmRequireJson.value = String(profile.vlm_require_json !== false);
      }
    }
    toggleComfyConfig();
    toggleVlmConfig();
  };

  const renderPreflight = (payload) => {
    const preflightStatus = document.getElementById("preflight_status");
    if (!preflightStatus) {
      return;
    }
    preflightStatus.innerHTML = "";
    const summary = document.createElement("div");
    summary.className = `status-row ${payload.status || "warning"}`;
    const payloadStatus = statusLabels[payload.status] || payload.status || "";
    summary.textContent = `${ui.profile_preflight}: ${payloadStatus} / ${web.js_failed} ${payload.failed || 0} / ${web.js_warnings} ${payload.warnings || 0}`;
    preflightStatus.appendChild(summary);
    for (const check of payload.checks || []) {
      const row = document.createElement("div");
      row.className = `status-row ${check.status}`;
      row.textContent = `${check.label}: ${statusLabels[check.status] || check.status} / ${check.detail}`;
      preflightStatus.appendChild(row);
    }
  };

  for (const trigger of document.querySelectorAll("[data-sf-toggle]")) {
    const targetId = trigger.getAttribute("data-sf-toggle");
    const target = targetId ? document.getElementById(targetId) : null;
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

  const providerProfileSelect = document.getElementById("provider_profile_id");
  if (providerProfileSelect) {
    providerProfileSelect.addEventListener("change", syncProfileFields);
  }
  const videoProvider = document.getElementById("generator_provider_id");
  if (videoProvider) {
    videoProvider.addEventListener("change", toggleComfyConfig);
  }
  toggleComfyConfig();

  const observerProvider = document.getElementById("observer_provider_id");
  if (observerProvider) {
    observerProvider.addEventListener("change", toggleVlmConfig);
  }
  toggleVlmConfig();

  const workspaceLanguageSelect = document.getElementById("workspace_language");
  if (workspaceLanguageSelect) {
    workspaceLanguageSelect.addEventListener("change", () => {
      const url = new URL(window.location.href);
      url.searchParams.set("language", workspaceLanguageSelect.value);
      window.location.href = url.toString();
    });
  }

  const iterationSlider = document.getElementById("max_iterations");
  const iterationValue = document.getElementById("max_iterations_value");
  if (iterationSlider && iterationValue) {
    iterationSlider.addEventListener("input", () => {
      iterationValue.textContent = iterationSlider.value;
    });
  }

  const signalToggle = document.getElementById("show-signals");
  if (signalToggle) {
    signalToggle.addEventListener("change", () => {
      document.body.classList.toggle("show-signals", signalToggle.checked);
    });
  }

  const runForm = document.getElementById("run_form");
  if (runForm) {
    runForm.addEventListener("submit", () => {
      document.body.classList.add("submitting");
      const submit = document.getElementById("run_submit");
      if (submit) {
        submit.disabled = true;
        submit.textContent = ui.js_running;
      }
    });
  }

  const saveProviderProfile = document.getElementById("save_provider_profile");
  if (saveProviderProfile) {
    saveProviderProfile.addEventListener("click", async () => {
      saveProviderProfile.disabled = true;
      try {
        const response = await fetch("/api/provider-profiles", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(currentProviderPayload()),
        });
        if (!response.ok) {
          throw new Error(`${response.status} ${response.statusText}`);
        }
        const payload = await response.json();
        renderPreflight({status: "passed", failed: 0, warnings: 0, checks: [
          {label: ui.profile_label, status: "passed", detail: `${ui.profile_saved} ${payload.profile.profile_id}`},
        ]});
      } catch (error) {
        renderPreflight({status: "failed", failed: 1, warnings: 0, checks: [
          {label: ui.profile_label, status: "failed", detail: `${error}`},
        ]});
      } finally {
        saveProviderProfile.disabled = false;
      }
    });
  }

  const preflightCheck = document.getElementById("preflight_check");
  if (preflightCheck) {
    preflightCheck.addEventListener("click", async () => {
      preflightCheck.disabled = true;
      renderPreflight({status: "warning", failed: 0, warnings: 1, checks: [
        {label: ui.profile_check_label, status: "warning", detail: ui.profile_checking},
      ]});
      try {
        const response = await fetch("/api/preflight", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(currentPreflightPayload()),
        });
        if (!response.ok) {
          throw new Error(`${response.status} ${response.statusText}`);
        }
        renderPreflight(await response.json());
      } catch (error) {
        renderPreflight({status: "failed", failed: 1, warnings: 0, checks: [
          {label: ui.profile_check_label, status: "failed", detail: `${error}`},
        ]});
      } finally {
        preflightCheck.disabled = false;
      }
    });
  }

  const testChain = document.getElementById("test_chain");
  if (testChain) {
    testChain.addEventListener("click", async () => {
      testChain.disabled = true;
      renderPreflight({status: "warning", failed: 0, warnings: 1, checks: [
        {label: ui.profile_test_chain_label, status: "warning", detail: ui.profile_test_chain_running},
      ]});
      try {
        const response = await fetch("/api/test-chain", {method: "POST"});
        if (!response.ok) {
          throw new Error(`${response.status} ${response.statusText}`);
        }
        renderPreflight(await response.json());
      } catch (error) {
        renderPreflight({status: "failed", failed: 1, warnings: 0, checks: [
          {label: ui.profile_test_chain_label, status: "failed", detail: `${error}`},
        ]});
      } finally {
        testChain.disabled = false;
      }
    });
  }

  const workflowSearch = document.getElementById("comfyui_search");
  const workflowSelect = document.getElementById("comfyui_workflow_id");
  if (workflowSearch && workflowSelect) {
    workflowSearch.addEventListener("click", async () => {
      const workflowsDir = document.getElementById("comfyui_workflows_dir");
      const workflowStatus = document.getElementById("comfyui_search_status");
      workflowSearch.disabled = true;
      if (workflowStatus) {
        workflowStatus.textContent = ui.form_comfyui_searching;
      }
      const url = new URL("/api/comfyui/workflows", window.location.origin);
      if (workflowsDir && workflowsDir.value.trim()) {
        url.searchParams.set("root", workflowsDir.value.trim());
      }
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`${response.status} ${response.statusText}`);
        }
        const payload = await response.json();
        const previousValue = workflowSelect.value;
        const workflows = payload.workflows || [];
        workflowSelect.innerHTML = "";
        for (const workflow of workflows) {
          const option = document.createElement("option");
          option.value = workflow.workflow_id;
          option.textContent = workflow.workflow_id + (workflow.callable ? "" : ` / ${ui.js_disabled}`);
          option.disabled = !workflow.callable;
          workflowSelect.appendChild(option);
        }
        if ([...workflowSelect.options].some((option) => option.value === previousValue)) {
          workflowSelect.value = previousValue;
        }
        const localCount = workflows.filter((workflow) => workflow.source === "local").length;
        const callableCount = workflows.filter((workflow) => workflow.callable).length;
        if (workflowStatus) {
          workflowStatus.textContent = workflows.length
            ? `${ui.form_comfyui_search_found}: ${workflows.length} / ${ui.js_local} ${localCount} / ${ui.js_callable} ${callableCount}`
            : ui.form_comfyui_search_empty;
        }
      } catch (error) {
        if (workflowStatus) {
          workflowStatus.textContent = `${ui.form_comfyui_search_failed}: ${error}`;
        }
      } finally {
        workflowSearch.disabled = false;
      }
    });
  }
})();

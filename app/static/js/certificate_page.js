(function () {
  const STORAGE_KEY = "publicCertWizardState";

  function setMessage(element, message) {
    if (!element) {
      return;
    }

    if (message) {
      element.textContent = message;
      element.classList.remove("hidden", "is-hidden");
      element.classList.add("is-visible");
      return;
    }

    element.textContent = "";
    element.classList.add("hidden", "is-hidden");
    element.classList.remove("is-visible");
  }

  function fallbackCopy(text) {
    const helper = document.createElement("textarea");
    helper.value = text;
    helper.setAttribute("readonly", "readonly");
    helper.style.position = "fixed";
    helper.style.opacity = "0";
    document.body.appendChild(helper);
    helper.select();
    helper.setSelectionRange(0, helper.value.length);

    let copied = false;
    try {
      copied = document.execCommand("copy");
    } finally {
      document.body.removeChild(helper);
    }

    return copied;
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }

    return fallbackCopy(text);
  }

  function defaultState() {
    return {
      sessionId: "",
      step: 1,
      domain: "",
      challengeName: "",
      challengeValue: "",
      txtVerified: false,
      issued: false,
    };
  }

  function loadState() {
    try {
      const raw = window.sessionStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return defaultState();
      }
      const parsed = JSON.parse(raw);
      return {
        ...defaultState(),
        ...parsed,
      };
    } catch (_error) {
      return defaultState();
    }
  }

  function persistState(state) {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function setStepState(elements, state) {
    const step = Math.max(1, Math.min(4, Number(state.step) || 1));
    const panels = [
      elements.step1,
      elements.step2,
      elements.step3,
      elements.step4,
    ];

    panels.forEach((panel, index) => {
      const isEnabled = index + 1 <= step;
      panel.classList.toggle("wizard-step-locked", !isEnabled);
      panel.setAttribute("aria-disabled", String(!isEnabled));
    });

    elements.stepMarkers.forEach((marker, index) => {
      marker.classList.toggle("is-active", index + 1 <= step);
    });

    // Show only the active step panel; other panels stay off-canvas.
    elements.stageTrack.style.transform = `translateX(-${(step - 1) * 100}%)`;

    elements.generateButton.disabled = !state.txtVerified;
    elements.downloadButton.disabled = !state.issued;
    elements.step3NextButton.disabled = !state.txtVerified;
  }

  function updateInstructionFields(elements, state) {
    elements.challengeName.textContent = state.challengeName || "Awaiting wizard start";
    elements.challengeValue.textContent = state.challengeValue || "Awaiting wizard start";
  }

  function setPending(elements, isPending) {
    elements.page.dataset.state = isPending ? "pending" : "idle";
    elements.startButton.disabled = isPending;
    elements.verifyButton.disabled = isPending;
    elements.generateButton.disabled = isPending || elements.generateButton.disabled;
  }

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: payload ? JSON.stringify(payload) : null,
    });

    const data = await response.json().catch(function () {
      return null;
    });

    return { response, data };
  }

  async function restoreTxtInstructions(elements, state) {
    if (!state.sessionId || !state.challengeName) {
      return;
    }

    const response = await fetch(`/api/v1/public-cert/wizard/${state.sessionId}/txt`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      return;
    }

    const payload = await response.json();
    state.challengeName = payload.challenge_name;
    state.challengeValue = payload.challenge_value;
    state.step = Math.max(state.step, 2);
    updateInstructionFields(elements, state);
    setStepState(elements, state);
    persistState(state);
  }

  async function handleStart(event, elements, state) {
    event.preventDefault();
    setMessage(elements.validationMessage, "");
    setMessage(elements.apiErrorMessage, "");

    const domain = elements.domainInput.value.trim();

    if (!domain) {
      setMessage(elements.validationMessage, "Domain is required.");
      return;
    }

    setPending(elements, true);
    elements.requestStatus.textContent = "Creating wizard session...";

    try {
      const started = await postJson("/api/v1/public-cert/wizard/start", {
        domain,
      });

      if (!started.response.ok || !started.data) {
        const message = started.data && started.data.message
          ? started.data.message
          : "Unable to start wizard session.";
        setMessage(elements.apiErrorMessage, message);
        elements.requestStatus.textContent = "Wizard start failed.";
        return;
      }

      state.sessionId = started.data.session_id;
      state.domain = domain;
      state.step = 2;
      state.txtVerified = false;
      state.issued = false;

      const txt = await fetch(`/api/v1/public-cert/wizard/${state.sessionId}/txt`, {
        headers: {
          Accept: "application/json",
        },
      });
      const txtPayload = await txt.json().catch(function () {
        return null;
      });

      if (!txt.ok || !txtPayload) {
        setMessage(elements.apiErrorMessage, "Unable to load TXT instructions.");
        elements.requestStatus.textContent = "Wizard start incomplete.";
        return;
      }

      state.challengeName = txtPayload.challenge_name;
      state.challengeValue = txtPayload.challenge_value;
      state.step = 2;

      updateInstructionFields(elements, state);
      setStepState(elements, state);
      persistState(state);
      elements.requestStatus.textContent = "TXT instructions ready. Add the DNS record.";
    } catch (_error) {
      setMessage(elements.apiErrorMessage, "Network error, please retry.");
      elements.requestStatus.textContent = "Wizard start failed.";
    } finally {
      setPending(elements, false);
    }
  }

  async function handleVerify(elements, state) {
    if (!state.sessionId) {
      setMessage(elements.apiErrorMessage, "Start the wizard first.");
      return;
    }

    setMessage(elements.apiErrorMessage, "");
    setPending(elements, true);
    elements.requestStatus.textContent = "Verifying TXT record...";

    try {
      const result = await postJson(
        `/api/v1/public-cert/wizard/${state.sessionId}/verify-txt`,
        {},
      );

      if (!result.response.ok || !result.data) {
        const message = result.data && result.data.message
          ? result.data.message
          : "Verification failed.";
        setMessage(elements.apiErrorMessage, message);
        elements.verificationStatus.textContent = "Verification failed.";
        return;
      }

      const observed = result.data.observed_values || [];
      elements.resolverEvidence.textContent = observed.length
        ? observed.join("\n")
        : "No TXT records observed.";

      if (result.data.verified) {
        state.txtVerified = true;
        state.step = 4;
        elements.verificationStatus.textContent = "TXT verification passed.";
        elements.requestStatus.textContent = "TXT verified. Generation unlocked.";
      } else {
        state.txtVerified = false;
        state.step = Math.max(state.step, 3);
        elements.verificationStatus.textContent = "TXT verification not yet successful.";
        elements.requestStatus.textContent = "Still waiting for DNS propagation.";
      }

      setStepState(elements, state);
      persistState(state);
    } catch (_error) {
      setMessage(elements.apiErrorMessage, "Network error, please retry.");
      elements.verificationStatus.textContent = "Verification failed.";
    } finally {
      setPending(elements, false);
    }
  }

  async function handleGenerate(elements, state) {
    if (!state.sessionId) {
      setMessage(elements.apiErrorMessage, "Start the wizard first.");
      return;
    }

    setMessage(elements.apiErrorMessage, "");
    setPending(elements, true);
    elements.requestStatus.textContent = "Issuing certificate...";

    try {
      const result = await postJson(
        `/api/v1/public-cert/wizard/${state.sessionId}/generate`,
        {},
      );

      if (!result.response.ok || !result.data) {
        const message = result.data && result.data.message
          ? result.data.message
          : "Certificate issuance failed.";
        setMessage(elements.apiErrorMessage, message);
        elements.issuanceStatus.textContent = "Issuance failed.";
        return;
      }

      state.issued = true;
      state.step = 4;
      setStepState(elements, state);
      persistState(state);
      elements.issuanceStatus.textContent = "Certificate issued. Download is ready.";
      elements.requestStatus.textContent = "Ready to download.";
    } catch (_error) {
      setMessage(elements.apiErrorMessage, "Network error, please retry.");
      elements.issuanceStatus.textContent = "Issuance failed.";
    } finally {
      setPending(elements, false);
    }
  }

  function handleDownload(elements, state) {
    if (!state.sessionId || !state.issued) {
      return;
    }

    window.location.href = `/api/v1/public-cert/wizard/${state.sessionId}/download.zip`;
  }

  async function handleCopy(button) {
    const target = document.getElementById(button.dataset.copyTarget);
    if (!target) {
      return;
    }

    const text = target.textContent || "";
    if (!text.trim()) {
      return;
    }

    await copyText(text);
  }

  document.addEventListener("DOMContentLoaded", function () {
    const page = document.getElementById("certificate-page");
    if (!page) {
      return;
    }

    const elements = {
      page: page,
      startForm: document.getElementById("wizard-start-form"),
      startButton: document.getElementById("wizard-start-button"),
      verifyButton: document.getElementById("verify-txt-button"),
      generateButton: document.getElementById("wizard-generate-button"),
      downloadButton: document.getElementById("wizard-download-button"),
      step2NextButton: document.getElementById("step2-next-button"),
      step3NextButton: document.getElementById("step3-next-button"),
      domainInput: document.getElementById("domain-input"),
      challengeName: document.getElementById("challenge-name"),
      challengeValue: document.getElementById("challenge-value"),
      resolverEvidence: document.getElementById("resolver-evidence"),
      verificationStatus: document.getElementById("verification-status"),
      issuanceStatus: document.getElementById("issuance-status"),
      requestStatus: document.getElementById("request-status"),
      validationMessage: document.getElementById("validation-message"),
      apiErrorMessage: document.getElementById("api-error-message"),
      stageTrack: document.getElementById("wizard-stage-track"),
      step1: document.getElementById("wizard-step-1"),
      step2: document.getElementById("wizard-step-2"),
      step3: document.getElementById("wizard-step-3"),
      step4: document.getElementById("wizard-step-4"),
      stepMarkers: Array.from(document.querySelectorAll("[data-step-marker]")),
    };

    const state = loadState();
    elements.domainInput.value = state.domain;

    updateInstructionFields(elements, state);
    setStepState(elements, state);

    void restoreTxtInstructions(elements, state);

    elements.startForm.addEventListener("submit", function (event) {
      void handleStart(event, elements, state);
    });

    elements.verifyButton.addEventListener("click", function () {
      void handleVerify(elements, state);
    });

    elements.generateButton.addEventListener("click", function () {
      void handleGenerate(elements, state);
    });

    elements.downloadButton.addEventListener("click", function () {
      handleDownload(elements, state);
    });

    elements.step2NextButton.addEventListener("click", function () {
      state.step = 3;
      setStepState(elements, state);
      persistState(state);
    });

    elements.step3NextButton.addEventListener("click", function () {
      state.step = 4;
      setStepState(elements, state);
      persistState(state);
    });

    document.querySelectorAll("[data-copy-target]").forEach(function (button) {
      button.addEventListener("click", function () {
        void handleCopy(button);
      });
    });
  });
})();

(function (global) {
  "use strict";

  function renderMissionBoardSection({
    currentStageLabel,
    currentStageDetail,
    currentFocusLabel,
    currentFocusMeta,
    promptStatusLabel,
    promptStatusMeta,
    promptMissionCard,
    verdictMissionCard,
    verdictSummary,
    verdictMeta,
    runtimeBadge,
    officeState,
    formatDuration,
    now = Date.now(),
  }) {
    currentStageLabel.textContent = officeState.currentStageTitle;
    currentStageDetail.textContent = officeState.currentStageSummary;

    currentFocusLabel.textContent = officeState.focusTitle;
    currentFocusMeta.textContent = officeState.focusDetail;

    promptStatusLabel.textContent = officeState.promptPending ? "입력 대기" : "없음";
    promptStatusMeta.textContent = officeState.promptDetail;
    promptMissionCard.classList.toggle("prompt-live", officeState.promptPending);

    verdictMissionCard.classList.remove("verdict-pass", "verdict-pwf", "verdict-reject");
    if (!officeState.lastVerdict) {
      verdictSummary.textContent = "없음";
      verdictMeta.textContent = "아직 심사 결과 없음";
    } else {
      const verdictLabel = officeState.lastVerdict === "PASS_WITH_FIX" ? "PASS_WITH_FIX" : officeState.lastVerdict;
      verdictSummary.textContent = officeState.lastVerdictScore
        ? `${verdictLabel} · ${officeState.lastVerdictScore}점`
        : verdictLabel;
      verdictMeta.textContent = officeState.mode === "RUNNING" ? "다음 판정을 기다리는 중" : "최근 심사 결과를 유지 중";
      if (officeState.lastVerdict === "PASS") {
        verdictMissionCard.classList.add("verdict-pass");
      } else if (officeState.lastVerdict === "PASS_WITH_FIX") {
        verdictMissionCard.classList.add("verdict-pwf");
      } else if (officeState.lastVerdict === "REJECT") {
        verdictMissionCard.classList.add("verdict-reject");
      }
    }

    if (officeState.isRunning && officeState.runStartedAt) {
      runtimeBadge.textContent = `경과: ${formatDuration(now - officeState.runStartedAt)}`;
    } else {
      runtimeBadge.textContent = "경과: --:--";
    }
  }

  function refreshBackendStatusBadge({
    readyBadge,
    backendConnected = false,
    commandReady = false,
  }) {
    if (backendConnected && commandReady) {
      readyBadge.textContent = "이벤트 연결됨 / 명령 가능";
      return;
    }
    if (backendConnected) {
      readyBadge.textContent = "이벤트 연결됨 / 명령 점검 중";
      return;
    }
    if (commandReady) {
      readyBadge.textContent = "이벤트 재연결 대기 / 명령 가능";
      return;
    }
    readyBadge.textContent = "백엔드 점검 필요";
  }

  function setStateBadge({
    stateBadge,
    mode,
  }) {
    stateBadge.classList.remove("state-running", "state-idle", "state-pass", "state-pwf", "state-reject");

    if (mode === "RUNNING") {
      stateBadge.classList.add("state-running");
      stateBadge.textContent = "상태: RUNNING";
    } else if (mode === "IDLE") {
      stateBadge.classList.add("state-idle");
      stateBadge.textContent = "상태: IDLE";
    } else if (mode === "PASS") {
      stateBadge.classList.add("state-pass");
      stateBadge.textContent = "상태: PASS";
    } else if (mode === "PASS_WITH_FIX") {
      stateBadge.classList.add("state-pwf");
      stateBadge.textContent = "상태: PASS_WITH_FIX";
    } else if (mode === "REJECT") {
      stateBadge.classList.add("state-reject");
      stateBadge.textContent = "상태: REJECT";
    }
  }

  function setEffectBanner({
    effectBanner,
    text,
    className,
  }) {
    effectBanner.textContent = text;
    effectBanner.classList.remove("pass", "pwf", "reject", "show");
    if (!text) return;
    effectBanner.classList.add(className, "show");
  }

  function setLastActionText({
    lastAction,
    label,
    key,
    action,
  }) {
    lastAction.textContent = `최근 클릭: ${label} (key: ${key || action})`;
  }

  function buildLogRow({
    message,
    verdict,
    rowMeta,
    currentSubKey = null,
    getAgentDisplayName,
    resolveActionMeta,
    nowLabel,
  }) {
    const row = document.createElement("div");
    row.className = "log-row";
    row.dataset.agent = rowMeta.agent || "";
    row.dataset.stage = rowMeta.stage || "";

    const time = document.createElement("span");
    time.className = "log-time";
    time.textContent = nowLabel();

    const main = document.createElement("div");
    main.className = "log-main";

    const metaRow = document.createElement("div");
    metaRow.className = "log-meta-row";
    if (rowMeta.agent) {
      const agentChip = document.createElement("span");
      agentChip.className = "log-chip log-chip-agent";
      agentChip.textContent = getAgentDisplayName(rowMeta.agent);
      metaRow.appendChild(agentChip);
    }
    if (rowMeta.stage) {
      const stageChip = document.createElement("span");
      stageChip.className = "log-chip log-chip-stage";
      stageChip.textContent = resolveActionMeta(rowMeta.stage, currentSubKey).title;
      metaRow.appendChild(stageChip);
    }

    const msg = document.createElement("span");
    msg.className = "log-msg";
    msg.textContent = message;

    if (metaRow.childNodes.length > 0) {
      main.appendChild(metaRow);
    }
    main.appendChild(msg);
    row.append(time, main);

    if (verdict) {
      const badge = document.createElement("span");
      badge.className = "verdict-badge";
      if (verdict === "PASS") {
        badge.classList.add("verdict-pass");
        badge.textContent = "PASS";
      } else if (verdict === "REJECT") {
        badge.classList.add("verdict-reject");
        badge.textContent = "REJECT";
      } else {
        badge.classList.add("verdict-pwf");
        badge.textContent = "PWF";
      }
      row.appendChild(badge);
    }

    return {
      row,
      timeText: time.textContent,
    };
  }

  function renderMaterialEmpty({
    container,
    message,
  }) {
    container.innerHTML = `<div class="material-empty">${message}</div>`;
  }

  function buildMaterialFileItem({
    file,
    folder,
    formatSize,
    escapeHtml,
    onDelete,
  }) {
    const item = document.createElement("div");
    item.className = "material-file-item";
    const safeFileName = escapeHtml(file.name);
    item.innerHTML = `<span class="file-name" title="${safeFileName}">${safeFileName}</span>`
      + `<span class="file-size">${formatSize(file.size)}</span>`
      + `<button type="button" class="file-del" title="삭제">✕</button>`;
    item.querySelector(".file-del").addEventListener("click", () => onDelete(folder, file.name));
    return item;
  }

  function setWorkspaceView({
    viewName,
    buttons = [],
    views = [],
  }) {
    buttons.forEach((button) => {
      button.classList.toggle("active", button.dataset.view === viewName);
    });
    views.forEach((view) => {
      view.classList.toggle("active", view.dataset.view === viewName);
    });
  }

  function buildWorkspacePanel({
    document,
    title,
    subtitle = "",
  }) {
    const panel = document.createElement("article");
    panel.className = "panel";

    const titleEl = document.createElement("h2");
    titleEl.className = "panel-title";
    titleEl.textContent = title;
    panel.appendChild(titleEl);

    if (subtitle) {
      const subEl = document.createElement("p");
      subEl.className = "panel-sub";
      subEl.textContent = subtitle;
      panel.appendChild(subEl);
    }

    return panel;
  }

  function createWorkspaceScaffold({
    document,
    viewSpecs = [],
    onSelectView,
  }) {
    const workspaceNav = document.createElement("nav");
    workspaceNav.className = "workspace-nav";
    workspaceNav.id = "workspaceNav";

    const workspaceHost = document.createElement("div");
    workspaceHost.className = "workspace-host";

    const viewMap = {};
    viewSpecs.forEach(({ key, label }) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "workspace-nav-btn";
      button.dataset.view = key;
      button.textContent = label;
      button.addEventListener("click", () => onSelectView(key));
      workspaceNav.appendChild(button);

      const view = document.createElement("section");
      view.className = `workspace-view ${key}-view`;
      view.dataset.view = key;
      workspaceHost.appendChild(view);
      viewMap[key] = view;
    });

    return {
      workspaceNav,
      workspaceHost,
      viewMap,
    };
  }

  function buildProjectActionRow({
    document,
    onSaveProject,
    onOpenSettings,
    saveLabel,
    settingsLabel,
  }) {
    const actionRow = document.createElement("div");
    actionRow.className = "project-form-actions";

    const projectSaveBtn = document.createElement("button");
    projectSaveBtn.type = "button";
    projectSaveBtn.className = "top-action";
    projectSaveBtn.textContent = saveLabel;
    projectSaveBtn.addEventListener("click", onSaveProject);

    const projectOpenSettingsBtn = document.createElement("button");
    projectOpenSettingsBtn.type = "button";
    projectOpenSettingsBtn.className = "top-action";
    projectOpenSettingsBtn.textContent = settingsLabel;
    projectOpenSettingsBtn.addEventListener("click", onOpenSettings);

    actionRow.append(projectSaveBtn, projectOpenSettingsBtn);
    return actionRow;
  }

  function mountRunWorkspace({
    document,
    runView,
    runPanel,
    logPanel,
    titleText,
    subtitleText,
  }) {
    const runTitle = runPanel.querySelector(".panel-title");
    const runSub = runPanel.querySelector(".panel-sub");
    if (runTitle) runTitle.textContent = titleText;
    if (runSub) runSub.textContent = subtitleText;

    const runShell = document.createElement("div");
    runShell.className = "workspace-shell";
    const runMainCol = document.createElement("div");
    runMainCol.className = "workspace-main-col";
    runView.appendChild(runShell);
    runShell.append(runPanel, runMainCol);
    runMainCol.appendChild(logPanel);
  }

  function mountQualityWorkspace({
    document,
    qualityView,
    qualityRadarPanel,
    qualityInsightGrid,
    agentBoardNode,
    eventFeedNode,
  }) {
    if (qualityRadarPanel) qualityView.appendChild(qualityRadarPanel);
    if (qualityInsightGrid) qualityView.appendChild(qualityInsightGrid);

    if (agentBoardNode) {
      const agentPanel = buildWorkspacePanel({
        document,
        title: "Agent Board",
        subtitle: "에이전트 상태와 최근 발화 흔적",
      });
      agentPanel.classList.add("quality-page-panel", "agent-board-panel");
      agentPanel.appendChild(agentBoardNode);
      qualityView.appendChild(agentPanel);
    }

    if (eventFeedNode) {
      const feedPanel = buildWorkspacePanel({
        document,
        title: "Event Feed",
        subtitle: "최근 주요 이벤트와 런타임 신호",
      });
      feedPanel.classList.add("quality-page-panel", "event-feed-panel");
      feedPanel.appendChild(eventFeedNode);
      qualityView.appendChild(feedPanel);
    }

    const qualityShell = document.createElement("div");
    qualityShell.className = "quality-page-shell";
    while (qualityView.firstChild) {
      qualityShell.appendChild(qualityView.firstChild);
    }
    qualityView.appendChild(qualityShell);
  }

  function mountOfficeWorkspace({
    document,
    officeView,
    officePanel,
  }) {
    officePanel.classList.add("office-page-panel");
    const officeShell = document.createElement("div");
    officeShell.className = "workspace-shell single";
    officeShell.appendChild(officePanel);
    officeView.appendChild(officeShell);
  }

  function mountProjectWorkspace({
    document,
    projectView,
    materialAccordion,
    projectTab,
    projectTabButton,
  }) {
    const projectShell = document.createElement("div");
    projectShell.className = "project-shell";
    projectView.appendChild(projectShell);

    const projectMaterialsPanel = buildWorkspacePanel({
      document,
      title: "재료",
      subtitle: "Bible, Treatment, 그리고 프로젝트 준비물",
    });
    const projectConfigPanel = buildWorkspacePanel({
      document,
      title: "프로젝트 설정",
      subtitle: "작품 가드와 작가 지시사항을 여기서 관리합니다.",
    });
    projectShell.append(projectMaterialsPanel, projectConfigPanel);

    if (materialAccordion) {
      projectMaterialsPanel.appendChild(materialAccordion);
    }

    projectTabButton?.remove();
    projectTab.classList.remove("tab-content", "active");
    projectTab.classList.add("project-page-content");
    projectConfigPanel.appendChild(projectTab);

    return {
      projectShell,
      projectMaterialsPanel,
      projectConfigPanel,
    };
  }

  function setAccordionCollapsed({
    document,
    targetId,
    collapsed,
  }) {
    const body = document.getElementById(targetId);
    const header = document.querySelector(`.category-header[data-target="${targetId}"]`);
    if (!body || !header) return;
    body.classList.toggle("collapsed", collapsed);
    header.classList.toggle("collapsed", collapsed);
  }

  function toggleAccordionCollapsed({
    document,
    header,
  }) {
    const targetId = header?.dataset?.target;
    if (!targetId) return false;
    const body = document.getElementById(targetId);
    if (!body) return false;
    const isCollapsed = body.classList.toggle("collapsed");
    header.classList.toggle("collapsed", isCollapsed);
    return isCollapsed;
  }

  function updateGenreGating({
    hasGenre,
    buttons = [],
    hint = null,
    subMenu = null,
  }) {
    buttons.forEach((btn) => {
      btn.disabled = !hasGenre;
    });
    if (hint) {
      hint.classList.toggle("show", !hasGenre);
    }
    if (!hasGenre && subMenu) {
      subMenu.classList.remove("open");
    }
  }

  function setSettingsTab({
    tabButtons = [],
    tabContents = [],
    tabId,
  }) {
    let activeTabId = tabId;
    if (!tabContents.some((content) => content.id === activeTabId)) {
      activeTabId = tabButtons.find((button) => !button.disabled)?.dataset.tab || tabButtons[0]?.dataset.tab || "";
    }
    tabButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.tab === activeTabId);
    });
    tabContents.forEach((content) => {
      content.classList.toggle("active", content.id === activeTabId);
    });
  }

  function setSettingsOverlayOpen({
    settingsOverlay,
    isOpen,
  }) {
    settingsOverlay.classList.toggle("open", isOpen);
  }

  function setGenreModalOpen({
    genreModal,
    isOpen,
  }) {
    genreModal.classList.toggle("open", isOpen);
  }

  function setGenreConfirmModalOpen({
    genreConfirmModal,
    isOpen,
  }) {
    genreConfirmModal.classList.toggle("open", isOpen);
  }

  function setPromptOverlayOpen({
    promptOverlay,
    isOpen,
  }) {
    promptOverlay.classList.toggle("open", isOpen);
  }

  function setPromptState({
    officeState,
    pending,
    detail,
    onRenderMissionBoard,
  }) {
    officeState.promptPending = !!pending;
    officeState.promptDetail = detail || (pending ? "사용자 입력을 기다리는 중" : "대기 중인 입력 없음");
    onRenderMissionBoard();
  }

  function setVerdictState({
    officeState,
    verdict,
    score,
    onRenderMissionBoard,
  }) {
    officeState.lastVerdict = verdict || null;
    officeState.lastVerdictScore = score || null;
    onRenderMissionBoard();
  }

  function setActionState({
    officeState,
    action,
    label,
    subKey,
    resolveActionMeta,
    onRenderMissionBoard,
    onRenderPipelineStrip,
    onRenderAgentBoard,
  }) {
    const meta = resolveActionMeta(action, subKey);
    officeState.currentStage = action;
    officeState.currentSubKey = subKey || null;
    officeState.currentStageTitle = label || meta.title;
    officeState.currentStageSummary = meta.summary;
    onRenderMissionBoard();
    onRenderPipelineStrip();
    onRenderAgentBoard();
  }

  function pushEventFeed({
    officeState,
    entry,
    nowLabel,
    onRenderEventFeed,
  }) {
    if (!entry || !entry.title) return;
    officeState.recentEvents.unshift({
      time: entry.time || nowLabel(),
      title: entry.title,
      detail: entry.detail || "",
      agent: entry.agent || null,
    });
    officeState.recentEvents = officeState.recentEvents.slice(0, 8);
    onRenderEventFeed();
  }

  function updateGenreModalState({
    currentGenre,
    genreLabels = {},
    genreCurrentLabel,
    genreItems = [],
  }) {
    const label = currentGenre ? genreLabels[currentGenre] : "없음";
    genreCurrentLabel.textContent = `현재 선택: ${label}`;
    genreItems.forEach((item) => {
      item.classList.toggle("selected", item.dataset.genre === currentGenre);
    });
  }

  function updateToggleLabels({
    toggleSkip,
    toggleMute,
    skipAnimation,
    mute,
  }) {
    toggleSkip.textContent = `Skip animation: ${skipAnimation ? "ON" : "OFF"}`;
    toggleMute.textContent = `Mute: ${mute ? "ON" : "OFF"}`;
    toggleSkip.classList.toggle("active", skipAnimation);
    toggleMute.classList.toggle("active", mute);
  }

  function setLogPanelCollapsed({
    logPanel,
    logToggleBtn,
  }) {
    const collapsed = logPanel.classList.toggle("log-panel-collapsible");
    logToggleBtn.textContent = collapsed ? "펼치기" : "접기";
    return collapsed;
  }

  function applyLogFilter({
    logSearchInput,
    logFilterSelect,
    logStream,
  }) {
    const search = (logSearchInput.value || "").toLowerCase();
    const filter = logFilterSelect.value;
    const rows = logStream.querySelectorAll(".log-row");
    for (const row of rows) {
      const msg = (row.textContent || "").toLowerCase();
      const badge = row.querySelector(".verdict-badge");
      const badgeText = badge ? badge.textContent.trim() : "";
      let show = true;
      if (search && !msg.includes(search)) {
        show = false;
      }
      if (filter && filter !== badgeText) {
        show = false;
      }
      row.style.display = show ? "" : "none";
    }
  }

  global.GeuldobiRendererStateBootstrap = {
    renderMissionBoardSection,
    refreshBackendStatusBadge,
    setStateBadge,
    setEffectBanner,
    setLastActionText,
    buildLogRow,
    renderMaterialEmpty,
    buildMaterialFileItem,
    setWorkspaceView,
    buildWorkspacePanel,
    createWorkspaceScaffold,
    buildProjectActionRow,
    mountRunWorkspace,
    mountQualityWorkspace,
    mountOfficeWorkspace,
    mountProjectWorkspace,
    setAccordionCollapsed,
    toggleAccordionCollapsed,
    updateGenreGating,
    setSettingsTab,
    setSettingsOverlayOpen,
    setGenreModalOpen,
    setGenreConfirmModalOpen,
    setPromptOverlayOpen,
    setPromptState,
    setVerdictState,
    setActionState,
    pushEventFeed,
    updateGenreModalState,
    updateToggleLabels,
    setLogPanelCollapsed,
    applyLogFilter,
  };
})(window);

(function (global) {
  "use strict";

  function renderInsights(renderers = {}) {
    const ordered = [
      "renderSafeOpsPreview",
      "renderArtifactLadder",
      "renderRetrievalInspector",
      "renderResultSummary",
      "renderTrendCompare",
      "renderFailureWatch",
      "renderCalibrationDesk",
    ];
    for (const key of ordered) {
      if (typeof renderers[key] === "function") {
        renderers[key]();
      }
    }
  }

  function renderQualityRadarSection({
    qualityRadar,
    qualityRadarTitle,
    qualityRadarMeta,
    qualityRadarFoot,
    summary,
    project,
    renderQualityRadarReactCards,
    renderQualityRadarFoot,
    QUALITY_SIGNAL_META,
    sanitizeToken,
    buildSparklineSvg,
    describeSignal,
    escapeHtml,
  }) {
    qualityRadar.innerHTML = "";

    if (!project) {
      qualityRadarTitle.textContent = "최근 품질 신호";
      qualityRadarMeta.textContent = "프로젝트를 선택하면 최근 5화 기준 신호를 표시합니다";
      qualityRadarFoot.textContent = "프로젝트가 아직 선택되지 않았습니다.";
      if (
        renderQualityRadarReactCards(summary, {
          label: "No Project",
          meta: "PASS 원고가 쌓이면 CED, AI Slop, gzip, Rhythm, Density가 표시됩니다.",
        })
      ) {
        return;
      }
      const empty = document.createElement("div");
      empty.className = "quality-signal-card is-empty";
      empty.innerHTML =
        '<div class="quality-signal-label">No Project</div><div class="quality-signal-meta">PASS 원고가 쌓이면 CED, AI Slop, gzip, Rhythm, Density가 표시됩니다.</div>';
      qualityRadar.appendChild(empty);
      return;
    }

    const projectLabel = summary.project || project;
    qualityRadarTitle.textContent = `${projectLabel} · Quality Radar`;

    if (!summary.available) {
      qualityRadarMeta.textContent = "최근 PASS 원고가 아직 없거나 신호를 불러오지 못했습니다";
      qualityRadarFoot.textContent = "Stage 4 PASS 원고가 저장되면 이 패널이 최근 5화 기준 상대 추세를 보여줍니다.";
      if (
        renderQualityRadarReactCards(summary, {
          label: "Signals Pending",
          meta: "신규 프로젝트이거나 아직 품질 신호가 기록되지 않았습니다.",
        })
      ) {
        return;
      }
      const empty = document.createElement("div");
      empty.className = "quality-signal-card is-empty";
      empty.innerHTML =
        '<div class="quality-signal-label">Signals Pending</div><div class="quality-signal-meta">신규 프로젝트이거나 아직 품질 신호가 기록되지 않았습니다.</div>';
      qualityRadar.appendChild(empty);
      return;
    }

    qualityRadarMeta.textContent = `ep ${summary.latest_ep || "-"} · 최근 ${summary.lookback || 5}화 median 대비 상대 위치`;
    if (renderQualityRadarReactCards(summary)) {
      renderQualityRadarFoot(summary);
      return;
    }

    for (const [key, meta] of Object.entries(QUALITY_SIGNAL_META)) {
      const stat = summary.signals?.[key] || {};
      const card = document.createElement("div");
      const signalStatus = sanitizeToken(stat.status, "watch");
      card.className = `quality-signal-card is-${signalStatus}`;

      const deltaValue = Number(stat.delta || 0);
      const trendMap = { up: "상승", down: "하강", flat: "유지" };
      const deltaSign = deltaValue > 0 ? "+" : "";
      const valueText = escapeHtml(meta.format(stat.value || 0));
      const medianText = escapeHtml(meta.format(stat.median || 0));
      const recentValues = (summary.recent || []).map((row) => row?.[meta.field]);
      const sparkMarkup = buildSparklineSvg(recentValues, stat.status || "watch");
      const signalReason = escapeHtml(describeSignal(key, stat));

      card.innerHTML = `
        <div class="quality-signal-label">${meta.label}</div>
        <div class="quality-signal-value">${valueText}</div>
        <div class="quality-signal-meta">${meta.hint}</div>
        <div class="quality-signal-spark">${sparkMarkup || ""}</div>
        <div class="quality-signal-meta">median ${medianText}</div>
        <div class="quality-signal-meta">${trendMap[stat.trend] || "유지"} · Δ ${deltaSign}${meta.format(deltaValue)}</div>
        <div class="quality-signal-reason">${signalReason}</div>
      `;
      qualityRadar.appendChild(card);
    }

    renderQualityRadarFoot(summary);
  }

  function renderResultSummarySection({
    resultSummaryTitle,
    resultSummaryMeta,
    resultVerdictBadge,
    resultSummaryHeadline,
    resultSummaryReason,
    resultSignalAlerts,
    resultFixNow,
    resultKeepNext,
    resultAvoidNext,
    resultIssueList,
    resultNextAction,
    project,
    result,
    renderResultSummaryCopyReact,
    renderResultSignalAlertsReact,
    renderResultActionGridReact,
    renderResultIssueListReact,
    renderResultNextActionReact,
    appendInsightEmpty,
  }) {
    resultSummaryTitle.textContent = project ? `${project} · 최근 심사 결과` : "최근 심사 결과";
    resultSummaryMeta.textContent = result.available
      ? `ep ${result.ep_num || "-"} 기준 verdict · 즉시 행동 가이드`
      : "프로젝트를 선택하면 최근 심사 결과와 즉시 행동 가이드를 표시합니다";

    resultVerdictBadge.className = "verdict-badge";
    if (!result.available) {
      resultVerdictBadge.textContent = "대기";
      if (
        !renderResultSummaryCopyReact(
          "최근 결과가 아직 없습니다.",
          "Stage 4 PASS/PWF/REJECT 결과가 기록되면 여기에 핵심 요약이 표시됩니다."
        )
      ) {
        resultSummaryHeadline.textContent = "최근 결과가 아직 없습니다.";
        resultSummaryReason.textContent = "Stage 4 PASS/PWF/REJECT 결과가 기록되면 여기에 핵심 요약이 표시됩니다.";
      }
      if (!renderResultSignalAlertsReact([])) {
        resultSignalAlerts.innerHTML = "";
      }
      if (
        !renderResultActionGridReact([
          { label: "Fix Now", copy: "지금 고칠 포인트가 여기에 표시됩니다." },
          { label: "Keep Next", copy: "다음 화에 유지할 강점이 여기에 표시됩니다." },
          { label: "Avoid Next", copy: "다음 화에서 피할 반복 패턴이 여기에 표시됩니다." },
        ])
      ) {
        resultFixNow.textContent = "지금 고칠 포인트가 여기에 표시됩니다.";
        resultKeepNext.textContent = "다음 화에 유지할 강점이 여기에 표시됩니다.";
        resultAvoidNext.textContent = "다음 화에서 피할 반복 패턴이 여기에 표시됩니다.";
      }
      if (!renderResultIssueListReact([], "이번 화의 핵심 이슈 3개가 여기에 표시됩니다.")) {
        resultIssueList.innerHTML = "";
        appendInsightEmpty(resultIssueList, "이번 화의 핵심 이슈 3개가 여기에 표시됩니다.");
      }
      if (!renderResultNextActionReact("다음 행동 추천이 여기에 표시됩니다.")) {
        resultNextAction.textContent = "다음 행동 추천이 여기에 표시됩니다.";
      }
      return;
    }

    const verdict = String(result.verdict || "").toUpperCase();
    resultVerdictBadge.textContent = verdict || "UNKNOWN";
    if (verdict === "PASS") resultVerdictBadge.classList.add("is-pass");
    else if (verdict === "PASS_WITH_FIX") resultVerdictBadge.classList.add("is-pwf");
    else if (verdict === "REJECT") resultVerdictBadge.classList.add("is-reject");

    if (
      !renderResultSummaryCopyReact(
        result.headline || "최근 심사 결과",
        result.selection_reason || result.open_review || "Director selection reason이 아직 없습니다."
      )
    ) {
      resultSummaryHeadline.textContent = result.headline || "최근 심사 결과";
      resultSummaryReason.textContent =
        result.selection_reason || result.open_review || "Director selection reason이 아직 없습니다.";
    }

    const alerts = result.signal_alerts || [];
    if (!renderResultSignalAlertsReact(alerts)) {
      resultSignalAlerts.innerHTML = "";
    }
    if (alerts.length && !global.React) {
      for (const alertText of alerts) {
        const chip = document.createElement("span");
        chip.className = "signal-alert-chip";
        chip.textContent = alertText;
        resultSignalAlerts.appendChild(chip);
      }
    }

    const fixNow = (result.fix_now || []).slice(0, 3);
    if (
      !renderResultActionGridReact([
        {
          label: "Fix Now",
          copy: fixNow.length ? fixNow.join(" · ") : "즉시 고쳐야 할 경고가 아직 없습니다.",
        },
        {
          label: "Keep Next",
          copy: result.keep_next || "다음 화에 유지할 강점이 아직 정리되지 않았습니다.",
        },
        {
          label: "Avoid Next",
          copy: result.avoid_next || "다음 화에서 피할 반복 패턴이 아직 정리되지 않았습니다.",
        },
      ])
    ) {
      resultFixNow.textContent = fixNow.length ? fixNow.join(" · ") : "즉시 고쳐야 할 경고가 아직 없습니다.";
      resultKeepNext.textContent = result.keep_next || "다음 화에 유지할 강점이 아직 정리되지 않았습니다.";
      resultAvoidNext.textContent = result.avoid_next || "다음 화에서 피할 반복 패턴이 아직 정리되지 않았습니다.";
    }

    const issues = result.issues || [];
    if (
      !renderResultIssueListReact(
        issues,
        "이번 화에서 즉시 강조할 이슈가 없거나 아직 집계되지 않았습니다."
      )
    ) {
      resultIssueList.innerHTML = "";
    }
    if (!issues.length && !global.React) {
      appendInsightEmpty(resultIssueList, "이번 화에서 즉시 강조할 이슈가 없거나 아직 집계되지 않았습니다.");
    } else if (issues.length && !global.React) {
      for (const issue of issues.slice(0, 3)) {
        const item = document.createElement("li");
        item.className = "issue-item";
        item.textContent = issue;
        resultIssueList.appendChild(item);
      }
    }

    if (!renderResultNextActionReact(result.next_action || "다음 행동 추천이 없습니다.")) {
      resultNextAction.textContent = result.next_action || "다음 행동 추천이 없습니다.";
    }
  }

  function renderRetrievalInspectorSection({
    retrievalInspectorMeta,
    retrievalSummaryStrip,
    retrievalStageGrid,
    retrievalWarningList,
    retrievalRecentList,
    retrievalInspectorHint,
    project,
    retrieval,
    renderRetrievalSummaryStripReact,
    renderRetrievalStageGridReact,
    renderRetrievalWarningListReact,
    renderRetrievalRecentListReact,
    appendInsightEmpty,
    escapeHtml,
  }) {
    retrievalInspectorMeta.textContent = project
      ? `${project} 최근 retrieval 관측과 coverage 경고`
      : "프로젝트를 선택하면 최근 retrieval 관측이 표시됩니다";

    retrievalSummaryStrip.innerHTML = "";
    const summaryChips = retrieval.available
      ? [
          `관측 ${retrieval.total_observations || 0}건`,
          `Stage ${((retrieval.stage_rows || []).map((row) => row.stage).join(", ") || "-")}`,
          `반복 경고 ${((retrieval.top_warnings || []).length || 0)}종`,
        ]
      : ["관측 0건", "retrieval summary 대기", "coverage 경고 없음"];
    if (!renderRetrievalSummaryStripReact(summaryChips)) {
      for (const label of summaryChips) {
        const chip = document.createElement("span");
        chip.className = "trend-chip";
        chip.textContent = label;
        retrievalSummaryStrip.appendChild(chip);
      }
    }

    retrievalStageGrid.innerHTML = "";
    const stageRows = retrieval.stage_rows || [];
    if (!renderRetrievalStageGridReact(stageRows, "Stage별 retrieval 관측이 아직 없습니다.")) {
      retrievalStageGrid.innerHTML = "";
    }
    if (!stageRows.length && !global.React) {
      appendInsightEmpty(retrievalStageGrid, "Stage별 retrieval 관측이 아직 없습니다.");
    } else if (stageRows.length && !global.React) {
      for (const row of stageRows.slice(0, 4)) {
        const card = document.createElement("div");
        card.className = "retrieval-stage-card";
        const workRate = Math.round(Number(row.work_focus_rate || 0) * 100);
        const summaryRate = Math.round(Number(row.summary_included_rate || 0) * 100);
        const relationRate = Math.round(Number(row.relation_slice_rate || 0) * 100);
        const warningRate = Math.round(Number(row.coverage_warning_rate || 0) * 100);
        const stageLabel = escapeHtml(row.stage || "unknown");
        card.innerHTML = `
          <div class="retrieval-stage-label">${stageLabel}</div>
          <div class="retrieval-stage-value">${summaryRate}%</div>
          <div class="retrieval-stage-meta">summary slot 포함률</div>
          <div class="retrieval-stage-meta">work focus ${workRate}% · relation slice ${relationRate}%</div>
          <div class="retrieval-stage-meta">coverage warning ${warningRate}% · 표본 ${row.total || 0}건</div>
        `;
        retrievalStageGrid.appendChild(card);
      }
    }

    retrievalWarningList.innerHTML = "";
    const warnings = retrieval.top_warnings || [];
    if (
      !renderRetrievalWarningListReact(
        warnings,
        "반복적으로 관찰된 retrieval 경고가 아직 없습니다."
      )
    ) {
      retrievalWarningList.innerHTML = "";
    }
    if (!warnings.length && !global.React) {
      appendInsightEmpty(retrievalWarningList, "반복적으로 관찰된 retrieval 경고가 아직 없습니다.");
    } else if (warnings.length && !global.React) {
      for (const row of warnings.slice(0, 6)) {
        const item = document.createElement("div");
        item.className = "pattern-item";
        const warningLabel = escapeHtml(row.warning || "unknown_warning");
        item.innerHTML = `
          <div class="pattern-item-title">${warningLabel}</div>
          <div class="pattern-item-meta">누적 ${row.count || 0}회</div>
        `;
        retrievalWarningList.appendChild(item);
      }
    }

    retrievalRecentList.innerHTML = "";
    const recent = retrieval.recent || [];
    if (!renderRetrievalRecentListReact(recent, "최근 retrieval 샘플이 아직 없습니다.")) {
      retrievalRecentList.innerHTML = "";
    }
    if (!recent.length && !global.React) {
      appendInsightEmpty(retrievalRecentList, "최근 retrieval 샘플이 아직 없습니다.");
    } else if (recent.length && !global.React) {
      for (const row of recent.slice(0, 6)) {
        const item = document.createElement("div");
        item.className = "pattern-item";
        const sources = Object.entries(row.source_counts || {})
          .map(([key, value]) => `${key} ${value}`)
          .join(" · ");
        const warningsText = (row.coverage_warnings || []).join(" · ");
        const stageLabel = escapeHtml(String(row.stage || "unknown").toUpperCase());
        const safeSources = escapeHtml(sources || "source count 없음");
        const safeWarningsText = escapeHtml(warningsText || "coverage warning 없음");
        item.innerHTML = `
          <div class="pattern-item-title">ep ${row.ep_num ?? "-"} · ${stageLabel}</div>
          <div class="pattern-item-meta">summary ${row.work_slot_summary_included ? "yes" : "no"} · relation ${row.relation_slice_included ? "yes" : "no"}</div>
          <div class="pattern-item-meta">${safeSources}</div>
          <div class="pattern-item-meta">${safeWarningsText}</div>
        `;
        retrievalRecentList.appendChild(item);
      }
    }

    const topWarning = warnings[0]?.warning;
    retrievalInspectorHint.textContent = topWarning
      ? `지금 가장 반복되는 retrieval 문제는 ${topWarning} 입니다. 이 경고가 많은 stage부터 summary slot / relation slice를 점검하세요.`
      : "retrieval 경고가 거의 없거나 아직 충분한 관측이 없습니다.";
  }

  function renderSafeOpsPreviewSection({
    safeOpsMeta,
    safeOpsGrid,
    safeOpsHint,
    project,
    safeOps,
    renderSafeOpsGridReact,
    appendInsightEmpty,
    escapeHtml,
    formatSafeOpsImpactCounts,
  }) {
    safeOpsMeta.textContent = project
      ? `${project} · latest ep ${safeOps.latest_ep || 0} · Arc ${safeOps.arc_count || 0}개`
      : "프로젝트를 선택하면 삭제/유지 범위를 미리 보여줍니다";
    safeOpsGrid.innerHTML = "";

    if (!project) {
      appendInsightEmpty(safeOpsGrid, "프로젝트를 선택하면 운영 작업별 영향 범위가 표시됩니다.");
      safeOpsHint.textContent = "운영 버튼을 누르기 전, 무엇이 지워지고 무엇이 남는지 여기서 먼저 확인합니다.";
      return;
    }

    const actionOrder = ["rollback", "wipe", "reset", "rewind"];
    const actionRows = actionOrder
      .map((key) => ({ key, action: safeOps.actions?.[key] }))
      .filter((row) => Boolean(row.action));
    if (!renderSafeOpsGridReact(actionRows, "운영 작업 preview가 아직 없습니다.")) {
      safeOpsGrid.innerHTML = "";
    }
    if (!actionRows.length && !global.React) {
      appendInsightEmpty(safeOpsGrid, "운영 작업 preview가 아직 없습니다.");
    } else if (actionRows.length && !global.React) {
      for (const { key, action } of actionRows) {
        const card = document.createElement("div");
        card.className = "safe-ops-card";
        const actionTitle = escapeHtml(action.title || key);
        const targetLabel = action.requires_target ? "target 필요" : "즉시 preview";
        const actionSummary = escapeHtml(action.summary || "");
        const actionImpact = escapeHtml(formatSafeOpsImpactCounts(action));
        const actionNote = escapeHtml((action.notes || [])[0] || "추가 메모 없음");
        card.innerHTML = `
          <div class="safe-ops-card-head">
            <span class="safe-ops-card-title">${actionTitle}</span>
            <span class="safe-ops-chip ${action.requires_target ? "is-target" : ""}">
              ${targetLabel}
            </span>
          </div>
          <div class="safe-ops-card-copy">${actionSummary}</div>
          <div class="safe-ops-card-impact"><strong>영향</strong> · ${actionImpact}</div>
          <div class="safe-ops-card-note">${actionNote}</div>
        `;
        safeOpsGrid.appendChild(card);
      }
    }

    safeOpsHint.textContent = safeOps.hint || "Rollback/Wipe/Reset/Rewind의 삭제/유지 범위를 확인하세요.";
  }

  function renderArtifactLadderSection({
    artifactLadderMeta,
    artifactLadderHint,
    artifactSupportRow,
    artifactLadderGrid,
    project,
    artifact,
    renderArtifactLadderReact,
    appendInsightEmpty,
    buildArtifactFallbackHint,
    sanitizeToken,
    escapeHtml,
    getArtifactStatusLabel,
  }) {
    artifactLadderMeta.textContent = project
      ? `${project} 최신 산출물 상태와 다음 행동`
      : "프로젝트를 선택하면 최신 산출물과 다음 행동이 표시됩니다";

    if (!project) {
      artifactLadderHint.textContent = "프로젝트를 먼저 선택하세요.";
      if (
        renderArtifactLadderReact(artifact, {
          short: "BI",
          status: "대기",
          title: "프로젝트 선택 대기",
          detail: "프로젝트를 선택하면 현재 산출물 사다리와 최신 파일을 보여줍니다.",
        })
      ) {
        return;
      }
    }

    artifactSupportRow.innerHTML = "";
    const supportChips = artifact.support || [];
    if (!supportChips.length) {
      const chip = document.createElement("span");
      chip.className = "artifact-support-chip";
      chip.textContent = "지원 아티팩트 없음";
      artifactSupportRow.appendChild(chip);
    } else {
      for (const support of supportChips) {
        const chip = document.createElement("span");
        chip.className = `artifact-support-chip is-${support.status || "pending"}`;
        chip.textContent = `${support.label} · ${support.value}`;
        artifactSupportRow.appendChild(chip);
      }
    }

    artifactLadderGrid.innerHTML = "";
    const items = artifact.items || [];
    if (!project) {
      const emptyCard = document.createElement("div");
      emptyCard.className = "artifact-card is-pending";
      emptyCard.innerHTML = `
        <div class="artifact-card-top">
          <span class="artifact-short">BI</span>
          <span class="artifact-status-chip is-pending">대기</span>
        </div>
        <div class="artifact-card-title">프로젝트 선택 대기</div>
        <div class="artifact-card-detail">프로젝트를 선택하면 현재 산출물 사다리와 최신 파일을 보여줍니다.</div>
      `;
      artifactLadderGrid.appendChild(emptyCard);
      artifactLadderHint.textContent = "프로젝트를 먼저 선택하세요.";
      return;
    }

    if (!items.length) {
      if (
        renderArtifactLadderReact(
          { ...artifact, items: [] },
          {
            short: "BI",
            status: "대기",
            title: "산출물 사다리 대기",
            detail: "프로젝트 산출물 사다리를 아직 불러오지 못했습니다.",
          }
        )
      ) {
        artifactLadderHint.textContent = artifact.hint || "프로젝트 산출물 상태를 다시 불러오세요.";
        return;
      }
      appendInsightEmpty(artifactLadderGrid, "프로젝트 산출물 사다리를 아직 불러오지 못했습니다.");
      artifactLadderHint.textContent = artifact.hint || "프로젝트 산출물 상태를 다시 불러오세요.";
      return;
    }

    if (renderArtifactLadderReact(artifact)) {
      artifactLadderHint.textContent = artifact.hint || buildArtifactFallbackHint(items);
      return;
    }

    for (const item of items) {
      const card = document.createElement("div");
      const status = sanitizeToken(item.status, "pending");
      const shortLabel = escapeHtml(item.short || item.key || "-");
      const titleLabel = escapeHtml(item.title || item.label || item.key || "Artifact");
      const metaLabel = escapeHtml(item.meta || item.label || "");
      const detailLabel = escapeHtml(item.detail || "");
      const pathLabel = escapeHtml(item.path || "경로 정보 없음");
      card.className = `artifact-card is-${status}`;
      card.innerHTML = `
        <div class="artifact-card-top">
          <span class="artifact-short">${shortLabel}</span>
          <span class="artifact-status-chip is-${status}">${getArtifactStatusLabel(status)}</span>
        </div>
        <div class="artifact-card-title">${titleLabel}</div>
        <div class="artifact-card-meta">${metaLabel}</div>
        <div class="artifact-card-detail">${detailLabel}</div>
        <div class="artifact-card-path">${pathLabel}</div>
      `;
      artifactLadderGrid.appendChild(card);
    }

    artifactLadderHint.textContent = artifact.hint || buildArtifactFallbackHint(items);
  }

  function renderTrendCompareSection({
    trendPanelMeta,
    qualityTrendSummary,
    qualityCompareBody,
    scoreTrend,
    compareRows,
    renderQualityTrendSummaryReact,
    renderQualityCompareBodyReact,
    escapeHtml,
  }) {
    trendPanelMeta.textContent = scoreTrend.summary || "최근 회차 점수와 품질 신호를 비교합니다";
    qualityTrendSummary.innerHTML = "";

    const chips = [
      `Trend · ${scoreTrend.trend || "insufficient_data"}`,
      `평균 ${Number(scoreTrend.avg || 0).toFixed(1)}점`,
      `Δ ${Number(scoreTrend.delta || 0) > 0 ? "+" : ""}${Number(scoreTrend.delta || 0)}`,
      `샘플 ${scoreTrend.samples || 0}화`,
    ];
    if (!renderQualityTrendSummaryReact(chips)) {
      for (const label of chips) {
        const chip = document.createElement("span");
        chip.className = "trend-chip";
        chip.textContent = label;
        qualityTrendSummary.appendChild(chip);
      }
    }

    qualityCompareBody.innerHTML = "";
    if (!renderQualityCompareBodyReact(compareRows, "최근 회차 비교 데이터가 아직 없습니다.")) {
      qualityCompareBody.innerHTML = "";
    }
    if (!compareRows.length && !global.React) {
      const row = document.createElement("tr");
      row.innerHTML = '<td colspan="5">최근 회차 비교 데이터가 아직 없습니다.</td>';
      qualityCompareBody.appendChild(row);
      return;
    }

    if (compareRows.length && !global.React) {
      for (const rowData of compareRows.slice(0, 6)) {
        const row = document.createElement("tr");
        const verdict = String(rowData.verdict || "").toUpperCase();
        const verdictClass = verdict === "PASS" ? "is-pass" : verdict === "PASS_WITH_FIX" ? "is-pwf" : verdict === "REJECT" ? "is-reject" : "";
        const verdictLabel = escapeHtml(verdict || "-");
        row.innerHTML = `
          <td>${rowData.ep_num ?? "-"}</td>
          <td><span class="compare-verdict ${verdictClass}">${verdictLabel}</span></td>
          <td>${rowData.score ?? "-"}</td>
          <td>${rowData.ced != null ? Number(rowData.ced).toFixed(2) : "-"}</td>
          <td>${rowData.ai_slop != null ? Number(rowData.ai_slop).toFixed(2) : "-"}</td>
        `;
        qualityCompareBody.appendChild(row);
      }
    }
  }

  function renderFailureWatchSection({
    failureWatchMeta,
    stageStatsGrid,
    failurePatternList,
    failureRangeList,
    stageStats,
    failurePatterns,
    commonViolations,
    renderFailureStageStatsGridReact,
    renderFailurePatternListReact,
    renderFailureRangeListReact,
    appendInsightEmpty,
    escapeHtml,
  }) {
    failureWatchMeta.textContent = stageStats.length
      ? `Stage ${stageStats.map((row) => row.stage).join(", ")} 최근 통과율과 실패 패턴`
      : "실패 원인과 Stage별 통과 흐름을 요약합니다";

    stageStatsGrid.innerHTML = "";
    if (!renderFailureStageStatsGridReact(stageStats, "Stage별 pass rate / avg score가 누적되면 여기에 표시됩니다.")) {
      stageStatsGrid.innerHTML = "";
    }
    if (!stageStats.length && !global.React) {
      appendInsightEmpty(stageStatsGrid, "Stage별 pass rate / avg score가 누적되면 여기에 표시됩니다.");
    } else if (stageStats.length && !global.React) {
      for (const stat of stageStats.slice(0, 3)) {
        const card = document.createElement("div");
        card.className = "stage-stat-card";
        const stageLabel = escapeHtml(stat.stage);
        card.innerHTML = `
          <div class="stage-stat-label">Stage ${stageLabel}</div>
          <div class="stage-stat-value">${Number(stat.pass_rate || 0).toFixed(1)}%</div>
          <div class="stage-stat-meta">평균 ${Number(stat.avg_score || 0).toFixed(1)}점 · 총 ${stat.total || 0}회</div>
        `;
        stageStatsGrid.appendChild(card);
      }
    }

    failurePatternList.innerHTML = "";
    const topTypes = failurePatterns.top_types?.length ? failurePatterns.top_types : commonViolations;
    if (!renderFailurePatternListReact(topTypes || [], "주요 실패 패턴이 아직 충분히 쌓이지 않았습니다.")) {
      failurePatternList.innerHTML = "";
    }
    if ((!topTypes || !topTypes.length) && !global.React) {
      appendInsightEmpty(failurePatternList, "주요 실패 패턴이 아직 충분히 쌓이지 않았습니다.");
    } else if (topTypes?.length && !global.React) {
      for (const item of topTypes.slice(0, 5)) {
        const node = document.createElement("div");
        node.className = "pattern-item";
        const typeLabel = escapeHtml(item.type || "unknown");
        node.innerHTML = `
          <div class="pattern-item-title">${typeLabel}</div>
          <div class="pattern-item-meta">누적 ${item.count || 0}회</div>
        `;
        failurePatternList.appendChild(node);
      }
    }

    failureRangeList.innerHTML = "";
    const ranges = failurePatterns.by_episode_range || [];
    if (!renderFailureRangeListReact(ranges, "회차 구간별 실패 경향이 아직 없습니다.")) {
      failureRangeList.innerHTML = "";
    }
    if (!ranges.length && !global.React) {
      appendInsightEmpty(failureRangeList, "회차 구간별 실패 경향이 아직 없습니다.");
    } else if (ranges.length && !global.React) {
      for (const item of ranges.slice(0, 5)) {
        const node = document.createElement("div");
        node.className = "pattern-item";
        const rangeLabel = escapeHtml(item.range);
        node.innerHTML = `
          <div class="pattern-item-title">${rangeLabel}</div>
          <div class="pattern-item-meta">REJECT ${item.count || 0}회</div>
        `;
        failureRangeList.appendChild(node);
      }
    }
  }

  function renderCalibrationDeskSection({
    calibrationMeta,
    qualityObservationEp,
    calibrationSummary,
    qualityObservationList,
    qualityAdvisoryList,
    project,
    latestEp,
    calibration,
    renderCalibrationSummaryReact,
    renderQualityObservationListReact,
    renderQualityAdvisoryListReact,
    appendInsightEmpty,
    escapeHtml,
  }) {
    calibrationMeta.textContent = calibration.available
      ? `최근 ${calibration.lookback || 5}화 기준 수기 관측 ${calibration.total_reviews || 0}건`
      : "프로젝트를 선택하면 수기 관측과 승격 후보가 표시됩니다";

    const projectKey = project || "";
    if (qualityObservationEp.dataset.project !== projectKey) {
      qualityObservationEp.dataset.project = projectKey;
      qualityObservationEp.value = latestEp || "";
    } else if (!qualityObservationEp.value && latestEp) {
      qualityObservationEp.value = latestEp;
    }

    calibrationSummary.innerHTML = "";
    const summaryChips = calibration.label_counts?.length
      ? calibration.label_counts.map((item) => `${item.label} ${item.count}건`)
      : [`허용 라벨 ${((calibration.allowed_labels || []).length || 5)}종`, "아직 관측 데이터 없음"];
    if (!renderCalibrationSummaryReact(summaryChips)) {
      for (const label of summaryChips.slice(0, 5)) {
        const chip = document.createElement("span");
        chip.className = "trend-chip";
        chip.textContent = label;
        calibrationSummary.appendChild(chip);
      }
    }

    qualityObservationList.innerHTML = "";
    const recentObservations = calibration.recent_observations || [];
    if (
      !renderQualityObservationListReact(
        recentObservations,
        "좋음/경계/AI 티 같은 수기 관측이 쌓이면 여기서 최근 노트를 비교할 수 있습니다."
      )
    ) {
      qualityObservationList.innerHTML = "";
    }
    if (!recentObservations.length && !global.React) {
      appendInsightEmpty(qualityObservationList, "좋음/경계/AI 티 같은 수기 관측이 쌓이면 여기서 최근 노트를 비교할 수 있습니다.");
    } else if (recentObservations.length && !global.React) {
      for (const row of recentObservations.slice(0, 6)) {
        const card = document.createElement("div");
        card.className = "pattern-item";
        const verdict = row.verdict ? ` · ${row.verdict}${row.score ? ` ${row.score}점` : ""}` : "";
        const notes = (row.signal_notes || []).join(" · ");
        const noteLabel = escapeHtml(row.note || "메모 없음");
        const verdictLabel = escapeHtml(verdict);
        const notesLabel = escapeHtml(notes || "신호 메모 없음");
        const operatorLabel = escapeHtml(row.operator_label);
        card.innerHTML = `
          <div class="pattern-item-title">ep ${row.ep_num} <span class="observation-label-chip ${row.operator_label === "좋음" ? "is-good" : row.operator_label === "AI 티" || row.operator_label === "과잉 설명" ? "is-alert" : "is-watch"}">${operatorLabel}</span></div>
          <div class="pattern-item-meta">${noteLabel}${verdictLabel}</div>
          <div class="pattern-item-meta">${notesLabel}</div>
        `;
        qualityObservationList.appendChild(card);
      }
    }

    qualityAdvisoryList.innerHTML = "";
    const candidates = calibration.advisory_candidates || [];
    if (
      !renderQualityAdvisoryListReact(
        candidates,
        calibration.next_step || "승격 후보가 아직 없습니다."
      )
    ) {
      qualityAdvisoryList.innerHTML = "";
    }
    if (!candidates.length && !global.React) {
      appendInsightEmpty(qualityAdvisoryList, calibration.next_step || "승격 후보가 아직 없습니다.");
    } else if (candidates.length && !global.React) {
      for (const item of candidates.slice(0, 4)) {
        const card = document.createElement("div");
        card.className = "candidate-card";
        const signalLabel = escapeHtml(item.signal);
        const reasonLabel = escapeHtml(item.reason);
        card.innerHTML = `
          <strong>${signalLabel} advisory 후보</strong>
          <span>${reasonLabel}</span>
          <span>동행 관측 ${item.count || 0}건</span>
        `;
        qualityAdvisoryList.appendChild(card);
      }
    }
  }

  function mergeDashboardData(fallback, data) {
    return {
      ...fallback,
      ...(data || {}),
      safe_ops: {
        ...fallback.safe_ops,
        ...((data || {}).safe_ops || {}),
      },
      artifact_ladder: {
        ...fallback.artifact_ladder,
        ...((data || {}).artifact_ladder || {}),
      },
      retrieval_summary: {
        ...fallback.retrieval_summary,
        ...((data || {}).retrieval_summary || {}),
      },
      quality_summary: {
        ...fallback.quality_summary,
        ...((data || {}).quality_summary || {}),
      },
      result_summary: {
        ...fallback.result_summary,
        ...((data || {}).result_summary || {}),
      },
      failure_patterns: {
        ...fallback.failure_patterns,
        ...((data || {}).failure_patterns || {}),
      },
      calibration: {
        ...fallback.calibration,
        ...((data || {}).calibration || {}),
      },
    };
  }

  async function refreshSummary({
    desktop,
    project,
    officeState,
    createEmptyQualityDashboard,
    renderQualityRadar,
    renderQualityInsights,
  }) {
    if (!desktop || !project) {
      officeState.qualityInsights = createEmptyQualityDashboard(project || null);
      officeState.qualitySummary = officeState.qualityInsights.quality_summary;
      renderQualityRadar();
      renderQualityInsights();
      return;
    }

    try {
      if (desktop.getQualityDashboard) {
        const result = await desktop.getQualityDashboard(project, 5);
        if (result && result.ok) {
          const fallback = createEmptyQualityDashboard(project);
          officeState.qualityInsights = mergeDashboardData(fallback, result.data || {});
          officeState.qualitySummary = officeState.qualityInsights.quality_summary;
        } else {
          officeState.qualityInsights = createEmptyQualityDashboard(project);
          officeState.qualitySummary = officeState.qualityInsights.quality_summary;
        }
      } else {
        const result = await desktop.getQualitySummary(project, 5);
        const fallback = createEmptyQualityDashboard(project);
        if (result && result.ok) {
          officeState.qualitySummary = {
            ...fallback.quality_summary,
            ...result.data,
          };
          officeState.qualityInsights = {
            ...fallback,
            quality_summary: officeState.qualitySummary,
          };
        } else {
          officeState.qualityInsights = fallback;
          officeState.qualitySummary = fallback.quality_summary;
        }
      }
    } catch (err) {
      officeState.qualityInsights = createEmptyQualityDashboard(project);
      officeState.qualitySummary = officeState.qualityInsights.quality_summary;
    }

    renderQualityRadar();
    renderQualityInsights();
  }

  async function loadSafeOpsPreview({
    desktop,
    project,
    officeState,
    createEmptyQualityDashboard,
    renderQualityInsights,
    warn = () => {},
  }) {
    if (!project || !desktop?.getSafeOpsPreview) {
      return officeState.qualityInsights?.safe_ops || createEmptyQualityDashboard(project).safe_ops;
    }
    try {
      const result = await desktop.getSafeOpsPreview(project);
      if (result && result.ok && result.data) {
        officeState.qualityInsights = officeState.qualityInsights || createEmptyQualityDashboard(project);
        officeState.qualityInsights.safe_ops = {
          ...createEmptyQualityDashboard(project).safe_ops,
          ...result.data,
        };
        renderQualityInsights();
        return officeState.qualityInsights.safe_ops;
      }
    } catch (err) {
      warn("safe ops preview load failed:", err);
    }
    return officeState.qualityInsights?.safe_ops || createEmptyQualityDashboard(project).safe_ops;
  }

  global.GeuldobiQualityPageBootstrap = {
    renderInsights,
    renderQualityRadarSection,
    renderResultSummarySection,
    renderRetrievalInspectorSection,
    renderSafeOpsPreviewSection,
    renderArtifactLadderSection,
    renderTrendCompareSection,
    renderFailureWatchSection,
    renderCalibrationDeskSection,
    refreshSummary,
    loadSafeOpsPreview,
  };
})(window);

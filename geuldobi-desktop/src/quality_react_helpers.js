(function (global) {
  "use strict";

  function renderResultSignalAlerts({
    container,
    rootKey,
    alerts = [],
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = alerts.map((alertText, index) =>
      e(
        "span",
        { className: "signal-alert-chip", key: `alert-${index}` },
        alertText
      )
    );
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderResultSummaryCopy({
    headlineContainer,
    headlineRootKey,
    headline = "",
    reasonContainer,
    reasonRootKey,
    reason = "",
    renderTree,
  }) {
    if (!headlineContainer || !reasonContainer || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const headlineRendered = renderTree(
      headlineContainer,
      headlineRootKey,
      e(global.React.Fragment, null, headline)
    );
    const reasonRendered = renderTree(
      reasonContainer,
      reasonRootKey,
      e(global.React.Fragment, null, reason)
    );
    return headlineRendered && reasonRendered;
  }

  function renderResultIssueList({
    container,
    rootKey,
    issues = [],
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = issues.length
      ? issues.slice(0, 3).map((issue, index) =>
          e(
            "li",
            { className: "issue-item", key: `issue-${index}` },
            issue
          )
        )
      : [
          e(
            "div",
            { className: "insight-empty", key: "issue-empty" },
            emptyText
          ),
        ];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderResultActionGrid({
    container,
    rootKey,
    cards = [],
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = cards.map((card, index) =>
      e(
        "div",
        { className: "action-card", key: `result-action-card-${index}` },
        e("div", { className: "action-card-label" }, card.label),
        e("div", { className: "action-card-copy" }, card.copy)
      )
    );
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderResultNextAction({
    container,
    rootKey,
    text = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, text)
    );
  }

  function renderRetrievalSummaryStrip({
    container,
    rootKey,
    summaryChips = [],
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = summaryChips.map((label, index) =>
      e(
        "span",
        { className: "trend-chip", key: `retrieval-summary-${index}` },
        label
      )
    );
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderRetrievalStageGrid({
    container,
    rootKey,
    stageRows = [],
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = stageRows.length
      ? stageRows.slice(0, 4).map((row, index) => {
          const workRate = Math.round(Number(row.work_focus_rate || 0) * 100);
          const summaryRate = Math.round(Number(row.summary_included_rate || 0) * 100);
          const relationRate = Math.round(Number(row.relation_slice_rate || 0) * 100);
          const warningRate = Math.round(Number(row.coverage_warning_rate || 0) * 100);
          const stageLabel = String(row.stage || "unknown");
          return e(
            "div",
            { className: "retrieval-stage-card", key: `retrieval-stage-${stageLabel}-${index}` },
            e("div", { className: "retrieval-stage-label" }, stageLabel),
            e("div", { className: "retrieval-stage-value" }, `${summaryRate}%`),
            e("div", { className: "retrieval-stage-meta" }, "summary slot 포함률"),
            e(
              "div",
              { className: "retrieval-stage-meta" },
              `work focus ${workRate}% · relation slice ${relationRate}%`
            ),
            e(
              "div",
              { className: "retrieval-stage-meta" },
              `coverage warning ${warningRate}% · 표본 ${row.total || 0}건`
            )
          );
        })
      : [e("div", { className: "insight-empty", key: "retrieval-stage-empty" }, emptyText)];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderRetrievalWarningList({
    container,
    rootKey,
    warnings = [],
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = warnings.length
      ? warnings.slice(0, 6).map((row, index) =>
          e(
            "div",
            { className: "pattern-item", key: `retrieval-warning-${index}` },
            e("div", { className: "pattern-item-title" }, row.warning || "unknown_warning"),
            e("div", { className: "pattern-item-meta" }, `누적 ${row.count || 0}회`)
          )
        )
      : [e("div", { className: "insight-empty", key: "retrieval-warning-empty" }, emptyText)];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderRetrievalRecentList({
    container,
    rootKey,
    recentRows = [],
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = recentRows.length
      ? recentRows.slice(0, 6).map((row, index) => {
          const sources = Object.entries(row.source_counts || {})
            .map(([key, value]) => `${key} ${value}`)
            .join(" · ");
          const warningsText = (row.coverage_warnings || []).join(" · ");
          const stageLabel = String(row.stage || "unknown").toUpperCase();
          return e(
            "div",
            { className: "pattern-item", key: `retrieval-recent-${index}` },
            e("div", { className: "pattern-item-title" }, `ep ${row.ep_num ?? "-"} · ${stageLabel}`),
            e(
              "div",
              { className: "pattern-item-meta" },
              `summary ${row.work_slot_summary_included ? "yes" : "no"} · relation ${row.relation_slice_included ? "yes" : "no"}`
            ),
            e("div", { className: "pattern-item-meta" }, sources || "source count 없음"),
            e("div", { className: "pattern-item-meta" }, warningsText || "coverage warning 없음")
          );
        })
      : [e("div", { className: "insight-empty", key: "retrieval-recent-empty" }, emptyText)];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderQualityTrendSummary({
    container,
    rootKey,
    chips = [],
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = chips.map((label, index) =>
      e(
        "span",
        { className: "trend-chip", key: `trend-summary-${index}` },
        label
      )
    );
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderQualityCompareBody({
    container,
    rootKey,
    compareRows = [],
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = compareRows.length
      ? compareRows.slice(0, 6).map((rowData, index) => {
          const verdict = String(rowData.verdict || "").toUpperCase();
          const verdictClass =
            verdict === "PASS"
              ? "is-pass"
              : verdict === "PASS_WITH_FIX"
                ? "is-pwf"
                : verdict === "REJECT"
                  ? "is-reject"
                  : "";
          return e(
            "tr",
            { key: `quality-compare-${rowData.ep_num ?? "ep"}-${index}` },
            e("td", null, rowData.ep_num ?? "-"),
            e(
              "td",
              null,
              e("span", { className: `compare-verdict ${verdictClass}`.trim() }, verdict || "-")
            ),
            e("td", null, rowData.score ?? "-"),
            e("td", null, rowData.ced != null ? Number(rowData.ced).toFixed(2) : "-"),
            e("td", null, rowData.ai_slop != null ? Number(rowData.ai_slop).toFixed(2) : "-")
          );
        })
      : [e("tr", { key: "quality-compare-empty" }, e("td", { colSpan: 5 }, emptyText))];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderFailureStageStatsGrid({
    container,
    rootKey,
    stageStats = [],
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = stageStats.length
      ? stageStats.slice(0, 3).map((stat, index) =>
          e(
            "div",
            { className: "stage-stat-card", key: `stage-stat-${stat.stage || "stage"}-${index}` },
            e("div", { className: "stage-stat-label" }, `Stage ${stat.stage || "-"}`),
            e("div", { className: "stage-stat-value" }, `${Number(stat.pass_rate || 0).toFixed(1)}%`),
            e(
              "div",
              { className: "stage-stat-meta" },
              `평균 ${Number(stat.avg_score || 0).toFixed(1)}점 · 총 ${stat.total || 0}회`
            )
          )
        )
      : [e("div", { className: "insight-empty", key: "stage-stat-empty" }, emptyText)];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderFailurePatternList({
    container,
    rootKey,
    items = [],
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = items.length
      ? items.slice(0, 5).map((item, index) =>
          e(
            "div",
            { className: "pattern-item", key: `failure-pattern-${item.type || "type"}-${index}` },
            e("div", { className: "pattern-item-title" }, item.type || "unknown"),
            e("div", { className: "pattern-item-meta" }, item.meta || `누적 ${item.count || 0}회`)
          )
        )
      : [e("div", { className: "insight-empty", key: "failure-pattern-empty" }, emptyText)];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderFailureRangeList({
    container,
    rootKey,
    ranges = [],
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = ranges.length
      ? ranges.slice(0, 5).map((item, index) =>
          e(
            "div",
            { className: "pattern-item", key: `failure-range-${item.range || "range"}-${index}` },
            e("div", { className: "pattern-item-title" }, item.range || "-"),
            e("div", { className: "pattern-item-meta" }, `REJECT ${item.count || 0}회`)
          )
        )
      : [e("div", { className: "insight-empty", key: "failure-range-empty" }, emptyText)];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderSafeOpsGrid({
    container,
    rootKey,
    actionRows = [],
    emptyText = "",
    formatSafeOpsImpactCounts,
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = actionRows.length
      ? actionRows.map(({ key, action }, index) => {
          const targetLabel = action.requires_target ? "target 필요" : "즉시 preview";
          return e(
            "div",
            { className: "safe-ops-card", key: `safe-ops-${key}-${index}` },
            e(
              "div",
              { className: "safe-ops-card-head" },
              e("span", { className: "safe-ops-card-title" }, action.title || key),
              e(
                "span",
                { className: `safe-ops-chip ${action.requires_target ? "is-target" : ""}`.trim() },
                targetLabel
              )
            ),
            e("div", { className: "safe-ops-card-copy" }, action.summary || ""),
            e(
              "div",
              { className: "safe-ops-card-impact" },
              e("strong", null, "영향"),
              " · ",
              formatSafeOpsImpactCounts(action)
            ),
            e("div", { className: "safe-ops-card-note" }, (action.notes || [])[0] || "추가 메모 없음")
          );
        })
      : [e("div", { className: "insight-empty", key: "safe-ops-empty" }, emptyText)];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderCalibrationSummary({
    container,
    rootKey,
    summaryChips = [],
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = summaryChips.slice(0, 5).map((label, index) =>
      e(
        "span",
        { className: "trend-chip", key: `calibration-summary-${index}` },
        label
      )
    );
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderQualityObservationList({
    container,
    rootKey,
    recentObservations = [],
    emptyText = "",
    getObservationLabelClass,
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = recentObservations.length
      ? recentObservations.slice(0, 6).map((row, index) => {
          const verdict = row.verdict ? ` · ${row.verdict}${row.score ? ` ${row.score}점` : ""}` : "";
          const notes = (row.signal_notes || []).join(" · ");
          return e(
            "div",
            { className: "pattern-item", key: `quality-observation-${row.ep_num || "ep"}-${index}` },
            e(
              "div",
              { className: "pattern-item-title" },
              `ep ${row.ep_num}`,
              " ",
              e(
                "span",
                { className: `observation-label-chip ${getObservationLabelClass(row.operator_label)}`.trim() },
                row.operator_label
              )
            ),
            e("div", { className: "pattern-item-meta" }, `${row.note || "메모 없음"}${verdict}`),
            e("div", { className: "pattern-item-meta" }, notes || "신호 메모 없음")
          );
        })
      : [e("div", { className: "insight-empty", key: "quality-observation-empty" }, emptyText)];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderQualityAdvisoryList({
    container,
    rootKey,
    candidates = [],
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = candidates.length
      ? candidates.slice(0, 4).map((item, index) =>
          e(
            "div",
            { className: "candidate-card", key: `quality-advisory-${item.signal || "signal"}-${index}` },
            e("strong", null, `${item.signal} advisory 후보`),
            e("span", null, item.reason || ""),
            e("span", null, `동행 관측 ${item.count || 0}건`)
          )
        )
      : [e("div", { className: "insight-empty", key: "quality-advisory-empty" }, emptyText)];
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...nodes)
    );
  }

  function renderArtifactLadder({
    supportContainer,
    supportRootKey,
    gridContainer,
    gridRootKey,
    artifact,
    emptyState = null,
    sanitizeToken,
    getArtifactStatusLabel,
    renderTree,
  }) {
    if (!supportContainer || !gridContainer || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const supportChips = (artifact.support || []).length
      ? artifact.support.map((support, index) =>
          e(
            "span",
            {
              className: `artifact-support-chip is-${support.status || "pending"}`,
              key: `${support.label || "support"}-${index}`,
            },
            `${support.label} · ${support.value}`
          )
        )
      : [
          e(
            "span",
            { className: "artifact-support-chip", key: "support-empty" },
            "지원 아티팩트 없음"
          ),
        ];

    let gridCards = [];
    if (emptyState) {
      gridCards = [
        e(
          "div",
          { className: "artifact-card is-pending", key: "artifact-empty" },
          e(
            "div",
            { className: "artifact-card-top" },
            e("span", { className: "artifact-short" }, emptyState.short || "BI"),
            e("span", { className: "artifact-status-chip is-pending" }, emptyState.status || "대기")
          ),
          e("div", { className: "artifact-card-title" }, emptyState.title),
          e("div", { className: "artifact-card-detail" }, emptyState.detail)
        ),
      ];
    } else {
      gridCards = (artifact.items || []).map((item, index) => {
        const status = sanitizeToken(item.status, "pending");
        return e(
          "div",
          { className: `artifact-card is-${status}`, key: `${item.key || "artifact"}-${index}` },
          e(
            "div",
            { className: "artifact-card-top" },
            e("span", { className: "artifact-short" }, item.short || item.key || "-"),
            e(
              "span",
              { className: `artifact-status-chip is-${status}` },
              getArtifactStatusLabel(status)
            )
          ),
          e("div", { className: "artifact-card-title" }, item.title || item.label || item.key || "Artifact"),
          e("div", { className: "artifact-card-meta" }, item.meta || item.label || ""),
          e("div", { className: "artifact-card-detail" }, item.detail || ""),
          e("div", { className: "artifact-card-path" }, item.path || "경로 정보 없음")
        );
      });
    }

    const supportRendered = renderTree(
      supportContainer,
      supportRootKey,
      e(global.React.Fragment, null, ...supportChips)
    );
    const gridRendered = renderTree(
      gridContainer,
      gridRootKey,
      e(global.React.Fragment, null, ...gridCards)
    );
    return supportRendered && gridRendered;
  }

  function renderQualityRadarFoot({
    container,
    rootKey,
    sentenceCount = 0,
    hits = [],
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const summaryLine = sentenceCount
      ? `최근 문장 수 ${sentenceCount} · 상투어 hit 상위 패턴`
      : "최근 문장/상투어 데이터가 아직 충분하지 않습니다.";
    const chips = hits.length
      ? hits.map((item, index) =>
          e(
            "span",
            { className: "mini-chip", key: `quality-radar-foot-${item.pattern || "pattern"}-${index}` },
            `${item.pattern} × ${item.count}`
          )
        )
      : [e("span", { className: "mini-chip", key: "quality-radar-foot-empty" }, "최근 상투어 hit 없음")];
    return renderTree(
      container,
      rootKey,
      e(
        global.React.Fragment,
        null,
        e("div", null, summaryLine),
        e("div", { className: "quality-radar-chips" }, ...chips)
      )
    );
  }

  function renderQualityRadarCards({
    container,
    rootKey,
    summary,
    emptyState = null,
    QUALITY_SIGNAL_META,
    sanitizeToken,
    buildSparklineSvg,
    describeSignal,
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    let cards = [];
    if (emptyState) {
      cards = [
        e(
          "div",
          { className: "quality-signal-card is-empty", key: "empty" },
          e("div", { className: "quality-signal-label" }, emptyState.label),
          e("div", { className: "quality-signal-meta" }, emptyState.meta)
        ),
      ];
    } else {
      cards = Object.entries(QUALITY_SIGNAL_META).map(([key, meta]) => {
        const stat = summary.signals?.[key] || {};
        const signalStatus = sanitizeToken(stat.status, "watch");
        const deltaValue = Number(stat.delta || 0);
        const trendMap = { up: "상승", down: "하강", flat: "유지" };
        const deltaSign = deltaValue > 0 ? "+" : "";
        const recentValues = (summary.recent || []).map((row) => row?.[meta.field]);
        const sparkMarkup = buildSparklineSvg(recentValues, stat.status || "watch");
        return e(
          "div",
          { className: `quality-signal-card is-${signalStatus}`, key },
          e("div", { className: "quality-signal-label" }, meta.label),
          e("div", { className: "quality-signal-value" }, meta.format(stat.value || 0)),
          e("div", { className: "quality-signal-meta" }, meta.hint),
          e("div", {
            className: "quality-signal-spark",
            dangerouslySetInnerHTML: { __html: sparkMarkup || "" },
          }),
          e("div", { className: "quality-signal-meta" }, `median ${meta.format(stat.median || 0)}`),
          e(
            "div",
            { className: "quality-signal-meta" },
            `${trendMap[stat.trend] || "유지"} · Δ ${deltaSign}${meta.format(deltaValue)}`
          ),
          e("div", { className: "quality-signal-reason" }, describeSignal(key, stat))
        );
      });
    }
    return renderTree(
      container,
      rootKey,
      e(global.React.Fragment, null, ...cards)
    );
  }

  global.GeuldobiQualityReactHelpers = {
    renderResultSignalAlerts,
    renderResultSummaryCopy,
    renderResultIssueList,
    renderResultActionGrid,
    renderResultNextAction,
    renderRetrievalSummaryStrip,
    renderRetrievalStageGrid,
    renderRetrievalWarningList,
    renderRetrievalRecentList,
    renderQualityTrendSummary,
    renderQualityCompareBody,
    renderFailureStageStatsGrid,
    renderFailurePatternList,
    renderFailureRangeList,
    renderSafeOpsGrid,
    renderCalibrationSummary,
    renderQualityObservationList,
    renderQualityAdvisoryList,
    renderArtifactLadder,
    renderQualityRadarFoot,
    renderQualityRadarCards,
  };
})(window);

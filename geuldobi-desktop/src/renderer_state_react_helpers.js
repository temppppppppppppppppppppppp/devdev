(function (global) {
  "use strict";

  function renderAgentBoard({
    container,
    rootKey,
    agents = [],
    runtimeByKey = {},
    activeKeys = [],
    officeIsRunning = false,
    hexToRgba,
    shortenText,
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const activeSet = new Set(activeKeys);
    const nodes = agents.map((agent) => {
      const runtime = runtimeByKey[agent.spriteKey] || {};
      const isActive = activeSet.has(agent.spriteKey);
      const isSpeaking = Number(runtime.bubbleTimer || 0) > 0;
      const bubbleText = isSpeaking
        ? runtime.bubbleText
        : officeIsRunning && isActive
          ? runtime.detail || runtime.status
          : "";
      const cardStyle = {
        borderColor: isActive
          ? hexToRgba(agent.screenColor, isSpeaking ? 0.6 : 0.34)
          : hexToRgba("#94a3b8", 0.2),
      };
      if (isSpeaking) {
        cardStyle.boxShadow = `0 14px 28px rgba(15, 23, 42, 0.1), 0 0 0 1px ${hexToRgba(agent.screenColor, 0.18)}`;
      } else if (isActive) {
        cardStyle.boxShadow = `0 10px 24px rgba(15, 23, 42, 0.05), 0 0 0 1px ${hexToRgba(agent.screenColor, 0.12)}`;
      }
      const stateStyle = {
        background: isActive
          ? `linear-gradient(180deg, ${hexToRgba(agent.screenColor, 0.18)}, ${hexToRgba(agent.screenColor, 0.08)})`
          : "#eef2ff",
        color: isActive ? "#1e293b" : "#475569",
      };
      const bubbleStyle = {
        borderColor: hexToRgba(agent.screenColor, bubbleText ? 0.24 : 0.12),
        background: bubbleText
          ? `linear-gradient(180deg, ${hexToRgba(agent.screenColor, 0.12)}, rgba(248, 250, 252, 0.98))`
          : "linear-gradient(180deg, #f8fafc, #f1f5f9)",
      };
      return e(
        "div",
        {
          className: `agent-card${isActive ? " active" : ""}${isSpeaking ? " speaking" : ""}`,
          key: agent.spriteKey,
          style: cardStyle,
        },
        e(
          "div",
          { className: "agent-head" },
          e(
            "div",
            { className: "agent-name-row" },
            e("span", { className: "agent-dot", style: { background: agent.screenColor } }),
            e("span", { className: "agent-name" }, agent.name)
          ),
          e("span", { className: "agent-state", style: stateStyle }, runtime.status || "")
        ),
        e("div", { className: "agent-role" }, agent.role),
        e("div", { className: "agent-detail" }, runtime.detail || ""),
        e(
          "div",
          {
            className: `agent-bubble-echo${bubbleText ? " live" : ""}`,
            style: bubbleStyle,
          },
          bubbleText ? `“${shortenText(bubbleText, 38)}”` : "최근 발화 없음"
        )
      );
    });
    return renderTree(container, rootKey, e(global.React.Fragment, null, ...nodes));
  }

  function renderEventFeed({
    container,
    rootKey,
    recentEvents = [],
    getAgentMeta,
    getAgentDisplayName,
    hexToRgba,
    emptyText = "",
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const nodes = recentEvents.length
      ? recentEvents.slice(0, 5).map((entry, index) => {
          const agentMeta = entry.agent ? getAgentMeta(entry.agent) : null;
          const rowStyle = agentMeta
            ? {
                borderColor: hexToRgba(agentMeta.screenColor, 0.25),
                background: `linear-gradient(180deg, ${hexToRgba(agentMeta.screenColor, 0.08)}, rgba(248, 250, 252, 0.94))`,
                boxShadow: `inset 3px 0 0 ${hexToRgba(agentMeta.screenColor, 0.6)}`,
              }
            : null;
          return e(
            "div",
            { className: "live-event", key: `event-${index}-${entry.time || "time"}`, style: rowStyle || undefined },
            e("div", { className: "live-event-time" }, entry.time),
            e(
              "div",
              { className: "live-event-body" },
              e(
                "div",
                { className: "live-event-title" },
                entry.agent ? `[${getAgentDisplayName(entry.agent)}] ${entry.title}` : entry.title
              ),
              e("div", { className: "live-event-meta" }, entry.detail || " ")
            )
          );
        })
      : [e("div", { className: "live-feed-empty", key: "live-feed-empty" }, emptyText)];
    return renderTree(container, rootKey, e(global.React.Fragment, null, ...nodes));
  }

  function renderPipelineStrip({
    container,
    rootKey,
    pipelineOrder = [],
    currentStage = null,
    isRunning = false,
    resolveActionMeta,
    renderTree,
  }) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    const e = global.React.createElement;
    const currentIndex = pipelineOrder.indexOf(currentStage);
    const stageAccent = {
      stage_0: "rgba(14, 165, 233, 0.14)",
      stage_2: "rgba(16, 185, 129, 0.14)",
      stage_3: "rgba(59, 130, 246, 0.14)",
      stage_4: "rgba(251, 191, 36, 0.16)",
      one_stop: "rgba(168, 85, 247, 0.14)",
      one_stop_frontier_lag: "rgba(244, 114, 182, 0.16)",
    };
    const nodes = pipelineOrder.map((key, idx) => {
      const classes = ["pipeline-chip"];
      if (currentIndex >= 0 && idx < currentIndex) {
        classes.push("is-past");
      }
      if (currentStage === key) {
        classes.push("is-active");
        if (isRunning) {
          classes.push("is-running");
        }
      }
      return e(
        "div",
        {
          className: classes.join(" "),
          key,
          style: {
            background: stageAccent[key] || "linear-gradient(180deg, #ffffff, #f8fafc)",
          },
        },
        resolveActionMeta(key).title.replace("Stage ", "S")
      );
    });
    return renderTree(container, rootKey, e(global.React.Fragment, null, ...nodes));
  }

  global.GeuldobiRendererStateReactHelpers = {
    renderAgentBoard,
    renderEventFeed,
    renderPipelineStrip,
  };
})(window);

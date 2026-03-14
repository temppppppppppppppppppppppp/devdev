const CONSOLE_SEVERITY = Object.freeze({
  0: "verbose",
  1: "info",
  2: "warn",
  3: "error",
});

function normalizeConsoleSeverity(level) {
  const numericLevel = Number(level);
  return CONSOLE_SEVERITY[numericLevel] || "unknown";
}

function shouldRelayConsoleMessage(level) {
  const severity = normalizeConsoleSeverity(level);
  return severity === "warn" || severity === "error";
}

function buildConsoleRelayEntry({ windowName, level, message, line, sourceId }) {
  return {
    source: String(windowName || "unknown"),
    severity: normalizeConsoleSeverity(level),
    message: String(message || ""),
    line: Number.isFinite(Number(line)) ? Number(line) : 0,
    sourceId: String(sourceId || ""),
  };
}

function attachConsoleRelay(webContents, { windowName, logFn }) {
  if (!webContents || typeof webContents.on !== "function") {
    return;
  }
  const sink = typeof logFn === "function" ? logFn : () => {};

  webContents.on("console-message", (_event, level, message, line, sourceId) => {
    if (!shouldRelayConsoleMessage(level)) {
      return;
    }
    sink(
      "renderer console",
      buildConsoleRelayEntry({
        windowName,
        level,
        message,
        line,
        sourceId,
      })
    );
  });
}

module.exports = {
  attachConsoleRelay,
  buildConsoleRelayEntry,
  normalizeConsoleSeverity,
  shouldRelayConsoleMessage,
};

const assert = require("assert");

const {
  attachConsoleRelay,
  buildConsoleRelayEntry,
  normalizeConsoleSeverity,
  shouldRelayConsoleMessage,
} = require("../geuldobi-desktop/src/console_relay");

function createFakeWebContents() {
  return {
    handlers: {},
    on(eventName, handler) {
      this.handlers[eventName] = handler;
    },
  };
}

function testSeverityHelpers() {
  assert.strictEqual(normalizeConsoleSeverity(2), "warn");
  assert.strictEqual(normalizeConsoleSeverity(3), "error");
  assert.strictEqual(normalizeConsoleSeverity(1), "info");
  assert.strictEqual(shouldRelayConsoleMessage(2), true);
  assert.strictEqual(shouldRelayConsoleMessage(3), true);
  assert.strictEqual(shouldRelayConsoleMessage(1), false);
}

function testConsoleRelayHookAndPayload() {
  const webContents = createFakeWebContents();
  const sinkCalls = [];
  attachConsoleRelay(webContents, {
    windowName: "mainWindow",
    logFn: (...parts) => sinkCalls.push(parts),
  });

  assert.strictEqual(typeof webContents.handlers["console-message"], "function");

  webContents.handlers["console-message"]({}, 1, "harmless info", 12, "index.html");
  assert.strictEqual(sinkCalls.length, 0);

  webContents.handlers["console-message"]({}, 3, "WS parse error: bad json", 5994, "index.html");
  assert.strictEqual(sinkCalls.length, 1);
  assert.strictEqual(sinkCalls[0][0], "renderer console");
  assert.deepStrictEqual(
    sinkCalls[0][1],
    buildConsoleRelayEntry({
      windowName: "mainWindow",
      level: 3,
      message: "WS parse error: bad json",
      line: 5994,
      sourceId: "index.html",
    })
  );
}

function testSplashWarnRelay() {
  const webContents = createFakeWebContents();
  const sinkCalls = [];
  attachConsoleRelay(webContents, {
    windowName: "splashWindow",
    logFn: (...parts) => sinkCalls.push(parts),
  });

  webContents.handlers["console-message"]({}, 2, "[splash] getSplashConfig failed: boom", 79, "splash.js");

  assert.strictEqual(sinkCalls.length, 1);
  assert.strictEqual(sinkCalls[0][1].source, "splashWindow");
  assert.strictEqual(sinkCalls[0][1].severity, "warn");
  assert.strictEqual(sinkCalls[0][1].sourceId, "splash.js");
}

testSeverityHelpers();
testConsoleRelayHookAndPayload();
testSplashWarnRelay();

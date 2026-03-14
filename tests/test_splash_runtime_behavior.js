const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const SPLASH_JS = fs.readFileSync(
  path.resolve(__dirname, "../geuldobi-desktop/src/splash/splash.js"),
  "utf8"
);

function createSplashHarness({ firstRun = false, configError = null, fetchResults = [] } = {}) {
  const statusMessage = { textContent: "" };
  const windowHandlers = {};
  const intervals = [];
  let notifyCalls = 0;
  let fetchCount = 0;

  const sandbox = {
    document: {
      getElementById(id) {
        assert.strictEqual(id, "statusMessage");
        return statusMessage;
      },
    },
    window: {
      lucide: null,
      geuldobiDesktop: {
        async getSplashConfig() {
          if (configError) {
            throw configError;
          }
          return {
            firstRun,
            statusBaseUrl: "http://127.0.0.1:8300",
          };
        },
        notifyBackendReady() {
          notifyCalls += 1;
        },
      },
      addEventListener(name, handler) {
        windowHandlers[name] = handler;
      },
    },
    fetch: async () => {
      const result = fetchResults[Math.min(fetchCount, fetchResults.length - 1)];
      fetchCount += 1;
      if (result instanceof Error) {
        throw result;
      }
      if (!result || result.ok === false) {
        return { ok: false, status: result?.status ?? 500 };
      }
      return {
        ok: true,
        status: result.status ?? 200,
        async json() {
          return result.body;
        },
      };
    },
    AbortSignal: {
      timeout(ms) {
        return { timeoutMs: ms };
      },
    },
    setInterval(handler, intervalMs) {
      intervals.push({ handler, intervalMs, cleared: false });
      return intervals.length - 1;
    },
    clearInterval(id) {
      if (intervals[id]) {
        intervals[id].cleared = true;
      }
    },
    console: {
      error() {},
      log() {},
      warn() {},
    },
  };

  vm.runInNewContext(SPLASH_JS, sandbox, { filename: "splash.js" });

  return {
    statusMessage,
    windowHandlers,
    intervals,
    get notifyCalls() {
      return notifyCalls;
    },
    get fetchCount() {
      return fetchCount;
    },
  };
}

async function testFirstRunPollingHandsOffWhenBackendTurnsIdle() {
  const harness = createSplashHarness({
    firstRun: true,
    fetchResults: [{ ok: true, body: { data: { state: "idle" } } }],
  });

  await harness.windowHandlers.DOMContentLoaded();
  assert.strictEqual(harness.statusMessage.textContent, "첫 실행은 잠시 시간이 걸립니다");
  assert.strictEqual(harness.intervals.length, 1);
  assert.strictEqual(harness.intervals[0].intervalMs, 1000);

  await harness.intervals[0].handler();

  assert.strictEqual(harness.fetchCount, 1);
  assert.strictEqual(harness.notifyCalls, 1);
  assert.strictEqual(harness.intervals[0].cleared, true);
}

async function testRepeatedPollFailuresSurfaceRestartMessage() {
  const harness = createSplashHarness({
    fetchResults: Array.from({ length: 30 }, () => new Error("offline")),
  });

  await harness.windowHandlers.DOMContentLoaded();
  assert.strictEqual(harness.statusMessage.textContent, "시작하는 중...");

  for (let i = 0; i < 30; i += 1) {
    await harness.intervals[0].handler();
  }

  assert.strictEqual(harness.notifyCalls, 0);
  assert.strictEqual(
    harness.statusMessage.textContent,
    "백엔드 연결 실패 — 앱을 재시작하세요"
  );
  assert.strictEqual(harness.intervals[0].cleared, true);
}

async function testConfigFailureSurfacesInitializationMessage() {
  const harness = createSplashHarness({
    configError: new Error("boom"),
  });

  await harness.windowHandlers.DOMContentLoaded();

  assert.strictEqual(harness.statusMessage.textContent, "초기화 오류 — 앱을 재시작하세요");
  assert.strictEqual(harness.intervals.length, 0);
}

Promise.resolve()
  .then(testFirstRunPollingHandsOffWhenBackendTurnsIdle)
  .then(testRepeatedPollFailuresSurfaceRestartMessage)
  .then(testConfigFailureSurfacesInitializationMessage)
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });

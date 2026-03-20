const assert = require("assert");
const Module = require("module");
const path = require("path");
const fs = require("fs");
const vm = require("vm");
const {
  WINDOW_BRIDGE_NAME,
  PRELOAD_METHOD_CHANNELS: CONTRACT_PRELOAD_METHOD_CHANNELS,
  LIVE_PRELOAD_METHOD_NAMES,
} = require("../geuldobi-desktop/src/desktop_control_plane_contract.js");
const {
  getDesktopBridge,
  listMissingDesktopBridgeMethods,
  isDesktopBridgeReady,
  requireDesktopBridge,
  createDesktopBridgeFacade,
} = require("../geuldobi-desktop/src/desktop_bridge_client.js");

function loadPreloadApi() {
  const invokeCalls = [];
  const sendCalls = [];
  const onCalls = [];
  const exposed = {};

  const fakeElectron = {
    contextBridge: {
      exposeInMainWorld(name, api) {
        exposed[name] = api;
      },
    },
    ipcRenderer: {
      invoke(channel, ...args) {
        invokeCalls.push([channel, ...args]);
        return Promise.resolve({ ok: true, channel, args });
      },
      send(channel, ...args) {
        sendCalls.push([channel, ...args]);
      },
      on(channel, handler) {
        onCalls.push([channel, handler]);
        return handler;
      },
    },
  };

  const preloadPath = path.resolve(__dirname, "../geuldobi-desktop/src/preload.js");
  delete require.cache[preloadPath];

  const originalLoad = Module._load;
  Module._load = function patchedLoad(request, parent, isMain) {
    if (request === "electron") {
      return fakeElectron;
    }
    return originalLoad.call(this, request, parent, isMain);
  };

  try {
    require(preloadPath);
  } finally {
    Module._load = originalLoad;
  }

  return {
    api: exposed.geuldobiDesktop,
    invokeCalls,
    sendCalls,
    onCalls,
  };
}

async function testSplashBridgeMethods() {
  const { api, invokeCalls, sendCalls, onCalls } = loadPreloadApi();
  assert.ok(api);

  await api.getSplashConfig();
  api.notifyBackendReady();
  api.onAppReady(() => {});

  assert.deepStrictEqual(invokeCalls[0], ["splash:get-config"]);
  assert.deepStrictEqual(sendCalls[0], ["splash:backend-ready"]);
  assert.strictEqual(onCalls[0][0], "app:ready");
}

async function testMaterialAndWorkspaceBridgeMethods() {
  const { api, invokeCalls } = loadPreloadApi();
  assert.ok(api);

  await api.listMaterialFiles("bible");
  await api.openWorkspaceFolder();

  assert.deepStrictEqual(invokeCalls[0], ["material:list-files", "bible"]);
  assert.deepStrictEqual(invokeCalls[1], ["workspace:open-folder"]);
  assert.strictEqual("getWorkspacePath" in api, false);
}

async function testPreloadDoesNotDependOnLocalRelativeRequireForContract() {
  const preloadSource = fs.readFileSync(
    path.resolve(__dirname, "../geuldobi-desktop/src/preload.js"),
    "utf8"
  );
  assert.ok(preloadSource.includes('const PRELOAD_METHOD_CHANNELS = Object.freeze({'));
  assert.ok(!preloadSource.includes('require("./desktop_control_plane_contract")'));
}

async function testPreloadMethodChannelMapStaysInLockstepWithControlPlaneContract() {
  const preloadPath = path.resolve(__dirname, "../geuldobi-desktop/src/preload.js");
  const preloadSource = fs.readFileSync(preloadPath, "utf8");
  const start = preloadSource.indexOf("const PRELOAD_METHOD_CHANNELS = Object.freeze({");
  const end = preloadSource.indexOf("contextBridge.exposeInMainWorld(", start);

  assert.ok(start >= 0, "PRELOAD_METHOD_CHANNELS block not found");
  assert.ok(end >= 0, "preload API export block not found");

  const block = preloadSource.slice(start, end).trim();
  const context = {};
  vm.runInNewContext(block + "\nthis.__channels = PRELOAD_METHOD_CHANNELS;", context, {
    filename: "preload.js",
  });

  assert.deepStrictEqual(
    JSON.parse(JSON.stringify(context.__channels)),
    JSON.parse(JSON.stringify(CONTRACT_PRELOAD_METHOD_CHANNELS))
  );
}

async function testDesktopBridgeClientTracksLiveContractShape() {
  assert.strictEqual(WINDOW_BRIDGE_NAME, "geuldobiDesktop");
  assert.deepStrictEqual([...LIVE_PRELOAD_METHOD_NAMES], Object.keys(CONTRACT_PRELOAD_METHOD_CHANNELS.live));

  const calls = [];
  const fakeBridge = Object.fromEntries(
    LIVE_PRELOAD_METHOD_NAMES.map((methodName) => [
      methodName,
      (...args) => {
        calls.push([methodName, ...args]);
        return { ok: true, methodName, args };
      },
    ])
  );
  const fakeGlobal = { [WINDOW_BRIDGE_NAME]: fakeBridge };

  assert.strictEqual(getDesktopBridge(fakeGlobal), fakeBridge);
  assert.deepStrictEqual(listMissingDesktopBridgeMethods(fakeGlobal), []);
  assert.strictEqual(isDesktopBridgeReady(fakeGlobal), true);

  const facade = createDesktopBridgeFacade(fakeGlobal);
  assert.ok(Object.isFrozen(facade));
  const result = facade.getStatus("ignored");

  assert.deepStrictEqual(calls[0], ["getStatus", "ignored"]);
  assert.deepStrictEqual(result, { ok: true, methodName: "getStatus", args: ["ignored"] });
}

async function testDesktopBridgeClientReportsMissingBridgeMethods() {
  const fakeGlobal = {
    [WINDOW_BRIDGE_NAME]: {
      getStatus: () => ({ ok: true }),
    },
  };

  const missing = listMissingDesktopBridgeMethods(fakeGlobal);
  assert.ok(missing.includes("runKey"));
  assert.ok(missing.includes("openWorkspaceFolder"));
  assert.strictEqual(isDesktopBridgeReady(fakeGlobal), false);
  assert.throws(
    () => requireDesktopBridge(fakeGlobal),
    /missing methods/
  );
  assert.throws(
    () => requireDesktopBridge({}),
    /not available/
  );
}

Promise.resolve()
  .then(testSplashBridgeMethods)
  .then(testMaterialAndWorkspaceBridgeMethods)
  .then(testPreloadDoesNotDependOnLocalRelativeRequireForContract)
  .then(testPreloadMethodChannelMapStaysInLockstepWithControlPlaneContract)
  .then(testDesktopBridgeClientTracksLiveContractShape)
  .then(testDesktopBridgeClientReportsMissingBridgeMethods)
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });

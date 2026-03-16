const assert = require("assert");
const Module = require("module");
const path = require("path");

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
  await api.getWorkspacePath();

  assert.deepStrictEqual(invokeCalls[0], ["material:list-files", "bible"]);
  assert.deepStrictEqual(invokeCalls[1], ["workspace:open-folder"]);
  assert.deepStrictEqual(invokeCalls[2], ["workspace:get-path"]);
}

async function testPreloadDoesNotDependOnLocalRelativeRequireForContract() {
  const preloadSource = require("fs").readFileSync(
    path.resolve(__dirname, "../geuldobi-desktop/src/preload.js"),
    "utf8"
  );
  assert.ok(preloadSource.includes('const PRELOAD_METHOD_CHANNELS = Object.freeze({'));
  assert.ok(!preloadSource.includes('require("./desktop_control_plane_contract")'));
}

Promise.resolve()
  .then(testSplashBridgeMethods)
  .then(testMaterialAndWorkspaceBridgeMethods)
  .then(testPreloadDoesNotDependOnLocalRelativeRequireForContract)
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });

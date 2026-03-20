"use strict";

const {
  WINDOW_BRIDGE_NAME,
  LIVE_PRELOAD_METHOD_NAMES,
} = require("./desktop_control_plane_contract");

function getDesktopBridge(globalObject = globalThis) {
  if (!globalObject || (typeof globalObject !== "object" && typeof globalObject !== "function")) {
    return null;
  }
  const bridge = globalObject[WINDOW_BRIDGE_NAME];
  if (!bridge || typeof bridge !== "object") {
    return null;
  }
  return bridge;
}

function listMissingDesktopBridgeMethods(globalObject = globalThis) {
  const bridge = getDesktopBridge(globalObject);
  if (!bridge) {
    return [...LIVE_PRELOAD_METHOD_NAMES];
  }
  return LIVE_PRELOAD_METHOD_NAMES.filter((methodName) => typeof bridge[methodName] !== "function");
}

function isDesktopBridgeReady(globalObject = globalThis) {
  return listMissingDesktopBridgeMethods(globalObject).length === 0;
}

function requireDesktopBridge(globalObject = globalThis) {
  const bridge = getDesktopBridge(globalObject);
  if (!bridge) {
    throw new Error(`Desktop bridge '${WINDOW_BRIDGE_NAME}' is not available.`);
  }
  const missingMethods = listMissingDesktopBridgeMethods(globalObject);
  if (missingMethods.length > 0) {
    throw new Error(
      `Desktop bridge '${WINDOW_BRIDGE_NAME}' is missing methods: ${missingMethods.join(", ")}`
    );
  }
  return bridge;
}

function createDesktopBridgeFacade(globalObject = globalThis) {
  const bridge = requireDesktopBridge(globalObject);
  const facade = {};
  for (const methodName of LIVE_PRELOAD_METHOD_NAMES) {
    facade[methodName] = (...args) => bridge[methodName](...args);
  }
  return Object.freeze(facade);
}

module.exports = {
  WINDOW_BRIDGE_NAME,
  LIVE_PRELOAD_METHOD_NAMES,
  getDesktopBridge,
  listMissingDesktopBridgeMethods,
  isDesktopBridgeReady,
  requireDesktopBridge,
  createDesktopBridgeFacade,
};

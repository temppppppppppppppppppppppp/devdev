"use strict";

/*
 * Manual debug shadow entry only.
 * Authoritative Electron entry lives at geuldobi-desktop/src/main.js.
 * Do not use this file for packaged/runtime contract changes.
 * Do not add runtime logic, IPC handlers, or packaged env wiring here.
 */

if (!process.env.GEULDOBI_ROOT_SHADOW_ENTRY) {
  process.env.GEULDOBI_ROOT_SHADOW_ENTRY = "1";
}

module.exports = require("./geuldobi-desktop/src/main.js");

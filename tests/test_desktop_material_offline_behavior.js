const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const INDEX_HTML = fs.readFileSync(
  path.resolve(__dirname, "../geuldobi-desktop/src/index.html"),
  "utf8"
);

function extractFunctionSource(signature) {
  const start = INDEX_HTML.indexOf(signature);
  assert.notStrictEqual(start, -1, `Missing function signature: ${signature}`);
  const braceStart = INDEX_HTML.indexOf("{", start);
  assert.notStrictEqual(braceStart, -1, `Missing function body: ${signature}`);

  let depth = 0;
  for (let i = braceStart; i < INDEX_HTML.length; i += 1) {
    const ch = INDEX_HTML[i];
    if (ch === "{") depth += 1;
    if (ch === "}") {
      depth -= 1;
      if (depth === 0) {
        return INDEX_HTML.slice(start, i + 1);
      }
    }
  }
  throw new Error(`Unterminated function body: ${signature}`);
}

function createContainer() {
  return {
    innerHTML: "",
    children: [],
    appendChild(child) {
      this.children.push(child);
    },
  };
}

function createElement() {
  return {
    className: "",
    innerHTML: "",
    children: [],
    appendChild(child) {
      this.children.push(child);
    },
    querySelector() {
      return {
        addEventListener() {},
      };
    },
  };
}

function loadRefreshMaterialList(windowValue) {
  const containers = {
    bibleFileList: createContainer(),
  };

  const sandbox = {
    window: windowValue,
    document: {
      getElementById(id) {
        return containers[id] || null;
      },
      createElement,
    },
    escapeHtml(value) {
      return String(value);
    },
    appendLog() {},
    confirm() {
      return true;
    },
  };

  const source = [
    extractFunctionSource("function _formatSize(bytes)"),
    extractFunctionSource("async function refreshMaterialList(folder, containerId)"),
    "globalThis.__refreshMaterialList = refreshMaterialList;",
  ].join("\n\n");

  vm.runInNewContext(source, sandbox, { filename: "material-panel-inline.js" });
  return {
    refreshMaterialList: sandbox.__refreshMaterialList,
    container: containers.bibleFileList,
  };
}

async function testOfflinePlaceholder() {
  const { refreshMaterialList, container } = loadRefreshMaterialList({});

  await refreshMaterialList("bible", "bibleFileList");

  assert.strictEqual(
    container.innerHTML,
    '<div class="material-empty">오프라인 모드</div>'
  );
}

async function testMaterialListRendersReturnedFiles() {
  const { refreshMaterialList, container } = loadRefreshMaterialList({
    geuldobiDesktop: {
      async listMaterialFiles(folder) {
        assert.strictEqual(folder, "bible");
        return {
          ok: true,
          files: [{ name: "demo.txt", size: 2048, isDir: false }],
        };
      },
      async deleteMaterialFile() {
        return { ok: true };
      },
    },
  });

  await refreshMaterialList("bible", "bibleFileList");

  assert.strictEqual(container.innerHTML, "");
  assert.strictEqual(container.children.length, 1);
  assert.ok(container.children[0].innerHTML.includes("demo.txt"));
  assert.ok(container.children[0].innerHTML.includes("2.0 KB"));
}

Promise.resolve()
  .then(testOfflinePlaceholder)
  .then(testMaterialListRendersReturnedFiles)
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });

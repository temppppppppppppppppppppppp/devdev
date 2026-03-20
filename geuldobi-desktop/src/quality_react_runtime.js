(function (global) {
  "use strict";

  function createRegistry() {
    return Object.create(null);
  }

  function renderTree(container, rootKey, tree, registry) {
    if (!container || !global.React || !global.ReactDOM) {
      return false;
    }
    if (typeof global.ReactDOM.render === "function") {
      global.ReactDOM.render(tree, container);
      return true;
    }
    if (typeof global.ReactDOM.createRoot === "function") {
      if (!registry[rootKey]) {
        registry[rootKey] = global.ReactDOM.createRoot(container);
      }
      registry[rootKey].render(tree);
      return true;
    }
    return false;
  }

  global.GeuldobiQualityReactRuntime = {
    createRegistry,
    renderTree,
  };
})(window);

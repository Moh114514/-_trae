(function () {
  "use strict";

  if (window.__beimsUnityPerfPatched) {
    return;
  }
  window.__beimsUnityPerfPatched = true;

  var MAX_DPR = 1.25;

  function patchUnityFactory() {
    if (typeof window.createUnityInstance !== "function" || window.__beimsCreateUnityWrapped) {
      return false;
    }

    var original = window.createUnityInstance;
    window.createUnityInstance = function (canvas, config, onProgress) {
      var cfg = Object.assign({}, config || {});
      var dpr = window.devicePixelRatio || 1;

      cfg.devicePixelRatio = Math.min(dpr, MAX_DPR);
      if (cfg.matchWebGLToCanvasSize == null) {
        cfg.matchWebGLToCanvasSize = true;
      }

      var attrs = Object.assign({}, cfg.webglContextAttributes || {});
      attrs.powerPreference = "high-performance";
      attrs.preserveDrawingBuffer = false;
      if (attrs.antialias == null) {
        attrs.antialias = false;
      }
      cfg.webglContextAttributes = attrs;

      return original(canvas, cfg, onProgress);
    };

    window.__beimsCreateUnityWrapped = true;
    return true;
  }

  if (!patchUnityFactory()) {
    var retry = setInterval(function () {
      if (patchUnityFactory()) {
        clearInterval(retry);
      }
    }, 120);
    setTimeout(function () {
      clearInterval(retry);
    }, 20000);
  }

  // Guard against accidental resize listeners that force fullscreen on every resize.
  var rawAddEventListener = window.addEventListener.bind(window);
  window.addEventListener = function (type, listener, options) {
    if (type === "resize" && typeof listener === "function") {
      var src = "";
      try {
        src = Function.prototype.toString.call(listener);
      } catch (err) {
        src = "";
      }

      if (src.indexOf("requestFullscreen") >= 0) {
        return;
      }
    }

    return rawAddEventListener(type, listener, options);
  };
})();

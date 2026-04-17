<template>
  <div class="building-3d-model">
    <div id="unity-container" class="unity-desktop">
      <canvas id="unity-canvas"></canvas>
      <div id="unity-loading-bar">
        <div id="unity-logo"></div>
        <div id="unity-progress-bar-empty">
          <div id="unity-progress-bar-full"></div>
        </div>
      </div>
      <div id="unity-warning"> </div>
      <div id="unity-footer">
        <div id="unity-fullscreen-button"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

let unityInstance = null

const initUnity = () => {
  var container = document.querySelector("#unity-container");
  var canvas = document.querySelector("#unity-canvas");
  var loadingBar = document.querySelector("#unity-loading-bar");
  var progressBarFull = document.querySelector("#unity-progress-bar-full");
  var fullscreenButton = document.querySelector("#unity-fullscreen-button");
  var warningBanner = document.querySelector("#unity-warning");

  function unityShowBanner(msg, type) {
    function updateBannerVisibility() {
      warningBanner.style.display = warningBanner.children.length ? 'block' : 'none';
    }
    var div = document.createElement('div');
    div.innerHTML = msg;
    warningBanner.appendChild(div);
    if (type == 'error') div.style = 'background: red; padding: 10px;';
    else {
      if (type == 'warning') div.style = 'background: yellow; padding: 10px;';
      setTimeout(function() {
        warningBanner.removeChild(div);
        updateBannerVisibility();
      }, 5000);
    }
    updateBannerVisibility();
  }

  var buildUrl = "/unity/Build";
  var loaderUrl = buildUrl + "/waibao.loader.js";
  var config = {
    dataUrl: buildUrl + "/waibao.data.unityweb",
    frameworkUrl: buildUrl + "/waibao.framework.js.unityweb",
    codeUrl: buildUrl + "/waibao.wasm.unityweb",
    streamingAssetsUrl: "StreamingAssets",
    companyName: "DefaultCompany",
    productName: "DataVisualization",
    productVersion: "0.1.0",
    showBanner: unityShowBanner,
  };

  if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
    var meta = document.createElement('meta');
    meta.name = 'viewport';
    meta.content = 'width=device-width, height=device-height, initial-scale=1.0, user-scalable=no, shrink-to-fit=yes';
    document.getElementsByTagName('head')[0].appendChild(meta);
    container.className = "unity-mobile";
    canvas.className = "unity-mobile";
    unityShowBanner('WebGL builds are not supported on mobile devices.');
  } else {
    canvas.style.width = "100%";
    canvas.style.height = "100%";
  }

  loadingBar.style.display = "block";

  var script = document.createElement("script");
  script.src = loaderUrl;
  script.onload = () => {
    createUnityInstance(canvas, config, (progress) => {
      progressBarFull.style.width = 100 * progress + "%";
    }).then((instance) => {
      unityInstance = instance;
      loadingBar.style.display = "none";
      fullscreenButton.onclick = () => {
        unityInstance.SetFullscreen(1);
      };
    }).catch((message) => {
      alert(message);
    });
  };
  document.body.appendChild(script);
}

const handleResize = () => {
  if (unityInstance) {
    unityInstance.Module.requestFullscreen();
  }
}

onMounted(() => {
  initUnity()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (unityInstance) {
    unityInstance.Quit();
  }
})
</script>

<style scoped>
.building-3d-model {
  width: 100%;
  height: 100%;
  position: relative;
  pointer-events: auto !important;
}

#unity-container {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: auto !important;
}

#unity-canvas {
  position: absolute;
  width: 100%;
  height: 100%;
  background: #0a1628;
  pointer-events: auto !important;
}

#unity-loading-bar {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  display: none;
}

#unity-logo {
  width: 154px;
  height: 130px;
  background: url('/unity/Build/TemplateData/unity-logo-dark.png') no-repeat center;
}

#unity-progress-bar-empty {
  width: 141px;
  height: 18px;
  margin-top: 10px;
  background: url('/unity/Build/TemplateData/progress-bar-empty-dark.png') no-repeat center;
}

#unity-progress-bar-full {
  width: 0%;
  height: 18px;
  margin-top: 10px;
  background: url('/unity/Build/TemplateData/progress-bar-full-dark.png') no-repeat center;
}

#unity-warning {
  position: absolute;
  left: 50%;
  top: 5%;
  transform: translate(-50%);
  background: white;
  padding: 10px;
  display: none;
}

#unity-footer {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 38px;
  line-height: 38px;
  background: url('/unity/Build/TemplateData/unity-logo-dark.png') no-repeat center left 10px;
  background-size: 20px 20px;
  padding-right: 10px;
  text-align: right;
  font-family: arial;
  font-size: 14px;
}

#unity-fullscreen-button {
  float: right;
  width: 38px;
  height: 38px;
  background: url('/unity/Build/TemplateData/fullscreen-button.png') no-repeat center;
  background-size: 20px 20px;
  cursor: pointer;
}

.unity-mobile #unity-footer {
  display: none;
}
</style>
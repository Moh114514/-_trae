<template>
  <div class="unity-animation-container" v-if="isUnityVisible">
    <div class="unity-canvas-wrapper" ref="unityWrapper">
      <!-- Unity WebGL 将在这里渲染 -->
      <canvas ref="unityCanvas" id="unity-canvas"></canvas>
    </div>
    <button class="unity-toggle-btn" @click="toggleUnityVisibility" title="切换Unity动画显示">
      {{ isUnityVisible ? '隐藏' : '显示' }}
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const isUnityVisible = ref(true)
const unityWrapper = ref(null)
const unityCanvas = ref(null)
let unityInstance = null

const toggleUnityVisibility = () => {
  isUnityVisible.value = !isUnityVisible.value
}

onMounted(() => {
  // 检查是否有 Unity WebGL 数据
  initializeUnityIfAvailable()
})

onUnmounted(() => {
  // 清理资源
  if (unityInstance) {
    unityInstance = null
  }
})

const initializeUnityIfAvailable = () => {
  // 检查是否存在 Unity 的加载脚本
  const unityLoaderScript = document.getElementById('unity-loader')
  if (unityLoaderScript) {
    // 使用存在的 Unity 加载器初始化
    loadUnityGame()
  } else {
    console.log('Unity WebGL 暂未配置，使用默认仪表板显示')
  }
}

const loadUnityGame = () => {
  // 这里可以集成实际的 Unity 加载代码
  // 示例：
  // unityInstance = new window.UnityLoader.instantiate("unityContainer", "Build/build.json", {
  //   onProgress: function(gameInstance, progress) {
  //     // 进度回调
  //   },
  //   onComplete: function(gameInstance) {
  //     unityInstance = gameInstance
  //   }
  // })
  console.log('Unity 游戏对象已准备好，等待加载脚本')
}
</script>

<style scoped>
.unity-animation-container {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 300px;
  background: rgba(0, 0, 0, 0.1);
  border-top: 1px solid rgba(100, 200, 255, 0.3);
  z-index: 100;
  overflow: hidden;
}

.unity-canvas-wrapper {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

#unity-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.unity-toggle-btn {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(70, 150, 255, 0.8);
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 101;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.unity-toggle-btn:hover {
  background: rgba(70, 150, 255, 1);
  box-shadow: 0 4px 12px rgba(70, 150, 255, 0.5);
}

.unity-toggle-btn:active {
  transform: scale(0.95);
}
</style>

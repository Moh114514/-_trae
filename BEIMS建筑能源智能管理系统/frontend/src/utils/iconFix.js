/**
 * 修复空气处理机组等状态项的图标
 * 解决 Element Plus icons 没有正确渲染的问题
 */

export function setupIconFix() {
  // 等待 DOM 加载完成
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixStatusIcons);
  } else {
    // 延迟执行，确保 Vue 应用已渲染
    setTimeout(fixStatusIcons, 500);
  }

  function fixStatusIcons() {
    // 等待 Vue 渲染完成
    setTimeout(() => {
      // 查找所有状态项中的 fan 图标
      const fanElements = document.querySelectorAll('.el-icon fan, .el-icon > fan');

      fanElements.forEach(fan => {
        const iconWrapper = fan.parentElement;

        // 如果父元素已经有 SVG，跳过
        if (iconWrapper.querySelector('svg')) return;

        // 创建 AHU (空气处理机组) SVG 图标
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 1024 1024');
        svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        svg.style.width = '100%';
        svg.style.height = '100%';

        // AHU 图标路径 - 代表空气处理机组
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('fill', 'currentColor');
        path.setAttribute('d', 'M192 192h640v640H192zM256 256v512h512V256zM320 320h384v96H320zm0 192h384v96H320z');

        svg.appendChild(path);
        iconWrapper.appendChild(svg);
      });

      console.log('✅ 空气处理机组图标已修复');
    }, 800);
  }

  // 也监听 Vue 路由变化
  window.addEventListener('hashchange', () => {
    setTimeout(fixStatusIcons, 500);
  });
}

export default setupIconFix;

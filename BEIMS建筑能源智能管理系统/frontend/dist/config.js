// 🔥 前端自动配置文件 (v2.0 - 改进版)
// 说明：此文件由「生成前端配置.ps1」脚本自动生成
// 作用：在页面加载时自动配置后端 API URL

(function() {
  'use strict';

  console.log('[配置初始化] 配置文件已加载');

  // 🔍 检查是否已有配置
  var savedURL = localStorage.getItem('BEIMS_API_BASE');
  if (savedURL) {
    console.log('[配置初始化] ✅ 已从 localStorage 恢复配置：' + savedURL);
    window.__BEIMS_CONFIG_READY__ = true;
    return;
  }

  // 🔥 直接设置后端 URL（正确的后端地址）
  var backendURL = 'https://acid-focal-affair-adds.trycloudflare.com';
  
  console.log('[配置初始化] 💚 自动设置后端 URL: ' + backendURL);
  localStorage.setItem('BEIMS_API_BASE', backendURL);
  window.__BEIMS_API_BASE__ = backendURL;
  
  console.log('[配置初始化] ✅ 已自动配置后端 URL: ' + backendURL);
  console.log('[配置初始化] 📱 前端访问地址: https://terry-genre-dreams-seemed.trycloudflare.com');
  window.__BEIMS_CONFIG_READY__ = true;
})();

/**
 * 智能问答浮窗组件 (优化版)
 * 支持拖拽移动、调整大小、Markdown渲染
 */

(function() {
  'use strict';

  // 🔥 API 配置 - 动态读取 + 候选回退
  function normalizeApiBase(url) {
    if (!url || typeof url !== 'string') {
      return '';
    }
    return url.trim().replace(/\/+$/, '');
  }

  function isLocalHostname(hostname) {
    return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
  }

  function isTunnelHost(host) {
    return host.indexOf('ngrok') !== -1 || host.indexOf('trycloudflare.com') !== -1;
  }

  function saveWorkingAPIBase(base) {
    var normalized = normalizeApiBase(base);
    if (!normalized) {
      return;
    }

    try {
      localStorage.setItem('BEIMS_API_BASE', normalized);
    } catch (e) {
      console.warn('[AI Chat] localStorage 写入失败:', e);
    }

    window.__BEIMS_API_BASE__ = normalized;
    console.log('[AI Chat] ✅ API 地址已更新:', normalized);
  }

  function getAPIBaseCandidates() {
    var candidates = [];

    function pushCandidate(base, source) {
      var normalized = normalizeApiBase(base);
      if (!normalized) {
        return;
      }
      if (candidates.indexOf(normalized) !== -1) {
        return;
      }

      candidates.push(normalized);
      console.log('[AI Chat] API 候选(' + source + '):', normalized);
    }

    var fromStorage = '';
    try {
      fromStorage = localStorage.getItem('BEIMS_API_BASE') || '';
    } catch (e) {
      console.warn('[AI Chat] localStorage 读取失败:', e);
    }

    pushCandidate(fromStorage, 'localStorage');
    pushCandidate(window.__BEIMS_API_BASE__, 'global');

    var host = window.location.host;
    var hostname = window.location.hostname;
    var protocol = window.location.protocol;
    var sameOrigin = protocol + '//' + host;

    if (isTunnelHost(host)) {
      pushCandidate(sameOrigin, 'tunnel-origin');
    }

    if (isLocalHostname(hostname)) {
      pushCandidate('http://localhost:8001', 'local-default');
      if (hostname === '127.0.0.1') {
        pushCandidate('http://127.0.0.1:8001', 'local-127-fallback');
      }
    } else {
      pushCandidate(sameOrigin, 'same-origin');
      pushCandidate('http://localhost:8001', 'cross-env-fallback');
    }

    if (candidates.length === 0) {
      pushCandidate('http://localhost:8001', 'hardcoded-default');
    }

    return candidates;
  }

  function getAPIBase() {
    var candidates = getAPIBaseCandidates();
    return candidates[0];
  }

  function getChatUrlCandidates() {
    var bases = getAPIBaseCandidates();
    return bases.map(function(base) {
      return base + '/chat';
    });
  }

  // 状态
  var isOpen = false;
  var isLoading = false;
  var isDragging = false;
  var isResizing = false;
  var dragOffset = { x: 0, y: 0 };

  // 停止按钮相关状态
  var currentTypewriter = null;  // 当前打字机控制对象
  var currentAbortController = null;  // 当前请求的 AbortController

  // 🔥 新增：防抖和状态锁机制
  var isProcessing = false;  // 全局处理锁（比 isLoading 更严格）
  var lastClickTime = 0;     // 上次点击时间戳
  var DEBOUNCE_DELAY = 800;  // 防抖延迟（毫秒）

  // 创建样式
  function createStyles() {
    var style = document.createElement('style');
    style.id = 'ai-chat-styles';
    style.textContent = `
      #ai-chat-float-btn {
        position: fixed; right: 24px; bottom: 24px; width: 56px; height: 56px;
        border-radius: 50%; background: linear-gradient(135deg, #00bfff 0%, #0080ff 100%);
        box-shadow: 0 4px 16px rgba(0,191,255,0.4); cursor: pointer; z-index: 99999;
        display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; border: none;
      }
      #ai-chat-float-btn:hover { transform: scale(1.1); box-shadow: 0 6px 24px rgba(0,191,255,0.5); }
      #ai-chat-float-btn svg { width: 28px; height: 28px; fill: white; }
      #ai-chat-window {
        position: fixed; right: 24px; bottom: 96px; width: 420px; height: 560px;
        min-width: 320px; min-height: 400px; max-width: 800px; max-height: 90vh;
        background: #fff; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        z-index: 99998; display: none; flex-direction: column; overflow: hidden;
        font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif; resize: both;
      }
      #ai-chat-window.open { display: flex; animation: slideUp 0.3s ease; }
      #ai-chat-window.dragging { transition: none; user-select: none; }
      @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
      #ai-chat-header {
        background: linear-gradient(135deg, #00bfff 0%, #0080ff 100%); color: white;
        padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; cursor: move;
      }
      #ai-chat-header .title { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
      #ai-chat-header .close-btn {
        background: rgba(255,255,255,0.2); border: none; color: white; width: 28px; height: 28px;
        border-radius: 50%; cursor: pointer; font-size: 18px; transition: background 0.2s;
      }
      #ai-chat-header .close-btn:hover { background: rgba(255,255,255,0.3); }
      #ai-chat-header .header-actions { display: flex; gap: 8px; align-items: center; }
      #ai-chat-header .reset-btn {
        background: rgba(255,255,255,0.15); border: none; color: white; padding: 4px 10px;
        border-radius: 12px; font-size: 12px; cursor: pointer; transition: background 0.2s;
      }
      #ai-chat-header .reset-btn:hover { background: rgba(255,255,255,0.25); }
      #ai-chat-messages { flex: 1; padding: 16px; overflow-y: auto; background: #f5f7fa; }
      #ai-chat-messages .message { margin-bottom: 16px; display: flex; }
      #ai-chat-messages .message.user { justify-content: flex-end; }
      #ai-chat-messages .message.assistant { justify-content: flex-start; }
      #ai-chat-messages .message-content {
        max-width: 85%; padding: 12px 16px; border-radius: 12px; line-height: 1.6; font-size: 14px;
      }
      #ai-chat-messages .message.user .message-content {
        background: linear-gradient(135deg, #00bfff 0%, #0080ff 100%); color: white; border-bottom-right-radius: 4px;
      }
      #ai-chat-messages .message.assistant .message-content {
        background: white; color: #333; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      }
      .message-content h1,.message-content h2,.message-content h3 { margin: 12px 0 8px 0; font-weight: 600; color: #333; }
      .message-content h1 { font-size: 18px; } .message-content h2 { font-size: 16px; } .message-content h3 { font-size: 15px; }
      .message-content p { margin: 8px 0; }
      .message-content ul,.message-content ol { margin: 8px 0; padding-left: 20px; }
      .message-content li { margin: 4px 0; }
      .message-content code {
        background: #f0f2f5; padding: 2px 6px; border-radius: 4px; font-family: Consolas,Monaco,monospace; font-size: 13px;
      }
      .message-content pre { background: #282c34; color: #abb2bf; padding: 12px; border-radius: 8px; overflow-x: auto; margin: 8px 0; }
      .message-content pre code { background: none; padding: 0; color: inherit; }
      .message-content blockquote { border-left: 3px solid #00bfff; padding-left: 12px; margin: 8px 0; color: #666; }
      .message-content table { border-collapse: collapse; margin: 8px 0; font-size: 13px; }
      .message-content th,.message-content td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; }
      .message-content th { background: #f0f2f5; font-weight: 600; }
      .message-content hr { border: none; border-top: 1px solid #eee; margin: 12px 0; }
      .message-content strong { font-weight: 600; } .message-content em { font-style: italic; }
      .typing-indicator { display: flex; gap: 4px; padding: 4px 0; }
      .typing-indicator span { width: 6px; height: 6px; background: #00bfff; border-radius: 50%; animation: typing 1.4s infinite; }
      .typing-indicator span:nth-child(2) { animation-delay: 0.2s; } .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
      @keyframes typing { 0%,60%,100% { transform: translateY(0); opacity: 0.4; } 30% { transform: translateY(-4px); opacity: 1; } }
      
      /* 打字机光标动画 */
      .typing-cursor::after {
        content: '|'; color: #00bfff; font-weight: bold;
        animation: cursorBlink 1s infinite; margin-left: 2px;
      }
      @keyframes cursorBlink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
      
      /* 正在思考指示器增强 */
      .thinking-indicator {
        display: flex; align-items: center; gap: 8px; padding: 8px 12px;
        color: #666; font-size: 13px; font-style: italic;
      }
      .thinking-icon {
        width: 20px; height: 20px; border: 2px solid #00bfff;
        border-top-color: transparent; border-radius: 50%;
        animation: spin 1s linear infinite;
      }
      @keyframes spin { to { transform: rotate(360deg); } }
      
      /* 跳过等待按钮 */
      .skip-wait-btn {
        margin-top: 8px; padding: 4px 12px; background: #f0f2f5;
        border: 1px solid #ddd; border-radius: 12px; font-size: 11px;
        color: #666; cursor: pointer; transition: all 0.2s; display: none;
      }
      .skip-wait-btn:hover { background: #00bfff; color: white; border-color: #00bfff; }
      
      /* 停止按钮 */
      #ai-chat-stop-btn {
        display: none; padding: 8px 16px; border-radius: 20px;
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        color: white; border: none; cursor: pointer; font-size: 13px;
        font-weight: 600; transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(238,90,82,0.3);
      }
      #ai-chat-stop-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(238,90,82,0.4);
      }
      #ai-chat-stop-btn:active { transform: scale(0.95); }
      #ai-chat-stop-btn.show { display: inline-flex; align-items: center; gap: 6px; }
      #ai-chat-stop-btn svg { width: 14px; height: 14px; fill: white; }
      
      /* 截断提示消息 */
      .truncation-notice {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%) !important;
        color: #856404 !important;
        border-left: 3px solid #ffc107 !important;
        font-size: 12px !important;
        padding: 8px 12px !important;
        font-style: italic;
      }
      #ai-chat-input-area { padding: 12px 16px; background: white; border-top: 1px solid #eee; display: flex; gap: 8px; }
      #ai-chat-input {
        flex: 1; padding: 10px 14px; border: 1px solid #ddd; border-radius: 20px; font-size: 14px; outline: none; transition: border-color 0.2s;
      }
      #ai-chat-input:focus { border-color: #00bfff; }
      #ai-chat-send {
        width: 40px; height: 40px; border-radius: 50%;
        background: linear-gradient(135deg, #00bfff 0%, #0080ff 100%); border: none; color: white; cursor: pointer;
        display: flex; align-items: center; justify-content: center; transition: transform 0.2s, box-shadow 0.2s;
      }
      #ai-chat-send:hover { transform: scale(1.05); box-shadow: 0 2px 8px rgba(0,191,255,0.4); }
      #ai-chat-send:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
      #ai-chat-quick-questions { padding: 0 16px 12px; background: white; display: flex; flex-wrap: wrap; gap: 8px; }
      .quick-btn {
        padding: 6px 12px; background: #f0f2f5; border: 1px solid #e0e0e0; border-radius: 16px;
        font-size: 12px; color: #666; cursor: pointer; transition: all 0.2s;
      }
      .quick-btn:hover { background: #00bfff; color: white; border-color: #00bfff; }
      #ai-chat-resize-handle {
        position: absolute; right: 0; bottom: 0; width: 16px; height: 16px; cursor: se-resize;
        background: linear-gradient(135deg, transparent 50%, #ccc 50%); border-radius: 0 0 16px 0;
      }
    `;
    document.head.appendChild(style);
  }

  // 创建浮动按钮
  function createFloatButton() {
    var btn = document.createElement('div');
    btn.id = 'ai-chat-float-btn';
    btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>';
    btn.title = '智能问答';
    btn.onclick = toggleChat;
    document.body.appendChild(btn);
  }

  // 创建聊天窗口
  function createChatWindow() {
    var win = document.createElement('div');
    win.id = 'ai-chat-window';
    win.innerHTML = '<div id="ai-chat-header">' +
      '<div class="title">' +
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>' +
        '智能问答助手' +
      '</div>' +
      '<div class="header-actions">' +
        '<button class="reset-btn" onclick="window.AIChat.resetChat()">清空对话</button>' +
        '<button class="close-btn" onclick="window.AIChat.close()">x</button>' +
      '</div>' +
    '</div>' +
    '<div id="ai-chat-messages">' +
      '<div class="message assistant"><div class="message-content">' +
        '您好！我是建筑能源管理系统的智能助手。<br><br>' +
        '<strong>我可以帮您：</strong><ul>' +
          '<li>查询能耗数据（电力、水、空调）</li>' +
          '<li>分析 COP 制冷效率</li>' +
          '<li>检测能耗异常</li>' +
          '<li>提供节能建议</li>' +
        '</ul>' +
      '</div></div>' +
    '</div>' +
    '<div id="ai-chat-quick-questions">' +
      '<button class="quick-btn" onclick="window.AIChat.sendQuick(\'查询今日能耗\')">查询今日能耗</button>' +
      '<button class="quick-btn" onclick="window.AIChat.sendQuick(\'COP效率如何\')">COP效率如何</button>' +
      '<button class="quick-btn" onclick="window.AIChat.sendQuick(\'有无异常警告\')">有无异常警告</button>' +
    '</div>' +
    '<div id="ai-chat-input-area">' +
      '<input type="text" id="ai-chat-input" placeholder="输入您的问题..." />' +
      '<button id="ai-chat-stop-btn" onclick="window.AIChat.stopResponse()">' +
        '<svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>' +
        '停止' +
      '</button>' +
      '<button id="ai-chat-send" onclick="window.AIChat.sendMessage()">' +
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>' +
      '</button>' +
    '</div>' +
    '<div id="ai-chat-resize-handle"></div>';
    document.body.appendChild(win);
    bindDragEvents();
    bindResizeEvents();
    var input = document.getElementById('ai-chat-input');
    input.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') { sendMessage(); }
    });
  }

  // 拖拽事件
  function bindDragEvents() {
    var header = document.getElementById('ai-chat-header');
    var win = document.getElementById('ai-chat-window');
    header.addEventListener('mousedown', function(e) {
      if (e.target.closest('.close-btn') || e.target.closest('.reset-btn')) return;
      isDragging = true;
      win.classList.add('dragging');
      var rect = win.getBoundingClientRect();
      dragOffset.x = e.clientX - rect.left;
      dragOffset.y = e.clientY - rect.top;
      e.preventDefault();
    });
    document.addEventListener('mousemove', function(e) {
      if (!isDragging) return;
      var win = document.getElementById('ai-chat-window');
      var x = e.clientX - dragOffset.x;
      var y = e.clientY - dragOffset.y;
      x = Math.max(0, Math.min(x, window.innerWidth - win.offsetWidth));
      y = Math.max(0, Math.min(y, window.innerHeight - win.offsetHeight));
      win.style.left = x + 'px';
      win.style.top = y + 'px';
      win.style.right = 'auto';
      win.style.bottom = 'auto';
    });
    document.addEventListener('mouseup', function() {
      if (isDragging) {
        isDragging = false;
        document.getElementById('ai-chat-window').classList.remove('dragging');
      }
    });
  }

  // 调整大小事件
  function bindResizeEvents() {
    var handle = document.getElementById('ai-chat-resize-handle');
    var startX, startY, startWidth, startHeight;
    handle.addEventListener('mousedown', function(e) {
      isResizing = true;
      var win = document.getElementById('ai-chat-window');
      startX = e.clientX; startY = e.clientY;
      startWidth = win.offsetWidth; startHeight = win.offsetHeight;
      e.preventDefault(); e.stopPropagation();
    });
    document.addEventListener('mousemove', function(e) {
      if (!isResizing) return;
      var win = document.getElementById('ai-chat-window');
      var nw = Math.max(320, Math.min(startWidth + (e.clientX - startX), 800));
      var nh = Math.max(400, Math.min(startHeight + (e.clientY - startY), window.innerHeight * 0.9));
      win.style.width = nw + 'px';
      win.style.height = nh + 'px';
    });
    document.addEventListener('mouseup', function() { isResizing = false; });
  }

  // 切换聊天窗口
  function toggleChat() {
    var win = document.getElementById('ai-chat-window');
    isOpen = !isOpen;
    if (isOpen) { win.classList.add('open'); document.getElementById('ai-chat-input').focus(); }
    else { win.classList.remove('open'); }
  }

  // 关闭聊天窗口
  function closeChat() {
    isOpen = false;
    document.getElementById('ai-chat-window').classList.remove('open');
  }

  // 重置对话
  function resetChat() {
    var container = document.getElementById('ai-chat-messages');
    container.innerHTML = '<div class="message assistant"><div class="message-content">对话已清空。请问有什么可以帮您的？</div></div>';
  }
  
  // 停止当前响应（截断模式：只保留已输出的部分）
  function stopResponse() {
    console.log('[AI Chat] Stop button clicked - truncating output');

    // 🔥 防止重复调用（如果已经停止过就不再处理）
    if (!currentTypewriter && !currentAbortController) {
      console.log('[AI Chat] ⚠️ 已经停止过了，忽略重复点击');
      return;
    }

    // 1. 取消正在进行的网络请求
    if (currentAbortController) {
      currentAbortController.abort();
      currentAbortController = null;
    }

    // 2. 截断打字机效果（停止在当前位置，不显示剩余内容）
    if (currentTypewriter) {
      currentTypewriter.truncate();  // 这会触发 onComplete 回调 → 自动调用 addTruncationNotice()
      currentTypewriter = null;     // 立即清空引用防止重复
    } else {
      // 如果没有打字机在运行（比如还在"思考"阶段），手动添加提示
      addTruncationNotice();
    }

    // 3. 隐藏"正在思考"动画
    hideTyping();

    // 4. 隐藏停止按钮
    hideStopButton();

    // 5. ✅ 使用统一的状态恢复函数
    resetAllStates();

    console.log('[AI Chat] Output truncated, UI restored');
  }

  // 🔥 新增：统一禁用/启用所有输入元素
  function disableAllInputs(disabled) {
    var input = document.getElementById('ai-chat-input');
    var sendBtn = document.getElementById('ai-chat-send');
    var quickBtns = document.querySelectorAll('.quick-btn');

    if (input) input.disabled = disabled;
    if (sendBtn) sendBtn.disabled = disabled;

    // 同时禁用快捷问题按钮
    quickBtns.forEach(function(btn) {
      btn.disabled = disabled;
      btn.style.opacity = disabled ? '0.5' : '1';
      btn.style.cursor = disabled ? 'not-allowed' : 'pointer';
    });

    console.log('[AI Chat] All inputs ' + (disabled ? 'disabled' : 'enabled'));
  }

  // 🔥 新增：统一重置所有状态（唯一入口）
  function resetAllStates() {
    isLoading = false;
    isProcessing = false;  // 🔥 释放全局锁
    lastClickTime = 0;      // 🔥 重置防抖计时器

    // 恢复所有输入元素
    disableAllInputs(false);

    // 隐藏停止按钮
    hideStopButton();

    console.log('[AI Chat] ✅ All states reset (isLoading=' + isLoading + ', isProcessing=' + isProcessing + ')');
  }

  function buildReportUrlFromAction(action) {
    var payload = action && action.payload ? action.payload : {};
    var reportUrl = new URL('/report', window.location.origin);
    var params = reportUrl.searchParams;

    params.set('auto_report', '1');

    if (payload.auto_export === 'html') {
      params.set('auto_export', 'html');
    }

    if (payload.building_id) {
      params.set('building_id', payload.building_id);
    }

    if (Array.isArray(payload.building_ids) && payload.building_ids.length > 0) {
      params.set('building_ids', payload.building_ids.join(','));
    }

    if (payload.start_time) {
      params.set('start_time', payload.start_time);
    }

    if (payload.end_time) {
      params.set('end_time', payload.end_time);
    }

    if (payload.top_n) {
      params.set('top_n', String(payload.top_n));
    }

    if (payload.carbon_factor) {
      params.set('carbon_factor', String(payload.carbon_factor));
    }

    return reportUrl.toString();
  }

  function executeUIAction(action) {
    if (!action || action.type !== 'open_report') {
      return false;
    }

    var targetUrl = buildReportUrlFromAction(action);
    console.log('[AI Chat] 执行报表动作 ->', targetUrl);

    setTimeout(function() {
      window.location.href = targetUrl;
    }, 250);

    return true;
  }
  
  // 添加截断提示消息
  function addTruncationNotice() {
    var container = document.getElementById('ai-chat-messages');
    var notice = document.createElement('div');
    notice.className = 'message assistant';
    notice.innerHTML = '<div class="message-content truncation-notice">⏹️ 输出已停止</div>';
    container.appendChild(notice);
    container.scrollTop = container.scrollHeight;
  }
  
  // 显示停止按钮
  function showStopButton() {
    var stopBtn = document.getElementById('ai-chat-stop-btn');
    console.log('[AI Chat] Showing stop button, element:', stopBtn);
    if (stopBtn) {
      stopBtn.classList.add('show');
      console.log('[AI Chat] Stop button should now be visible');
    } else {
      console.error('[AI Chat] Stop button element not found!');
    }
  }
  
  // 隐藏停止按钮
  function hideStopButton() {
    var stopBtn = document.getElementById('ai-chat-stop-btn');
    if (stopBtn) {
      stopBtn.classList.remove('show');
    }
  }

  // 发送快捷问题
  function sendQuick(text) {
    var input = document.getElementById('ai-chat-input');
    input.value = text;
    sendMessage();
  }

  // 发送消息（🔥 增强版：带防抖和强制状态锁）
  function sendMessage() {
    var input = document.getElementById('ai-chat-input');
    var text = input.value.trim();

    // 🔒 第一重防护：空消息检查
    if (!text) {
      console.log('[AI Chat] Empty message, ignored');
      return;
    }

    // 🔒 第二重防护：防抖检查（防止快速连续点击）
    var now = Date.now();
    if (now - lastClickTime < DEBOUNCE_DELAY) {
      console.log('[AI Chat] Debounce: click too fast (' + (now - lastClickTime) + 'ms < ' + DEBOUNCE_DELAY + 'ms), ignored');
      return;
    }
    lastClickTime = now;

    // 🔒 第三重防护：全局处理锁（最严格的检查）
    if (isProcessing || isLoading) {
      console.log('[AI Chat] Already processing (isProcessing=' + isProcessing + ', isLoading=' + isLoading + '), ignored');
      return;
    }

    // ✅ 通过所有检查，开始处理
    isProcessing = true;  // 设置全局锁
    isLoading = true;

    console.log('[AI Chat] ✅ Message accepted: "' + text.substring(0, 30) + '..."');

    addMessage('user', text, false);
    input.value = '';

    // 禁用所有交互元素（防止再次点击）
    disableAllInputs(true);

    // 显示停止按钮
    showStopButton();

    // 显示"正在思考"动画
    showTyping();

    // 创建 AbortController 用于取消请求
    currentAbortController = new AbortController();

    // 🔥 构建 API 候选地址（地址失效时自动回退）
    var chatUrlCandidates = getChatUrlCandidates();
    console.log('[AI Chat] Chat URL candidates:', chatUrlCandidates);

    function shouldTryNextCandidate(error) {
      if (!error) {
        return false;
      }

      if (error.name === 'AbortError' || error.message === 'Request aborted') {
        return false;
      }

      if (error.__httpStatus === 404 || error.__httpStatus === 502 || error.__httpStatus === 503 || error.__httpStatus === 504) {
        return true;
      }

      if (error.name === 'TypeError') {
        return true;
      }

      return typeof error.message === 'string' && /Failed to fetch|NetworkError|Load failed/i.test(error.message);
    }

    function fetchWithFallback(index) {
      var chatUrl = chatUrlCandidates[index];
      console.log('🚀 Calling chat API:', chatUrl, '| candidate', (index + 1) + '/' + chatUrlCandidates.length);

      return fetch(chatUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
        signal: currentAbortController.signal
      })
      .then(function(response) {
        if (currentAbortController && currentAbortController.signal.aborted) {
          throw new Error('Request aborted');
        }

        if (!response.ok) {
          var httpError = new Error('HTTP ' + response.status + ' @ ' + chatUrl);
          httpError.__httpStatus = response.status;
          throw httpError;
        }

        saveWorkingAPIBase(chatUrl.replace(/\/chat$/, ''));
        return response.json();
      })
      .catch(function(error) {
        if (shouldTryNextCandidate(error) && index < chatUrlCandidates.length - 1) {
          console.warn('[AI Chat] API 候选失败，尝试下一个:', chatUrl, error.message || error);
          return fetchWithFallback(index + 1);
        }
        throw error;
      });
    }

    fetchWithFallback(0)
    .then(function(data) {
      // 检查是否被中止
      if (currentAbortController && currentAbortController.signal.aborted) {
        throw new Error('Request aborted');
      }

      // 检查是否被中止（在解析JSON后）
      if (currentAbortController && currentAbortController.signal.aborted) {
        throw new Error('Request aborted');
      }

      hideTyping();

      currentAbortController = null;  // 请求已完成，清除AbortController

      if (data.response) {
        var uiAction = data && data.context && data.context.ui_action;
        if (uiAction) {
          pendingResponse = null;
          currentTypewriter = null;
          addMessage('assistant', data.response, false);
          resetAllStates();
          executeUIAction(uiAction);
          return;
        }

        // 检查是否为超长文本（数据查询结果）
        var isLongText = data.response.length > 2000;

        // 保存响应（用于跳过等待功能）
        pendingResponse = data.response;

        // 🔥 定义打字机完成回调（事件驱动，不依赖定时器）
        function onTypewriterComplete(isTruncated) {
          console.log('[AI Chat] ✅ Typewriter event received (truncated=' + isTruncated + ')');

          // 清理资源
          pendingResponse = null;
          currentTypewriter = null;

          // 如果是被截断的，添加提示
          if (isTruncated) {
            addTruncationNotice();
          }

          // ✅ 统一恢复所有状态（只在真正完成后执行！）
          resetAllStates();
        }

        // 使用打字机效果显示并传入完成回调
        currentTypewriter = addMessageWithTypewriter(data.response, onTypewriterComplete);

        // 如果是超长文本，立即显示跳过按钮（不影响状态管理）
        if (isLongText) {
          setTimeout(function() {
            var skipBtn = document.querySelector('.skip-wait-btn');
            if (skipBtn) {
              skipBtn.style.display = 'inline-block';
              skipBtn.textContent = '查看完整数据 (' + Math.round(data.response.length / 1000) + 'K字符)';
            }
          }, 100);
        }

        // ⚠️ 注意：这里不再有 setTimeout 来强制重置状态！
        // 状态重置完全依赖 onTypewriterComplete 回调
        // 这样确保只有在打字机真正完成（或被停止）后才会恢复状态

      } else {
        addMessage('assistant', '抱歉，我无法理解您的问题。', true);
        resetAllStates();  // 即使失败也要恢复状态
      }
    })
    .catch(function(error) {
      // 忽略中止错误
      if (error.name === 'AbortError' || error.message === 'Request aborted') {
        console.log('[AI Chat] Response stopped by user');
        return;  // 注意：停止时不要调用 resetAllStates()，由 stopResponse() 处理
      }

      hideTyping();
      hideStopButton();
      isLoading = false;
      isProcessing = false;  // 🔥 新增：释放全局锁
      currentAbortController = null;

      // 恢复输入框和发送按钮
      disableAllInputs(false);

      addMessage('assistant', '抱歉，服务暂时不可用，请稍后再试。', true);
      console.error('Chat API Error:', error);
    });
  }

  // 添加消息
  function addMessage(role, content, useTypewriter) {
    var container = document.getElementById('ai-chat-messages');
    var msg = document.createElement('div');
    msg.className = 'message ' + role;
    
    if (role === 'assistant' && useTypewriter !== false) {
      // 使用打字机效果（不保存控制对象）
      var rendered = renderMarkdown(content);
      msg.innerHTML = '<div class="message-content typing-cursor"></div>';
      container.appendChild(msg);
      container.scrollTop = container.scrollHeight;
      
      // 开始打字机动画
      typeWriter(msg.querySelector('.message-content'), rendered);
    } else {
      // 直接显示（用户消息或禁用打字机）
      var rendered = role === 'assistant' ? renderMarkdown(content) : escapeHtml(content);
      msg.innerHTML = '<div class="message-content">' + rendered + '</div>';
      container.appendChild(msg);
      container.scrollTop = container.scrollHeight;
    }
  }
  
  // 添加消息（带打字机控制对象 + 完成回调）
  function addMessageWithTypewriter(content, onComplete) {
    var container = document.getElementById('ai-chat-messages');
    var msg = document.createElement('div');
    msg.className = 'message assistant';

    // 使用打字机效果并返回控制对象
    var rendered = renderMarkdown(content);
    msg.innerHTML = '<div class="message-content typing-cursor"></div>';
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;

    // 开始打字机动画并返回控制对象
    return typeWriter(msg.querySelector('.message-content'), rendered, onComplete);
  }
  
  // 打字机效果函数（🔥 增强版：基于事件驱动的状态管理）
  function typeWriter(element, htmlContent, onComplete) {
    // 创建临时容器来解析 HTML
    var tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;

    // 提取纯文本内容（保留基本结构）
    var textContent = tempDiv.textContent || '';

    // 🔥 关键修复：根据长度选择显示策略
    var MAX_TYPING_LENGTH = 2000;  // 超过此长度直接显示

    if (textContent.length > MAX_TYPING_LENGTH) {
      // 超长文本：直接显示 + 渐入动画（避免"死循环"）
      element.style.opacity = '0';
      element.style.transition = 'opacity 0.5s ease-in';
      element.innerHTML = htmlContent;

      // 强制重排后触发动画
      requestAnimationFrame(function() {
        element.style.opacity = '1';

        console.log('[AI Chat] Long text displayed, calling onComplete callback');

        // ✅ 超长文本显示完成后调用回调
        if (typeof onComplete === 'function') {
          onComplete();
        }
      });

      return { cancel: function() {}, skip: function() {} };
    }

    // 正常/短文本：使用打字机效果
    var charIndex = 0;
    var isStopped = false;  // 截断标志

    // 计算速度（根据长度自适应）
    var baseSpeed = 1; // 基础速度 ms/字
    var speed = textContent.length > 1000 ? 15 : (textContent.length > 500 ? 20 : baseSpeed);

    // 打字机主函数
    function type() {
      // 检查是否被停止
      if (isStopped) {
        console.log('[AI Chat] Typewriter stopped at char', charIndex, 'of', textContent.length);
        element.classList.remove('typing-cursor');

        // 🔥 即使停止也要调用回调（让上层知道打字机已结束）
        if (typeof onComplete === 'function') {
          onComplete(true);  // true 表示被截断
        }
        return;
      }

      if (charIndex < textContent.length) {
        // 每次添加一个字符
        element.innerHTML = escapeHtml(textContent.substring(0, charIndex + 1));
        charIndex++;

        // 自动滚动到底部
        var container = document.getElementById('ai-chat-messages');
        container.scrollTop = container.scrollHeight;

        setTimeout(type, speed);
      } else {
        // ✅ 打字真正完成！
        element.innerHTML = htmlContent;
        element.classList.remove('typing-cursor');

        var container = document.getElementById('ai-chat-messages');
        container.scrollTop = container.scrollHeight;

        console.log('[AI Chat] Typewriter naturally completed, calling onComplete callback');

        // 🔥 只在真正完成时才调用回调
        if (typeof onComplete === 'function') {
          onComplete(false);  // false 表示正常完成
        }
      }
    }

    // 开始打字
    setTimeout(type, 100); // 短暂延迟后开始

    // 返回控制对象（可用于取消或截断）
    return {
      cancel: function() {
        // 完整显示模式：立即显示全部内容
        charIndex = textContent.length;
        element.innerHTML = htmlContent;
        element.classList.remove('typing-cursor');
      },
      skip: function() {
        this.cancel();
      },
      truncate: function() {
        // 截断模式：停止在当前位置，只保留已输出的部分
        console.log('[AI Chat] truncate() called, current position:', charIndex);
        isStopped = true;  // 设置停止标志
        element.classList.remove('typing-cursor');  // 移除光标
      }
    };
  }

  // HTML 转义
  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // 简化 Markdown 渲染
  function renderMarkdown(text) {
    // 先清理 HTML 标签（保留换行）
    var cleanText = text.replace(/<[^>]+>/g, '');
    
    var html = escapeHtml(cleanText);
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    html = html.replace(/^\- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
    html = html.replace(/^---$/gm, '<hr>');
    html = html.replace(/\n/g, '<br>');
    html = html.replace(/<br><br>/g, '</p><p>');
    html = html.replace(/<h([1-6])><br>/g, '<h$1>');
    html = html.replace(/<br><\/h([1-6])>/g, '</h$1>');
    html = html.replace(/<ul><br>/g, '<ul>');
    html = html.replace(/<br><\/ul>/g, '</ul>');
    html = html.replace(/<li><br>/g, '<li>');
    return html;
  }

  // 显示打字动画（正在思考）
  function showTyping() {
    var container = document.getElementById('ai-chat-messages');
    var typing = document.createElement('div');
    typing.id = 'ai-typing';
    typing.className = 'message assistant';
    
    // 随机选择思考提示语
    var thinkingTexts = [
      'AI 正在思考中',
      '正在分析您的问题',
      '查询数据中...',
      '稍等片刻'
    ];
    var randomText = thinkingTexts[Math.floor(Math.random() * thinkingTexts.length)];
    
    typing.innerHTML = '<div class="message-content">' +
      '<div class="thinking-indicator">' +
        '<div class="thinking-icon"></div>' +
        '<span>' + randomText + '</span>' +
      '</div>' +
      '<button class="skip-wait-btn" onclick="window.AIChat.skipWaiting()">跳过等待</button>' +
    '</div>';
    
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
  }
  
  // 跳过等待（立即显示结果）
  var pendingResponse = null;
  function skipWaiting() {
    if (pendingResponse) {
      hideTyping();
      addMessage('assistant', pendingResponse, false); // 禁用打字机，直接显示
      pendingResponse = null;
    }
  }

  // 隐藏打字动画
  function hideTyping() {
    var typing = document.getElementById('ai-typing');
    if (typing) typing.remove();
  }

  // 检查当前页面是否是登录页面
  function isLoginPage() {
    var mainFrame = document.getElementById('mainFrame');
    if (mainFrame && mainFrame.contentWindow) {
      try {
        var iframeSrc = (mainFrame.src || '').toLowerCase();
        var iframePath = mainFrame.contentWindow.location.pathname.toLowerCase();
        var iframeTitle = mainFrame.contentDocument ? mainFrame.contentDocument.title : '';
        if (iframeSrc.indexOf('login') !== -1 || iframeSrc.indexOf('用户登录') !== -1 ||
            iframePath.indexOf('login') !== -1 || iframePath.indexOf('用户登录') !== -1 ||
            iframeTitle.indexOf('login') !== -1 || iframeTitle.indexOf('登录') !== -1) return true;
      } catch (e) {
        if (mainFrame.src && (mainFrame.src.indexOf('用户登录') !== -1 || mainFrame.src.indexOf('login') !== -1)) return true;
      }
    }
    var path = window.location.pathname.toLowerCase();
    var filename = path.split('/').pop() || '';
    return filename.indexOf('login') !== -1 || filename.indexOf('用户登录') !== -1 ||
           document.title.toLowerCase().indexOf('login') !== -1 || document.title.indexOf('登录') !== -1;
  }

  // 显示/隐藏浮窗
  function updateVisibility() {
    var btn = document.getElementById('ai-chat-float-btn');
    var win = document.getElementById('ai-chat-window');
    if (isLoginPage()) {
      if (btn) btn.style.display = 'none';
      if (win) win.classList.remove('open');
      console.log('[AI Chat] 登录页面，隐藏浮窗');
    } else {
      if (btn) btn.style.display = 'flex';
      console.log('[AI Chat] 非登录页面，显示浮窗');
    }
  }

  // 🔥 处理点击外面关闭窗口
  function setupClickOutsideListener() {
    document.addEventListener('click', function(event) {
      if (!isOpen) return;  // 窗口未打开，忽略
      
      var chatWindow = document.getElementById('ai-chat-window');
      var floatBtn = document.getElementById('ai-chat-float-btn');
      
      // 检查点击是否在 widget 内部
      var clickedInsideWindow = chatWindow && chatWindow.contains(event.target);
      var clickedInsideBtn = floatBtn && floatBtn.contains(event.target);
      
      // 如果点击在 widget 外部，关闭窗口
      if (!clickedInsideWindow && !clickedInsideBtn) {
        console.log('[AI Chat] 检测到外部点击，关闭窗口');
        closeChat();
      }
    });
  }

  // 初始化
  function init() {
    createStyles();
    createFloatButton();
    createChatWindow();
    updateVisibility();
    setupClickOutsideListener();  // 🔥 添加外部点击监听
    var mainFrame = document.getElementById('mainFrame');
    if (mainFrame) {
      mainFrame.addEventListener('load', function() {
        setTimeout(updateVisibility, 100);
      });
    }
    console.log('[AI Chat] 浮窗已加载 (v2.4-event-driven-state-management)');
  }

  // 暴露公共方法
  window.AIChat = {
    toggle: toggleChat,
    close: closeChat,
    resetChat: resetChat,
    sendQuick: sendQuick,
    sendMessage: sendMessage,
    skipWaiting: skipWaiting,
    stopResponse: stopResponse
  };

  // DOM 加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

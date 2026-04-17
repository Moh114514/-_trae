(function () {
  "use strict";

  if (window.__beimsChatWidgetMounted) {
    return;
  }
  window.__beimsChatWidgetMounted = true;

  function createEl(tag, className, text) {
    var el = document.createElement(tag);
    if (className) {
      el.className = className;
    }
    if (typeof text === "string") {
      el.textContent = text;
    }
    return el;
  }

  function injectStyles() {
    var style = createEl("style");
    style.textContent = ""
      + ".beims-chat-toggle{position:fixed;right:22px;bottom:22px;z-index:99999;width:56px;height:56px;border:none;border-radius:50%;cursor:pointer;background:linear-gradient(135deg,#0c6cf2,#06b6d4);color:#fff;box-shadow:0 10px 24px rgba(5,36,89,.35);font-size:24px;line-height:56px;text-align:center;}"
      + ".beims-chat-panel{position:fixed;right:22px;bottom:88px;z-index:99999;width:360px;max-width:calc(100vw - 20px);height:520px;max-height:calc(100vh - 120px);display:none;flex-direction:column;background:rgba(7,15,34,.92);backdrop-filter:blur(8px);border:1px solid rgba(135,206,250,.35);border-radius:14px;overflow:hidden;box-shadow:0 14px 38px rgba(0,0,0,.36);font-family:'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;}"
      + ".beims-chat-panel.show{display:flex;}"
      + ".beims-chat-header{height:46px;display:flex;align-items:center;justify-content:space-between;padding:0 12px;color:#e6f0ff;background:linear-gradient(90deg,rgba(12,108,242,.38),rgba(6,182,212,.24));font-size:14px;font-weight:600;}"
      + ".beims-chat-close{background:none;border:none;color:#dce9ff;font-size:18px;cursor:pointer;}"
      + ".beims-chat-log{flex:1;overflow:auto;padding:10px;background:linear-gradient(180deg,rgba(8,18,44,.85),rgba(7,15,34,.95));}"
      + ".beims-chat-item{max-width:85%;margin:8px 0;padding:9px 11px;border-radius:10px;line-height:1.45;font-size:13px;white-space:pre-wrap;word-break:break-word;}"
      + ".beims-chat-item.user{margin-left:auto;background:#1275ff;color:#fff;border-bottom-right-radius:3px;}"
      + ".beims-chat-item.assistant{margin-right:auto;background:#1f2d4f;color:#e8f0ff;border:1px solid rgba(135,206,250,.25);border-bottom-left-radius:3px;}"
      + ".beims-chat-footer{padding:10px;border-top:1px solid rgba(135,206,250,.22);background:rgba(7,15,34,.96);}"
      + ".beims-chat-row{display:flex;gap:8px;}"
      + ".beims-chat-input{flex:1;height:36px;padding:0 10px;border-radius:8px;border:1px solid rgba(135,206,250,.35);outline:none;background:#0e1a37;color:#eef5ff;font-size:13px;}"
      + ".beims-chat-send{width:68px;border:none;border-radius:8px;background:#0c6cf2;color:#fff;cursor:pointer;font-size:13px;}"
      + ".beims-chat-send[disabled]{opacity:.65;cursor:not-allowed;}";
    document.head.appendChild(style);
  }

  function mount() {
    injectStyles();

    var toggle = createEl("button", "beims-chat-toggle", "AI");
    var panel = createEl("section", "beims-chat-panel");

    var header = createEl("div", "beims-chat-header", "智能助手");
    var close = createEl("button", "beims-chat-close", "×");
    close.type = "button";
    header.appendChild(close);

    var log = createEl("div", "beims-chat-log");

    var footer = createEl("div", "beims-chat-footer");
    var row = createEl("div", "beims-chat-row");
    var input = createEl("input", "beims-chat-input");
    input.type = "text";
    input.placeholder = "问我：能耗异常、设备状态、节能建议...";
    var send = createEl("button", "beims-chat-send", "发送");
    send.type = "button";

    row.appendChild(input);
    row.appendChild(send);
    footer.appendChild(row);

    panel.appendChild(header);
    panel.appendChild(log);
    panel.appendChild(footer);

    document.body.appendChild(panel);
    document.body.appendChild(toggle);

    function append(role, text) {
      var item = createEl("div", "beims-chat-item " + role, text || "");
      log.appendChild(item);
      log.scrollTop = log.scrollHeight;
    }

    append("assistant", "你好，我是建筑能源智能助手。你可以直接问我系统运行和能耗问题。");

    function setOpen(open) {
      if (open) {
        panel.classList.add("show");
        setTimeout(function () {
          input.focus();
        }, 30);
      } else {
        panel.classList.remove("show");
      }
    }

    toggle.addEventListener("click", function () {
      setOpen(!panel.classList.contains("show"));
    });
    close.addEventListener("click", function () {
      setOpen(false);
    });

    async function sendMessage() {
      var message = (input.value || "").trim();
      if (!message || send.disabled) {
        return;
      }

      append("user", message);
      input.value = "";
      send.disabled = true;
      send.textContent = "发送中";

      try {
        var res = await fetch("/chat/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: message,
            building_id: null,
            clear_history: false
          })
        });

        if (!res.ok) {
          throw new Error("HTTP " + res.status);
        }

        var data = await res.json();
        var reply = data.response || data.reply || data.message || "助手暂时没有返回内容。";
        append("assistant", String(reply));
      } catch (err) {
        append("assistant", "请求失败，请确认后端 8001 和助手服务状态。\n" + (err && err.message ? err.message : "未知错误"));
      } finally {
        send.disabled = false;
        send.textContent = "发送";
        input.focus();
      }
    }

    send.addEventListener("click", sendMessage);
    input.addEventListener("keydown", function (evt) {
      if (evt.key === "Enter") {
        sendMessage();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();

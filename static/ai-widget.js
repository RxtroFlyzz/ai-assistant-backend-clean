(function () {
  var scriptTag = document.currentScript || (function() {
    var scripts = document.getElementsByTagName("script");
    return scripts[scripts.length - 1];
  })();
  var scriptSrc = scriptTag ? scriptTag.getAttribute("src") : "";
  var urlParams = new URLSearchParams(scriptSrc.split("?")[1] || "");
  var CLIENT_TOKEN = (typeof WIDGET_TOKEN !== "undefined" ? WIDGET_TOKEN : "") || urlParams.get("token") || "";

  var BASE_URL = "https://ai-assistant-backend-clean-iz6y.onrender.com";
  var API_URL = BASE_URL + "/chat";
  var CONTACT_URL = BASE_URL + "/contact-human";

  var style = document.createElement("style");
  style.textContent = [
    "#rpl-btn {",
    "  position:fixed; bottom:24px; right:24px;",
    "  width:58px; height:58px; border-radius:50%;",
    "  background:linear-gradient(135deg,#6366f1,#a855f7);",
    "  color:white; font-size:26px; cursor:pointer;",
    "  display:flex; align-items:center; justify-content:center;",
    "  z-index:999999; border:none;",
    "  box-shadow:0 8px 32px rgba(99,102,241,0.5);",
    "  transition:transform 0.2s,box-shadow 0.2s;",
    "  font-family:sans-serif;",
    "}",
    "#rpl-btn:hover { transform:scale(1.08); box-shadow:0 12px 40px rgba(99,102,241,0.6); }",
    "#rpl-box {",
    "  position:fixed; bottom:96px; right:24px;",
    "  width:360px; height:520px;",
    "  background:#0d1120 !important;",
    "  border:1px solid rgba(255,255,255,0.08);",
    "  border-radius:20px; overflow:hidden;",
    "  display:none; flex-direction:column;",
    "  z-index:999999;",
    "  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;",
    "  box-shadow:0 24px 64px rgba(0,0,0,0.6),0 0 0 1px rgba(99,102,241,0.15);",
    "}",
    "#rpl-header {",
    "  padding:16px 18px;",
    "  background:linear-gradient(135deg,#6366f1,#a855f7);",
    "  display:flex; align-items:center; justify-content:space-between;",
    "  flex-shrink:0;",
    "}",
    "#rpl-header-left { display:flex; align-items:center; gap:10px; }",
    "#rpl-avatar {",
    "  width:34px; height:34px; border-radius:50%;",
    "  background:rgba(255,255,255,0.2);",
    "  display:flex; align-items:center; justify-content:center; font-size:18px;",
    "}",
    "#rpl-title { font-size:14px; font-weight:600; color:white; }",
    "#rpl-status { font-size:11px; color:rgba(255,255,255,0.8); display:flex; align-items:center; gap:4px; margin-top:2px; }",
    "#rpl-dot { width:6px; height:6px; background:#4ade80; border-radius:50%; display:inline-block; }",
    "#rpl-close {",
    "  cursor:pointer; font-size:18px; color:rgba(255,255,255,0.7);",
    "  background:none; border:none; padding:0; line-height:1;",
    "  font-family:sans-serif;",
    "}",
    "#rpl-close:hover { color:white; }",
    "#rpl-msgs {",
    "  flex:1; padding:16px; overflow-y:auto;",
    "  display:flex; flex-direction:column; gap:10px;",
    "  background:#0d1120 !important;",
    "}",
    "#rpl-msgs::-webkit-scrollbar { width:3px; }",
    "#rpl-msgs::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:2px; }",
    ".rpl-msg { display:flex; flex-direction:column; max-width:82%; }",
    ".rpl-msg.user { align-self:flex-end; }",
    ".rpl-msg.bot { align-self:flex-start; }",
    ".rpl-who { font-size:10px; color:rgba(255,255,255,0.35); margin-bottom:4px; padding:0 4px; }",
    ".rpl-msg.user .rpl-who { text-align:right; }",
    ".rpl-bubble { padding:10px 14px; border-radius:14px; font-size:13.5px; line-height:1.55; }",
    ".rpl-msg.user .rpl-bubble {",
    "  background:linear-gradient(135deg,#6366f1,#a855f7);",
    "  color:white; border-bottom-right-radius:4px;",
    "}",
    ".rpl-msg.bot .rpl-bubble {",
    "  background:rgba(255,255,255,0.07) !important;",
    "  border:1px solid rgba(255,255,255,0.1);",
    "  color:#e2e8f0 !important; border-bottom-left-radius:4px;",
    "}",
    "#rpl-typing {",
    "  align-self:flex-start; display:none;",
    "  padding:10px 14px;",
    "  background:rgba(255,255,255,0.07);",
    "  border:1px solid rgba(255,255,255,0.1);",
    "  border-radius:14px; border-bottom-left-radius:4px;",
    "  gap:4px; align-items:center;",
    "}",
    "#rpl-typing span {",
    "  width:6px; height:6px; border-radius:50%;",
    "  background:rgba(255,255,255,0.5);",
    "  animation:rplDot 1.2s infinite; display:inline-block;",
    "}",
    "#rpl-typing span:nth-child(2) { animation-delay:0.2s; }",
    "#rpl-typing span:nth-child(3) { animation-delay:0.4s; }",
    "@keyframes rplDot {",
    "  0%,60%,100% { transform:translateY(0); opacity:0.4; }",
    "  30% { transform:translateY(-5px); opacity:1; }",
    "}",
    "#rpl-human-btn {",
    "  margin:0 12px 10px; padding:10px;",
    "  background:linear-gradient(135deg,#ef4444,#dc2626);",
    "  color:white; border:none; border-radius:10px;",
    "  cursor:pointer; font-size:13px; font-weight:600;",
    "  font-family:inherit; transition:opacity 0.2s,transform 0.2s;",
    "  flex-shrink:0;",
    "}",
    "#rpl-human-btn:hover { opacity:0.9; transform:translateY(-1px); }",
    "#rpl-human-btn:disabled { background:rgba(255,255,255,0.1) !important; color:rgba(255,255,255,0.4); cursor:default; transform:none; }",
    "#rpl-input-row {",
    "  display:flex; align-items:center; gap:8px;",
    "  padding:10px 12px;",
    "  border-top:1px solid rgba(255,255,255,0.07);",
    "  background:#0d1120 !important;",
    "  flex-shrink:0;",
    "}",
    "#rpl-input {",
    "  flex:1; background:rgba(255,255,255,0.07) !important;",
    "  border:1px solid rgba(255,255,255,0.1);",
    "  border-radius:10px; padding:9px 14px;",
    "  color:#e2e8f0 !important; font-size:13.5px;",
    "  font-family:inherit; outline:none;",
    "  transition:border-color 0.2s;",
    "}",
    "#rpl-input::placeholder { color:rgba(255,255,255,0.3) !important; }",
    "#rpl-input:focus { border-color:rgba(99,102,241,0.6); }",
    "#rpl-send {",
    "  width:36px; height:36px; border-radius:10px; flex-shrink:0;",
    "  background:linear-gradient(135deg,#6366f1,#a855f7);",
    "  border:none; cursor:pointer; color:white; font-size:15px;",
    "  display:flex; align-items:center; justify-content:center;",
    "  transition:opacity 0.2s,transform 0.2s; font-family:sans-serif;",
    "}",
    "#rpl-send:hover { opacity:0.85; transform:scale(1.05); }"
  ].join("\n");
  document.head.appendChild(style);

  var button = document.createElement("button");
  button.id = "rpl-btn";
  button.innerHTML = "&#128172;";

  var box = document.createElement("div");
  box.id = "rpl-box";
  box.innerHTML = [
    "<div id='rpl-header'>",
    "  <div id='rpl-header-left'>",
    "    <div id='rpl-avatar'>&#129302;</div>",
    "    <div>",
    "      <div id='rpl-title'>Assistant IA</div>",
    "      <div id='rpl-status'><span id='rpl-dot'></span> En ligne</div>",
    "    </div>",
    "  </div>",
    "  <button id='rpl-close'>&#10005;</button>",
    "</div>",
    "<div id='rpl-msgs'>",
    "  <div id='rpl-typing'><span></span><span></span><span></span></div>",
    "</div>",
    "<button id='rpl-human-btn'>&#128222; Parler a un humain</button>",
    "<div id='rpl-input-row'>",
    "  <input id='rpl-input' placeholder='Ecris un message...' autocomplete='off' />",
    "  <button id='rpl-send'>&#10148;</button>",
    "</div>"
  ].join("");

  document.body.appendChild(button);
  document.body.appendChild(box);

  var conversationId = null;
  var isOpen = false;
  var msgs = document.getElementById("rpl-msgs");
  var input = document.getElementById("rpl-input");
  var humanBtn = document.getElementById("rpl-human-btn");
  var sendBtn = document.getElementById("rpl-send");
  var typing = document.getElementById("rpl-typing");

  function getPageContent() {
    var text = "";
    var els = document.querySelectorAll("main, section, article, body");
    for (var i = 0; i < els.length; i++) {
      if (els[i] && els[i].innerText) text += els[i].innerText + "\n";
    }
    return text.slice(0, 6000);
  }

  function addMsg(role, text) {
    var wrapper = document.createElement("div");
    wrapper.className = "rpl-msg " + role;
    var who = document.createElement("div");
    who.className = "rpl-who";
    who.textContent = role === "user" ? "Vous" : "Assistant IA";
    var bubble = document.createElement("div");
    bubble.className = "rpl-bubble";
    bubble.textContent = text;
    wrapper.appendChild(who);
    wrapper.appendChild(bubble);
    msgs.insertBefore(wrapper, typing);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function showTyping() { typing.style.display = "flex"; msgs.scrollTop = msgs.scrollHeight; }
  function hideTyping() { typing.style.display = "none"; }

  function sendMessage(text) {
    if (!text.trim()) return;
    addMsg("user", text);
    showTyping();
    fetch(API_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        message: text,
        conversation_id: conversationId,
        page_content: getPageContent(),
        client_token: CLIENT_TOKEN
      })
    }).then(function(res) {
      if (!res.ok) throw new Error("Erreur");
      return res.json();
    }).then(function(data) {
      conversationId = data.conversation_id;
      hideTyping();
      addMsg("bot", data.reply);
    }).catch(function() {
      hideTyping();
      addMsg("bot", "Une erreur est survenue. Reessayez.");
    });
  }

  button.onclick = function() {
    isOpen = !isOpen;
    box.style.display = isOpen ? "flex" : "none";
    if (isOpen) input.focus();
  };

  document.getElementById("rpl-close").onclick = function() {
    isOpen = false; box.style.display = "none";
  };

  input.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && input.value.trim()) {
      var text = input.value.trim(); input.value = "";
      sendMessage(text);
    }
  });

  sendBtn.onclick = function() {
    if (input.value.trim()) {
      var text = input.value.trim(); input.value = "";
      sendMessage(text);
    }
  };

  humanBtn.onclick = function() {
    humanBtn.disabled = true;
    humanBtn.innerText = "Envoi en cours...";
    fetch(CONTACT_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ conversation_id: conversationId, client_token: CLIENT_TOKEN })
    }).then(function(res) { return res.json(); })
    .then(function(data) {
      conversationId = data.conversation_id;
      hideTyping();
      addMsg("bot", data.reply);
      humanBtn.innerText = "Demande envoyee ✓";
    }).catch(function() {
      humanBtn.disabled = false;
      humanBtn.innerText = "Parler a un humain";
    });
  };

})();
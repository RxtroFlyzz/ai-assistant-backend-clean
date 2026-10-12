(function () {
  if (window.__replaiWidgetLoaded) return;
  window.__replaiWidgetLoaded = true;

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
  var CONFIG_URL = BASE_URL + "/widget-config?token=" + encodeURIComponent(CLIENT_TOKEN);
  var STORE_KEY = "rpl_conv_" + CLIENT_TOKEN;

  // ── Styles (couleurs pilotees par des variables CSS, cf. applyTheme) ───────
  var style = document.createElement("style");
  style.textContent = [
    "#rpl-btn, #rpl-box {",
    "  --rpl-accent: linear-gradient(135deg,#6366f1,#a855f7);",
    "  --rpl-on-accent: #ffffff;",
    "  --rpl-bg: #0d1120; --rpl-text: #e2e8f0; --rpl-muted: rgba(255,255,255,0.4);",
    "  --rpl-bubble: rgba(255,255,255,0.07); --rpl-border: rgba(255,255,255,0.1);",
    "}",
    "#rpl-btn {",
    "  position:fixed; bottom:24px; right:24px;",
    "  width:58px; height:58px; border-radius:50%;",
    "  background:var(--rpl-accent); color:var(--rpl-on-accent);",
    "  font-size:26px; cursor:pointer; visibility:hidden;",
    "  display:flex; align-items:center; justify-content:center;",
    "  z-index:999999; border:none;",
    "  box-shadow:0 8px 28px rgba(0,0,0,0.28);",
    "  transition:transform 0.2s,box-shadow 0.2s;",
    "  font-family:sans-serif;",
    "}",
    "#rpl-btn:hover { transform:scale(1.08); box-shadow:0 12px 36px rgba(0,0,0,0.35); }",
    "#rpl-box {",
    "  position:fixed; bottom:96px; right:24px;",
    "  width:360px; height:520px; max-height:calc(100vh - 120px); max-width:calc(100vw - 32px);",
    "  background:var(--rpl-bg) !important;",
    "  border:1px solid var(--rpl-border);",
    "  border-radius:20px; overflow:hidden;",
    "  display:none; flex-direction:column;",
    "  z-index:999999;",
    "  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;",
    "  box-shadow:0 24px 64px rgba(0,0,0,0.35);",
    "}",
    "#rpl-header {",
    "  padding:16px 18px; background:var(--rpl-accent);",
    "  display:flex; align-items:center; justify-content:space-between; flex-shrink:0;",
    "}",
    "#rpl-header-left { display:flex; align-items:center; gap:10px; }",
    "#rpl-avatar {",
    "  width:34px; height:34px; border-radius:50%;",
    "  background:rgba(255,255,255,0.22); color:var(--rpl-on-accent);",
    "  display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:700;",
    "}",
    "#rpl-title { font-size:14px; font-weight:600; color:var(--rpl-on-accent); }",
    "#rpl-status { font-size:11px; color:var(--rpl-on-accent); opacity:0.8; display:flex; align-items:center; gap:4px; margin-top:2px; }",
    "#rpl-dot { width:6px; height:6px; background:#4ade80; border-radius:50%; display:inline-block; }",
    "#rpl-close {",
    "  cursor:pointer; font-size:18px; color:var(--rpl-on-accent); opacity:0.75;",
    "  background:none; border:none; padding:0; line-height:1; font-family:sans-serif;",
    "}",
    "#rpl-close:hover { opacity:1; }",
    "#rpl-msgs {",
    "  flex:1; padding:16px; overflow-y:auto;",
    "  display:flex; flex-direction:column; gap:10px;",
    "  background:var(--rpl-bg) !important;",
    "}",
    "#rpl-msgs::-webkit-scrollbar { width:3px; }",
    "#rpl-msgs::-webkit-scrollbar-thumb { background:var(--rpl-border); border-radius:2px; }",
    ".rpl-msg { display:flex; flex-direction:column; max-width:82%; }",
    ".rpl-msg.user { align-self:flex-end; }",
    ".rpl-msg.bot { align-self:flex-start; }",
    ".rpl-who { font-size:10px; color:var(--rpl-muted); margin-bottom:4px; padding:0 4px; }",
    ".rpl-msg.user .rpl-who { text-align:right; }",
    ".rpl-bubble { padding:10px 14px; border-radius:14px; font-size:13.5px; line-height:1.55; white-space:pre-wrap; word-break:break-word; }",
    ".rpl-msg.user .rpl-bubble { background:var(--rpl-accent); color:var(--rpl-on-accent); border-bottom-right-radius:4px; }",
    ".rpl-msg.bot .rpl-bubble {",
    "  background:var(--rpl-bubble) !important; border:1px solid var(--rpl-border);",
    "  color:var(--rpl-text) !important; border-bottom-left-radius:4px;",
    "}",
    ".rpl-link {",
    "  display:inline-block; margin:2px 0; padding:3px 10px; border-radius:999px;",
    "  background:var(--rpl-accent); color:var(--rpl-on-accent) !important;",
    "  text-decoration:none !important; font-size:12.5px; font-weight:600; white-space:nowrap;",
    "  max-width:100%; overflow:hidden; text-overflow:ellipsis; vertical-align:middle;",
    "}",
    ".rpl-link:hover { opacity:0.88; }",
    "#rpl-typing {",
    "  align-self:flex-start; display:none; padding:10px 14px;",
    "  background:var(--rpl-bubble); border:1px solid var(--rpl-border);",
    "  border-radius:14px; border-bottom-left-radius:4px; gap:4px; align-items:center;",
    "}",
    "#rpl-typing span {",
    "  width:6px; height:6px; border-radius:50%; background:var(--rpl-muted);",
    "  animation:rplDot 1.2s infinite; display:inline-block;",
    "}",
    "#rpl-typing span:nth-child(2) { animation-delay:0.2s; }",
    "#rpl-typing span:nth-child(3) { animation-delay:0.4s; }",
    "@keyframes rplDot { 0%,60%,100% { transform:translateY(0); opacity:0.4; } 30% { transform:translateY(-5px); opacity:1; } }",
    "#rpl-human-btn {",
    "  margin:0 12px 10px; padding:10px;",
    "  background:var(--rpl-bubble); color:var(--rpl-text);",
    "  border:1px solid var(--rpl-border); border-radius:10px;",
    "  cursor:pointer; font-size:13px; font-weight:600;",
    "  font-family:inherit; transition:opacity 0.2s,transform 0.2s; flex-shrink:0;",
    "}",
    "#rpl-human-btn:hover { transform:translateY(-1px); }",
    "#rpl-human-btn:disabled { opacity:0.55; cursor:default; transform:none; }",
    "#rpl-input-row {",
    "  display:flex; align-items:center; gap:8px; padding:10px 12px;",
    "  border-top:1px solid var(--rpl-border); background:var(--rpl-bg) !important; flex-shrink:0;",
    "}",
    "#rpl-input {",
    "  flex:1; background:var(--rpl-bubble) !important; border:1px solid var(--rpl-border);",
    "  border-radius:10px; padding:9px 14px; color:var(--rpl-text) !important; font-size:13.5px;",
    "  font-family:inherit; outline:none; transition:border-color 0.2s;",
    "}",
    "#rpl-input::placeholder { color:var(--rpl-muted) !important; }",
    "#rpl-input:focus { border-color:var(--rpl-muted); }",
    "#rpl-send {",
    "  width:36px; height:36px; border-radius:10px; flex-shrink:0;",
    "  background:var(--rpl-accent); border:none; cursor:pointer; color:var(--rpl-on-accent); font-size:15px;",
    "  display:flex; align-items:center; justify-content:center;",
    "  transition:opacity 0.2s,transform 0.2s; font-family:sans-serif;",
    "}",
    "#rpl-send:hover { opacity:0.85; transform:scale(1.05); }"
  ].join("\n");
  document.head.appendChild(style);

  var button = document.createElement("button");
  button.id = "rpl-btn";
  button.setAttribute("aria-label", "Ouvrir le chat");
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
    "  <button id='rpl-close' aria-label='Fermer'>&#10005;</button>",
    "</div>",
    "<div id='rpl-msgs'>",
    "  <div id='rpl-typing'><span></span><span></span><span></span></div>",
    "</div>",
    "<button id='rpl-human-btn'>&#128222; Parler à un humain</button>",
    "<div id='rpl-input-row'>",
    "  <input id='rpl-input' placeholder='Écrivez votre message…' autocomplete='off' />",
    "  <button id='rpl-send' aria-label='Envoyer'>&#10148;</button>",
    "</div>"
  ].join("");

  document.body.appendChild(button);
  document.body.appendChild(box);

  var msgs = document.getElementById("rpl-msgs");
  var input = document.getElementById("rpl-input");
  var humanBtn = document.getElementById("rpl-human-btn");
  var sendBtn = document.getElementById("rpl-send");
  var typing = document.getElementById("rpl-typing");

  var botName = "Assistant IA";
  var welcome = "";

  // ── Memoire de la conversation (suit le visiteur de page en page) ────────
  var state = { c: null, m: [], o: false, h: false };
  try {
    var saved = JSON.parse(sessionStorage.getItem(STORE_KEY) || "null");
    if (saved && typeof saved === "object") state = saved;
  } catch (e) {}
  function persist() {
    try {
      state.m = state.m.slice(-40);
      sessionStorage.setItem(STORE_KEY, JSON.stringify(state));
    } catch (e) {}
  }

  // ── Apparence ─────────────────────────────────────────────────────────────
  function luminance(hex) {
    var r = parseInt(hex.substr(1, 2), 16) / 255, g = parseInt(hex.substr(3, 2), 16) / 255, b = parseInt(hex.substr(5, 2), 16) / 255;
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }
  function setVars(vars) {
    for (var k in vars) {
      button.style.setProperty(k, vars[k]);
      box.style.setProperty(k, vars[k]);
    }
  }
  function applyTheme(cfg) {
    if (cfg.mode === "light") {
      setVars({ "--rpl-bg": "#ffffff", "--rpl-text": "#1f2937", "--rpl-muted": "rgba(0,0,0,0.45)",
                "--rpl-bubble": "#f3f4f6", "--rpl-border": "rgba(0,0,0,0.09)" });
    }
    if (cfg.color && /^#[0-9a-fA-F]{6}$/.test(cfg.color)) {
      setVars({ "--rpl-accent": cfg.color, "--rpl-on-accent": luminance(cfg.color) > 0.6 ? "#111827" : "#ffffff" });
    }
    if (cfg.assistant_name) {
      botName = cfg.assistant_name;
      document.getElementById("rpl-title").textContent = botName;
      var brand = botName.replace(/^assistant(e)?\s+(de\s+|d')?/i, "");
      if (brand) document.getElementById("rpl-avatar").textContent = brand.charAt(0).toUpperCase();
    }
    if (cfg.welcome) welcome = cfg.welcome;
  }

  // ── Liens cliquables dans les reponses ────────────────────────────────────
  var TOKEN_RE = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s<>"']+)|\*\*([^*]+)\*\*/g;
  function linkLabel(url) {
    try {
      var u = new URL(url);
      var m = u.pathname.match(/\/products\/([^\/?#]+)/);
      if (m) {
        var name = decodeURIComponent(m[1]).replace(/[-_]+/g, " ").trim();
        return "Voir : " + name.charAt(0).toUpperCase() + name.slice(1);
      }
      if (/shipping-policy/.test(u.pathname)) return "Livraison";
      if (/refund-policy/.test(u.pathname)) return "Retours";
      if (/\/collections\//.test(u.pathname)) return "Voir la collection";
      return u.hostname.replace(/^www\./, "");
    } catch (e) { return url; }
  }
  function makeLink(url, label) {
    var a = document.createElement("a");
    a.className = "rpl-link";
    a.href = url;
    a.textContent = "↗ " + label;
    var sameSite = false;
    try { sameSite = new URL(url).host === window.location.host; } catch (e) {}
    if (!sameSite) { a.target = "_blank"; a.rel = "noopener"; }
    return a;
  }
  function renderBot(bubble, text) {
    var last = 0, m;
    TOKEN_RE.lastIndex = 0;
    while ((m = TOKEN_RE.exec(text)) !== null) {
      if (m.index > last) bubble.appendChild(document.createTextNode(text.slice(last, m.index)));
      if (m[1]) {
        bubble.appendChild(makeLink(m[2], m[1]));
      } else if (m[3]) {
        var url = m[3], trail = "";
        var t = url.match(/[.,;:!?)\]»]+$/);
        if (t) { trail = t[0]; url = url.slice(0, -trail.length); }
        bubble.appendChild(makeLink(url, linkLabel(url)));
        if (trail) bubble.appendChild(document.createTextNode(trail));
      } else if (m[4]) {
        var b = document.createElement("strong");
        b.textContent = m[4];
        bubble.appendChild(b);
      }
      last = TOKEN_RE.lastIndex;
    }
    if (last < text.length) bubble.appendChild(document.createTextNode(text.slice(last)));
  }

  function addMsg(role, text, remember) {
    var wrapper = document.createElement("div");
    wrapper.className = "rpl-msg " + role;
    var who = document.createElement("div");
    who.className = "rpl-who";
    who.textContent = role === "user" ? "Vous" : botName;
    var bubble = document.createElement("div");
    bubble.className = "rpl-bubble";
    if (role === "bot") renderBot(bubble, String(text || "")); else bubble.textContent = text;
    wrapper.appendChild(who);
    wrapper.appendChild(bubble);
    msgs.insertBefore(wrapper, typing);
    msgs.scrollTop = msgs.scrollHeight;
    if (remember !== false) { state.m.push({ r: role, t: text }); persist(); }
  }

  function showTyping() { typing.style.display = "flex"; msgs.scrollTop = msgs.scrollHeight; }
  function hideTyping() { typing.style.display = "none"; }

  function setOpen(open) {
    state.o = open; persist();
    box.style.display = open ? "flex" : "none";
    if (open) {
      if (!state.m.length && welcome) addMsg("bot", welcome);
      input.focus();
    }
  }

  function getPageContent() {
    var text = "";
    var els = document.querySelectorAll("main, section, article, body");
    for (var i = 0; i < els.length; i++) {
      if (els[i] && els[i].innerText) text += els[i].innerText + "\n";
    }
    return text.slice(0, 6000);
  }

  function sendMessage(text) {
    if (!text.trim()) return;
    addMsg("user", text);
    showTyping();
    fetch(API_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        message: text,
        conversation_id: state.c,
        page_content: getPageContent(),
        page_url: window.location.href,
        client_token: CLIENT_TOKEN
      })
    }).then(function(res) {
      if (!res.ok) throw new Error("Erreur");
      return res.json();
    }).then(function(data) {
      state.c = data.conversation_id; persist();
      hideTyping();
      addMsg("bot", data.reply);
    }).catch(function() {
      hideTyping();
      addMsg("bot", "Une erreur est survenue. Réessayez.", false);
    });
  }

  button.onclick = function() { setOpen(!state.o); };
  document.getElementById("rpl-close").onclick = function() { setOpen(false); };

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

  function markHumanSent() {
    humanBtn.disabled = true;
    humanBtn.textContent = "Demande envoyée ✓";
  }
  humanBtn.onclick = function() {
    humanBtn.disabled = true;
    humanBtn.textContent = "Envoi en cours…";
    fetch(CONTACT_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ conversation_id: state.c, client_token: CLIENT_TOKEN })
    }).then(function(res) { return res.json(); })
    .then(function(data) {
      state.c = data.conversation_id; state.h = true; persist();
      hideTyping();
      addMsg("bot", data.reply);
      markHumanSent();
    }).catch(function() {
      humanBtn.disabled = false;
      humanBtn.innerHTML = "&#128222; Parler à un humain";
    });
  };

  // ── Demarrage : apparence du client, puis restauration de la conversation ─
  function start() {
    for (var i = 0; i < state.m.length; i++) addMsg(state.m[i].r, state.m[i].t, false);
    if (state.h) markHumanSent();
    button.style.visibility = "visible";
    if (state.o) setOpen(true);
  }
  var started = false;
  function startOnce() { if (!started) { started = true; start(); } }
  fetch(CONFIG_URL).then(function(r) { return r.ok ? r.json() : {}; })
    .then(function(cfg) { applyTheme(cfg || {}); startOnce(); })
    .catch(startOnce);
  setTimeout(startOnce, 2500);
})();

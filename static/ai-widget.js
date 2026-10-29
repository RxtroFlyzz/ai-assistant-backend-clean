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
  var TEASER_KEY = "rpl_teaser_" + CLIENT_TOKEN;

  // ── Langue de l'interface : suit la langue de la page (attribut lang) ─────
  var TEXTS = {
    fr: {
      title: "Assistant IA", online: "En ligne", close: "Fermer", send: "Envoyer",
      human: "Parler à un humain", placeholder: "Écrivez votre message…", you: "Vous",
      error: "Une erreur est survenue. Réessayez.", sending: "Envoi en cours…", sent: "Demande envoyée ✓",
      welcome: "Bonjour ! Comment puis-je vous aider ?",
      welcomeProduct: "Bonjour ! Une question sur « {p} » ? Je vous réponds tout de suite.",
      hello: "Bonjour ! ",
      teaser: "Une question ? Je vous réponds tout de suite.",
      teaserProduct: "Une question sur ce produit ? Je vous réponds tout de suite.",
      view: "Voir : ", shipping: "Livraison", returns: "Retours", collection: "Voir la collection",
      add: "Ajouter au panier", adding: "Ajout…", added: "Ajouté ✓", cart: "Voir le panier",
      soldOut: "Épuisé", seeProduct: "Voir", out: "épuisé", addFail: "Impossible d'ajouter, ouvrez la fiche"
    },
    en: {
      title: "AI assistant", online: "Online", close: "Close", send: "Send",
      human: "Talk to a person", placeholder: "Type your message…", you: "You",
      error: "Something went wrong. Please try again.", sending: "Sending…", sent: "Request sent ✓",
      welcome: "Hi! How can I help you?",
      welcomeProduct: "Hi! Any question about “{p}”? I can help right away.",
      hello: "Hi! ",
      teaser: "Any questions? I can help right away.",
      teaserProduct: "A question about this product? I can help right away.",
      view: "View: ", shipping: "Shipping", returns: "Returns", collection: "View collection",
      add: "Add to cart", adding: "Adding…", added: "Added ✓", cart: "View cart",
      soldOut: "Sold out", seeProduct: "View", out: "sold out", addFail: "Couldn't add it, open the product page"
    }
  };
  function pageLang() {
    var l = (document.documentElement.getAttribute("lang") || navigator.language || "fr").toLowerCase();
    return l.slice(0, 2);
  }
  function uiLang() { return pageLang() === "fr" ? "fr" : (TEXTS[pageLang()] ? pageLang() : "en"); }
  function T(key) { return TEXTS[uiLang()][key]; }

  // ── Contexte de la page ───────────────────────────────────────────────────
  function isProductPage() {
    return /\/products\//.test(location.pathname) ||
      (document.body && document.body.classList.contains("single-product"));
  }
  function productTitle() {
    var og = document.querySelector("meta[property='og:title']");
    var t = (og && og.getAttribute("content")) || "";
    if (!t) { var h1 = document.querySelector("h1"); t = h1 ? h1.textContent : ""; }
    t = t.replace(/\s+/g, " ").trim();
    return t.length > 60 ? t.slice(0, 57) + "…" : t;
  }
  function sameHost(url) {
    try { return new URL(url, location.href).host.replace(/^www\./, "") === location.host.replace(/^www\./, ""); }
    catch (e) { return false; }
  }

  // ── Styles (couleurs pilotees par des variables CSS, cf. applyTheme) ───────
  var style = document.createElement("style");
  style.textContent = [
    "#rpl-btn, #rpl-box, #rpl-teaser {",
    "  --rpl-accent: linear-gradient(135deg,#6366f1,#a855f7);",
    "  --rpl-solid: #6366f1;",
    "  --rpl-on-accent: #ffffff;",
    "  --rpl-bg: #0d1120; --rpl-text: #e2e8f0; --rpl-muted: rgba(255,255,255,0.45);",
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
    "  width:370px; height:560px; max-height:calc(100vh - 120px); max-width:calc(100vw - 32px);",
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
    ".rpl-msg { display:flex; flex-direction:column; max-width:86%; }",
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
    /* Fiches produit */
    ".rpl-cards { display:flex; flex-direction:column; gap:8px; margin-top:8px; }",
    ".rpl-card { display:flex; gap:10px; padding:10px; border-radius:14px; background:var(--rpl-bubble) !important;",
    "  border:1px solid var(--rpl-border); color:var(--rpl-text) !important; font-size:13px; }",
    ".rpl-card img { width:68px; height:68px; border-radius:10px; object-fit:cover; flex-shrink:0; background:#fff; }",
    ".rpl-card-body { flex:1; min-width:0; display:flex; flex-direction:column; gap:4px; }",
    ".rpl-card-title { font-weight:600; line-height:1.3; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }",
    ".rpl-card-price { font-weight:700; }",
    ".rpl-card-price del { font-weight:400; color:var(--rpl-muted); margin-left:6px; }",
    ".rpl-card-row { display:flex; gap:6px; align-items:center; margin-top:2px; flex-wrap:wrap; }",
    ".rpl-card select { flex:1; min-width:70px; max-width:130px; padding:6px 8px; border-radius:8px; font-size:12.5px;",
    "  background:var(--rpl-bg) !important; color:var(--rpl-text) !important; border:1px solid var(--rpl-border); font-family:inherit; }",
    ".rpl-add { padding:7px 12px; border-radius:8px; border:none; cursor:pointer; font-weight:600; font-size:12.5px;",
    "  background:var(--rpl-accent); color:var(--rpl-on-accent); font-family:inherit; white-space:nowrap; }",
    ".rpl-add:disabled { opacity:0.55; cursor:default; }",
    ".rpl-card-links { display:flex; gap:12px; font-size:12px; }",
    ".rpl-card-links a { color:var(--rpl-text) !important; opacity:0.75; text-decoration:underline !important; }",
    ".rpl-card-links a:hover { opacity:1; }",
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
    "#rpl-send:hover { opacity:0.85; transform:scale(1.05); }",
    /* Bulle d'accroche */
    "#rpl-teaser {",
    "  position:fixed; bottom:94px; right:24px; z-index:999998; max-width:min(270px, calc(100vw - 48px));",
    "  background:var(--rpl-bg); color:var(--rpl-text); border:1px solid var(--rpl-border);",
    "  border-radius:16px; border-bottom-right-radius:4px; padding:12px 30px 12px 14px;",
    "  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-size:13.5px; line-height:1.45;",
    "  box-shadow:0 14px 40px rgba(0,0,0,0.25); cursor:pointer; display:none;",
    "  animation:rplIn 0.35s ease-out;",
    "}",
    "#rpl-teaser-x { position:absolute; top:6px; right:8px; background:none; border:none; cursor:pointer;",
    "  color:var(--rpl-muted); font-size:14px; line-height:1; padding:2px; font-family:sans-serif; }",
    "@keyframes rplIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }"
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
    "      <div id='rpl-title'></div>",
    "      <div id='rpl-status'><span id='rpl-dot'></span> <span id='rpl-online'></span></div>",
    "    </div>",
    "  </div>",
    "  <button id='rpl-close'>&#10005;</button>",
    "</div>",
    "<div id='rpl-msgs'>",
    "  <div id='rpl-typing'><span></span><span></span><span></span></div>",
    "</div>",
    "<button id='rpl-human-btn'></button>",
    "<div id='rpl-input-row'>",
    "  <input id='rpl-input' autocomplete='off' />",
    "  <button id='rpl-send'>&#10148;</button>",
    "</div>"
  ].join("");

  var teaser = document.createElement("div");
  teaser.id = "rpl-teaser";
  teaser.setAttribute("role", "button");
  teaser.innerHTML = "<span id='rpl-teaser-text'></span><button id='rpl-teaser-x' aria-label='Fermer'>&#10005;</button>";

  document.body.appendChild(button);
  document.body.appendChild(box);
  document.body.appendChild(teaser);

  var msgs = document.getElementById("rpl-msgs");
  var input = document.getElementById("rpl-input");
  var humanBtn = document.getElementById("rpl-human-btn");
  var sendBtn = document.getElementById("rpl-send");
  var typing = document.getElementById("rpl-typing");

  var customName = "";   // nom choisi pour le client (ex. "Assistant Dreamer")
  var customWelcome = ""; // message d'accueil configure (redige en francais)
  var teaserSetting = ""; // "" = automatique, "off" = desactivee, sinon texte personnalise
  function botName() {
    if (!customName) return T("title");
    if (uiLang() === "en") {
      var m = customName.match(/^assistante?\s+(?:de\s+|d['’])?(.+)$/i);
      if (m) return m[1] + " assistant";
    }
    return customName;
  }
  function welcomeText() {
    if (productHook && productHookLang === uiLang()) return T("hello") + productHook;
    var p = isProductPage() ? productTitle() : "";
    if (p) return T("welcomeProduct").replace("{p}", p);
    return customWelcome && uiLang() === "fr" ? customWelcome : T("welcome");
  }

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

  // ── Suivi : ce que le chat rapporte (clics, paniers, commandes) ───────────
  function send(path, data) {
    var body = JSON.stringify(data);
    try {
      if (navigator.sendBeacon && navigator.sendBeacon(BASE_URL + path, new Blob([body], { type: "text/plain" }))) return;
    } catch (e) {}
    try { fetch(BASE_URL + path, { method: "POST", body: body, keepalive: true, headers: { "Content-Type": "text/plain" } }); } catch (e) {}
  }
  function track(type, card, variantId) {
    send("/track", { client_token: CLIENT_TOKEN, conversation_id: state.c, type: type,
                     product_id: card && card.id, variant_id: variantId || null,
                     value: card && card.price, currency: card && card.currency });
  }
  // Shopify : on marque le panier avec la conversation. Le pixel de suivi
  // retrouve cette marque dans la commande et l'attribue a l'assistant.
  function tagShopifyCart() {
    if (!state.c || state.ca === state.c || !window.Shopify || !window.fetch) return;
    fetch("/cart/update.js", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ attributes: { _replai: state.c } })
    }).then(function(r) { if (r.ok) { state.ca = state.c; persist(); } }).catch(function() {});
  }
  // WooCommerce : sur la page de confirmation, on signale la commande
  function reportWooOrder() {
    var m = location.pathname.match(/order-received\/(\d+)/);
    if (!m || !state.c) return;
    state.ord = state.ord || [];
    if (state.ord.indexOf(m[1]) >= 0) return;
    var el = document.querySelector(".woocommerce-order-overview__total .woocommerce-Price-amount, .woocommerce-order-overview__total .amount, .order_details tfoot tr:last-child .amount");
    if (!el) return;
    var raw = el.textContent.replace(/[^\d,.]/g, "");
    if (/,\d{2}$/.test(raw)) raw = raw.replace(/\./g, "").replace(",", ".");
    else raw = raw.replace(/,/g, "");
    var total = parseFloat(raw);
    if (!(total >= 0)) return;
    state.ord.push(m[1]); persist();
    send("/track-order", { client_token: CLIENT_TOKEN, conversation_id: state.c, order_id: "wc-" + m[1], total: total, currency: "EUR" });
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
      teaser.style.setProperty(k, vars[k]);
    }
  }
  function applyTheme(cfg) {
    if (cfg.mode === "light") {
      setVars({ "--rpl-bg": "#ffffff", "--rpl-text": "#1f2937", "--rpl-muted": "rgba(0,0,0,0.45)",
                "--rpl-bubble": "#f3f4f6", "--rpl-border": "rgba(0,0,0,0.09)" });
    }
    if (cfg.color && /^#[0-9a-fA-F]{6}$/.test(cfg.color)) {
      setVars({ "--rpl-accent": cfg.color, "--rpl-solid": cfg.color,
                "--rpl-on-accent": luminance(cfg.color) > 0.6 ? "#111827" : "#ffffff" });
    }
    if (cfg.assistant_name) {
      customName = cfg.assistant_name;
      var brand = customName.replace(/^assistant(e)?\s+(de\s+|d')?/i, "");
      if (brand) document.getElementById("rpl-avatar").textContent = brand.charAt(0).toUpperCase();
    }
    if (cfg.welcome) customWelcome = cfg.welcome;
    if (cfg.teaser) teaserSetting = cfg.teaser;
    applyLang();
  }

  // Textes de l'interface, remis a jour si la page change de langue
  var lastLang = null;
  function applyLang() {
    var lang = uiLang();
    document.getElementById("rpl-title").textContent = botName();
    document.getElementById("rpl-online").textContent = T("online");
    document.getElementById("rpl-close").setAttribute("aria-label", T("close"));
    sendBtn.setAttribute("aria-label", T("send"));
    input.placeholder = T("placeholder");
    if (!humanBtn.disabled) humanBtn.textContent = "☎ " + T("human");
    else if (state.h) humanBtn.textContent = T("sent");
    var whos = msgs.querySelectorAll(".rpl-who");
    for (var i = 0; i < whos.length; i++) {
      whos[i].textContent = whos[i].parentNode.classList.contains("user") ? T("you") : botName();
    }
    // Si seul l'accueil a ete affiche, on le traduit aussi
    if (lastLang && lastLang !== lang && state.m.length === 1 && state.m[0].w) {
      state.m[0].t = welcomeText(); persist();
      var b = msgs.querySelector(".rpl-msg.bot .rpl-bubble");
      if (b) { b.textContent = ""; renderBot(b, state.m[0].t); }
    }
    lastLang = lang;
  }

  // ── Liens cliquables dans les reponses ────────────────────────────────────
  var TOKEN_RE = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s<>"']+)|\*\*([^*]+)\*\*/g;
  function linkLabel(url) {
    try {
      var u = new URL(url);
      var m = u.pathname.match(/\/products?\/([^\/?#]+)/);
      if (m) {
        var name = decodeURIComponent(m[1]).replace(/[-_]+/g, " ").trim();
        return T("view") + name.charAt(0).toUpperCase() + name.slice(1);
      }
      if (/shipping-policy/.test(u.pathname)) return T("shipping");
      if (/refund-policy/.test(u.pathname)) return T("returns");
      if (/\/collections\//.test(u.pathname)) return T("collection");
      return u.hostname.replace(/^www\./, "");
    } catch (e) { return url; }
  }
  function urlKey(url) {
    try { var u = new URL(url); return u.host.replace(/^www\./, "") + u.pathname.replace(/\/$/, "").toLowerCase(); }
    catch (e) { return ""; }
  }
  function makeLink(url, label) {
    var a = document.createElement("a");
    a.className = "rpl-link";
    a.href = url;
    a.textContent = "↗ " + label;
    if (!sameHost(url)) { a.target = "_blank"; a.rel = "noopener"; }
    return a;
  }
  // cardKeys : liens des produits affiches en fiche (pas besoin de les repeter en lien)
  function renderBot(bubble, text, cardKeys) {
    var last = 0, m;
    TOKEN_RE.lastIndex = 0;
    while ((m = TOKEN_RE.exec(text)) !== null) {
      if (m.index > last) bubble.appendChild(document.createTextNode(text.slice(last, m.index)));
      if (m[1]) {
        if (cardKeys && cardKeys[urlKey(m[2])]) {
          var strong = document.createElement("strong");
          strong.textContent = m[1];
          bubble.appendChild(strong);
        } else {
          bubble.appendChild(makeLink(m[2], m[1]));
        }
      } else if (m[3]) {
        var url = m[3], trail = "";
        var t = url.match(/[.,;:!?)\]»]+$/);
        if (t) { trail = t[0]; url = url.slice(0, -trail.length); }
        if (!(cardKeys && cardKeys[urlKey(url)])) bubble.appendChild(makeLink(url, linkLabel(url)));
        if (trail) bubble.appendChild(document.createTextNode(trail));
      } else if (m[4]) {
        var b = document.createElement("strong");
        b.textContent = m[4];
        bubble.appendChild(b);
      }
      last = TOKEN_RE.lastIndex;
    }
    if (last < text.length) bubble.appendChild(document.createTextNode(text.slice(last)));
    // Nettoyage des espaces laisses par les liens retires
    if (bubble.lastChild && bubble.lastChild.nodeType === 3) {
      bubble.lastChild.textContent = bubble.lastChild.textContent.replace(/[\s:]+$/, "");
    }
  }

  // ── Fiches produit avec ajout au panier ───────────────────────────────────
  function money(v, cur) {
    try { return new Intl.NumberFormat(uiLang() === "fr" ? "fr-FR" : "en-GB", { style: "currency", currency: cur || "EUR" }).format(v); }
    catch (e) { return v.toFixed(2) + " " + (cur || "EUR"); }
  }
  function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  // Variante citee dans la reponse (ex. "Prenez un M") : on la preselectionne
  function suggestedVariant(card, text) {
    var avail = card.variants.filter(function(v) { return v.available && v.title; });
    for (var i = 0; i < avail.length; i++) {
      var re = new RegExp("(^|[\\s(«\"'])" + escapeRe(avail[i].title) + "(?=[\\s.,!?)»\"']|$)");
      if (re.test(text)) return avail[i].id;
    }
    var first = card.variants.filter(function(v) { return v.available; })[0];
    return first ? first.id : null;
  }
  function addToCart(card, variantId, btn, links) {
    var url = card.url;
    track("add_to_cart", card, variantId);
    if (card.platform === "shopify" && sameHost(url) && window.fetch) {
      btn.disabled = true; btn.textContent = T("adding");
      fetch("/cart/add.js", {
        method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ items: [{ id: Number(variantId), quantity: 1 }] })
      }).then(function(r) {
        if (!r.ok) throw new Error("cart");
        btn.textContent = T("added");
        state.ca = null; tagShopifyCart();
        if (!links.querySelector(".rpl-cart-link")) {
          var a = document.createElement("a");
          a.className = "rpl-cart-link"; a.href = "/cart"; a.textContent = T("cart");
          links.insertBefore(a, links.firstChild);
        }
        try { document.dispatchEvent(new CustomEvent("cart:refresh", { bubbles: true })); } catch (e) {}
      }).catch(function() {
        btn.disabled = false; btn.textContent = T("add");
        window.location.href = url + (url.indexOf("?") < 0 ? "?" : "&") + "variant=" + encodeURIComponent(variantId);
      });
      return;
    }
    if (card.platform === "woocommerce" && sameHost(url)) {
      window.location.href = url + (url.indexOf("?") < 0 ? "?" : "&") + "add-to-cart=" + encodeURIComponent(variantId);
      return;
    }
    // Autre site (page de demo) : on ouvre la fiche produit sur la boutique
    var dest = card.platform === "shopify" ? url + (url.indexOf("?") < 0 ? "?" : "&") + "variant=" + encodeURIComponent(variantId) : url;
    window.open(dest, "_blank", "noopener");
  }
  function buildCard(card, replyText) {
    var el = document.createElement("div");
    el.className = "rpl-card";
    if (card.image) {
      var img = document.createElement("img");
      img.src = card.image; img.alt = ""; img.loading = "lazy";
      img.onerror = function() { img.remove(); };
      el.appendChild(img);
    }
    var body = document.createElement("div");
    body.className = "rpl-card-body";
    var title = document.createElement("div");
    title.className = "rpl-card-title"; title.textContent = card.title;
    body.appendChild(title);
    if (card.price != null) {
      var price = document.createElement("div");
      price.className = "rpl-card-price";
      price.textContent = money(card.price, card.currency);
      if (card.compare_at) {
        var del = document.createElement("del");
        del.textContent = money(card.compare_at, card.currency);
        price.appendChild(del);
      }
      body.appendChild(price);
    }
    var row = document.createElement("div");
    row.className = "rpl-card-row";
    var links = document.createElement("div");
    links.className = "rpl-card-links";
    var select = null;
    var withChoice = card.variants.filter(function(v) { return v.title; });
    if (withChoice.length > 1) {
      select = document.createElement("select");
      select.setAttribute("aria-label", card.option_label || "Option");
      var pre = suggestedVariant(card, replyText || "");
      withChoice.forEach(function(v) {
        var o = document.createElement("option");
        o.value = v.id;
        o.textContent = v.title + (v.available ? "" : " (" + T("out") + ")");
        o.disabled = !v.available;
        if (v.id === pre) o.selected = true;
        select.appendChild(o);
      });
      row.appendChild(select);
    }
    var btn = document.createElement("button");
    btn.className = "rpl-add";
    btn.type = "button";
    if (!card.available) { btn.disabled = true; btn.textContent = T("soldOut"); }
    else {
      btn.textContent = T("add");
      btn.onclick = function() {
        var vid = select ? select.value : (card.variants.filter(function(v) { return v.available; })[0] || {}).id;
        if (vid) addToCart(card, vid, btn, links);
      };
    }
    row.appendChild(btn);
    body.appendChild(row);
    var see = document.createElement("a");
    see.href = card.url; see.textContent = T("seeProduct");
    if (!sameHost(card.url)) { see.target = "_blank"; see.rel = "noopener"; }
    see.onclick = function() { track("product_click", card, select ? select.value : null); };
    links.appendChild(see);
    body.appendChild(links);
    el.appendChild(body);
    return el;
  }

  function addMsg(role, text, remember, isWelcome, products) {
    var wrapper = document.createElement("div");
    wrapper.className = "rpl-msg " + role;
    var who = document.createElement("div");
    who.className = "rpl-who";
    who.textContent = role === "user" ? T("you") : botName();
    var bubble = document.createElement("div");
    bubble.className = "rpl-bubble";
    var cards = (products && products.length) ? products : null;
    if (role === "bot") {
      var keys = null;
      if (cards) { keys = {}; cards.forEach(function(p) { keys[urlKey(p.url)] = 1; }); }
      renderBot(bubble, String(text || ""), keys);
    } else {
      bubble.textContent = text;
    }
    wrapper.appendChild(who);
    if (bubble.textContent.trim()) wrapper.appendChild(bubble);
    if (cards) {
      var list = document.createElement("div");
      list.className = "rpl-cards";
      cards.forEach(function(p) { list.appendChild(buildCard(p, String(text || ""))); });
      wrapper.appendChild(list);
    }
    msgs.insertBefore(wrapper, typing);
    msgs.scrollTop = msgs.scrollHeight;
    if (remember !== false) {
      var entry = { r: role, t: text };
      if (isWelcome) entry.w = 1;
      if (cards) entry.p = cards;
      state.m.push(entry); persist();
    }
  }

  function showTyping() { typing.style.display = "flex"; msgs.scrollTop = msgs.scrollHeight; }
  function hideTyping() { typing.style.display = "none"; }

  function setOpen(open) {
    state.o = open; persist();
    box.style.display = open ? "flex" : "none";
    if (open) {
      hideTeaser(true);
      if (!state.m.length) addMsg("bot", welcomeText(), true, true);
      input.focus();
    }
  }

  // ── Bulle d'accroche ──────────────────────────────────────────────────────
  // Sur chaque nouvelle page produit (3 fois maximum par visite), une fois
  // ailleurs. Plus jamais pendant la visite si le visiteur la ferme ou ouvre le chat.
  var TEASER_MAX = 5;
  var teaserTimer = null;
  // Phrase d'accroche ecrite par l'IA pour le produit regarde (taille, dimensions...)
  var productHook = "", productHookLang = "";
  function loadProductHook() {
    if (!isProductPage() || !window.fetch) return;
    var lang = uiLang();
    fetch(BASE_URL + "/teaser?token=" + encodeURIComponent(CLIENT_TOKEN) + "&lang=" + lang +
          "&url=" + encodeURIComponent(location.origin + location.pathname))
      .then(function(r) { return r.ok ? r.json() : {}; })
      .then(function(d) { if (d && d.text) { productHook = d.text; productHookLang = lang; } })
      .catch(function() {});
  }
  function teaserState() {
    try {
      var t = JSON.parse(sessionStorage.getItem(TEASER_KEY) || "null");
      if (t && typeof t === "object") return t;
    } catch (e) {}
    return { n: 0, off: false, pages: [] };
  }
  function saveTeaser(t) { try { sessionStorage.setItem(TEASER_KEY, JSON.stringify(t)); } catch (e) {} }
  function hideTeaser(stopForVisit) {
    teaser.style.display = "none";
    if (teaserTimer) { clearTimeout(teaserTimer); teaserTimer = null; }
    if (stopForVisit) { var t = teaserState(); t.off = true; saveTeaser(t); }
  }
  function scheduleTeaser() {
    if (teaserSetting === "off" || state.o || state.m.length > 1) return;
    var t = teaserState();
    var onProduct = isProductPage();
    var page = onProduct ? location.pathname : "*";
    if (t.off || t.n >= TEASER_MAX || t.pages.indexOf(page) >= 0) return;
    teaserTimer = setTimeout(function() {
      if (state.o) return;
      var custom = teaserSetting && uiLang() === "fr" ? teaserSetting : "";
      var hook = productHookLang === uiLang() ? productHook : "";
      document.getElementById("rpl-teaser-text").textContent = custom || hook || T(onProduct ? "teaserProduct" : "teaser");
      teaser.style.display = "block";
      var cur = teaserState();
      cur.n += 1; cur.pages.push(page); saveTeaser(cur);
    }, onProduct ? 6000 : 15000);
  }
  teaser.onclick = function(e) {
    hideTeaser(true);
    if (e.target && e.target.id === "rpl-teaser-x") return;
    setOpen(true);
  };

  function getPageContent() {
    var text = "";
    var els = document.querySelectorAll("main, section, article, body");
    for (var i = 0; i < els.length; i++) {
      if (els[i] && els[i].innerText) text += els[i].innerText + "\n";
    }
    // Le texte du widget lui-meme n'apporte rien a l'assistant
    return text.replace(box.innerText || "", "").slice(0, 6000);
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
        client_token: CLIENT_TOKEN,
        page_lang: pageLang()
      })
    }).then(function(res) {
      if (!res.ok) throw new Error("Erreur");
      return res.json();
    }).then(function(data) {
      state.c = data.conversation_id; persist();
      hideTyping();
      addMsg("bot", data.reply, true, false, data.products);
      tagShopifyCart();
    }).catch(function() {
      hideTyping();
      addMsg("bot", T("error"), false);
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
    humanBtn.textContent = T("sent");
  }
  humanBtn.onclick = function() {
    humanBtn.disabled = true;
    humanBtn.textContent = T("sending");
    fetch(CONTACT_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ conversation_id: state.c, client_token: CLIENT_TOKEN, page_lang: pageLang() })
    }).then(function(res) { return res.json(); })
    .then(function(data) {
      state.c = data.conversation_id; state.h = true; persist();
      hideTyping();
      addMsg("bot", data.reply);
      markHumanSent();
    }).catch(function() {
      humanBtn.disabled = false;
      humanBtn.textContent = "☎ " + T("human");
    });
  };

  // ── Demarrage : apparence du client, puis restauration de la conversation ─
  function start() {
    applyLang();
    for (var i = 0; i < state.m.length; i++) addMsg(state.m[i].r, state.m[i].t, false, false, state.m[i].p);
    if (state.h) markHumanSent();
    button.style.visibility = "visible";
    if (state.o) setOpen(true);
    else scheduleTeaser();
    loadProductHook();
    tagShopifyCart();
    reportWooOrder();
  }
  var started = false;
  function startOnce() { if (!started) { started = true; start(); } }
  fetch(CONFIG_URL).then(function(r) { return r.ok ? r.json() : {}; })
    .then(function(cfg) { applyTheme(cfg || {}); startOnce(); })
    .catch(startOnce);
  setTimeout(startOnce, 2500);
  applyLang();
  // Le site peut changer de langue sans recharger la page (bouton FR/EN)
  try {
    new MutationObserver(applyLang).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  } catch (e) {}
})();

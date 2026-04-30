(function () {
  // Lire le token depuis l'attribut src du script tag
  var scriptTag = document.currentScript || (function() {
    var scripts = document.getElementsByTagName("script");
    return scripts[scripts.length - 1];
  })();
  var scriptSrc = scriptTag ? scriptTag.getAttribute("src") : "";
  var urlParams = new URLSearchParams(scriptSrc.split("?")[1] || "");
  var CLIENT_TOKEN = urlParams.get("token") || "";

  var BASE_URL = "https://ai-assistant-backend-clean-iz6y.onrender.com";
  var API_URL = BASE_URL + "/chat";
  var CONTACT_URL = BASE_URL + "/contact-human";

  var style = document.createElement("style");
  style.innerHTML = [
    "#ai-widget-button {",
    "  position: fixed; bottom: 20px; right: 20px;",
    "  background: #000; color: #fff; border-radius: 50%;",
    "  width: 60px; height: 60px; font-size: 28px; cursor: pointer;",
    "  display: flex; align-items: center; justify-content: center; z-index: 999999;",
    "  box-shadow: 0 4px 12px rgba(0,0,0,0.3);",
    "}",
    "#ai-widget-box {",
    "  position: fixed; bottom: 90px; right: 20px; width: 340px; height: 480px;",
    "  background: white; border: 1px solid #ddd; display: none; flex-direction: column;",
    "  z-index: 999999; font-family: Arial, sans-serif;",
    "  box-shadow: 0 4px 20px rgba(0,0,0,0.18); border-radius: 12px; overflow: hidden;",
    "}",
    "#ai-widget-header {",
    "  background: #000; color: white; padding: 12px 16px;",
    "  font-size: 14px; font-weight: bold; display: flex;",
    "  align-items: center; justify-content: space-between;",
    "}",
    "#ai-widget-close { cursor: pointer; font-size: 18px; opacity: 0.7; }",
    "#ai-widget-close:hover { opacity: 1; }",
    "#ai-messages { flex: 1; padding: 12px; overflow-y: auto; font-size: 14px; }",
    "#ai-messages div { margin-bottom: 8px; line-height: 1.5; }",
    "#ai-human-button {",
    "  margin: 6px 10px; padding: 9px;",
    "  background: #e74c3c; color: white; border: none; border-radius: 8px;",
    "  cursor: pointer; font-size: 13px; font-weight: bold; width: calc(100% - 20px);",
    "  transition: background 0.2s;",
    "}",
    "#ai-human-button:hover { background: #c0392b; }",
    "#ai-human-button:disabled { background: #95a5a6; cursor: default; }",
    "#ai-input {",
    "  border: none; border-top: 1px solid #eee; padding: 11px 14px;",
    "  width: 100%; box-sizing: border-box; font-size: 14px; outline: none;",
    "}"
  ].join("\n");
  document.head.appendChild(style);

  var button = document.createElement("div");
  button.id = "ai-widget-button";
  button.innerHTML = "&#128172;";

  var box = document.createElement("div");
  box.id = "ai-widget-box";
  box.innerHTML = [
    "<div id='ai-widget-header'>",
    "  <span>Assistant IA</span>",
    "  <span id='ai-widget-close'>&#10005;</span>",
    "</div>",
    "<div id='ai-messages'></div>",
    "<button id='ai-human-button'>&#128222; Parler a un humain</button>",
    "<input id='ai-input' placeholder='Ecris un message...' />"
  ].join("");

  document.body.appendChild(button);
  document.body.appendChild(box);

  var conversationId = null;

  function getPageContent() {
    var text = "";
    var els = document.querySelectorAll("main, section, article, body");
    for (var i = 0; i < els.length; i++) {
      if (els[i] && els[i].innerText) text += els[i].innerText + "\n";
    }
    return text.slice(0, 6000);
  }

  button.onclick = function() {
    box.style.display = box.style.display === "flex" ? "none" : "flex";
  };

  document.getElementById("ai-widget-close").onclick = function() {
    box.style.display = "none";
  };

  var input = document.getElementById("ai-input");
  var messages = document.getElementById("ai-messages");
  var humanButton = document.getElementById("ai-human-button");

  humanButton.onclick = function() {
    humanButton.disabled = true;
    humanButton.innerText = "Envoi en cours...";
    fetch(CONTACT_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        conversation_id: conversationId,
        client_token: CLIENT_TOKEN
      })
    }).then(function(res) { return res.json(); }).then(function(data) {
      conversationId = data.conversation_id;
      messages.innerHTML += "<div><b>IA :</b> " + data.reply + "</div>";
      messages.scrollTop = messages.scrollHeight;
      humanButton.innerText = "Demande envoyee";
    }).catch(function() {
      humanButton.disabled = false;
      humanButton.innerText = "Parler a un humain";
      messages.innerHTML += "<div style='color:red'><b>Erreur :</b> Impossible d'envoyer la demande</div>";
    });
  };

  input.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && input.value.trim()) {
      var userText = input.value.trim();
      input.value = "";
      messages.innerHTML += "<div><b>Moi :</b> " + userText + "</div>";
      messages.scrollTop = messages.scrollHeight;
      fetch(API_URL, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          message: userText,
          conversation_id: conversationId,
          page_content: getPageContent(),
          client_token: CLIENT_TOKEN
        })
      }).then(function(res) {
        if (!res.ok) throw new Error("Erreur serveur");
        return res.json();
      }).then(function(data) {
        conversationId = data.conversation_id;
        messages.innerHTML += "<div><b>IA :</b> " + data.reply + "</div>";
        messages.scrollTop = messages.scrollHeight;
      }).catch(function() {
        messages.innerHTML += "<div style='color:red'><b>Erreur :</b> IA indisponible</div>";
      });
    }
  });
})();
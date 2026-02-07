(function () {
  // =========================
  // CONFIG
  // =========================
  const API_URL = "https://ai-assistant-backend-clean-iz6y.onrender.com/chat";

  // =========================
  // STYLE
  // =========================
  const style = document.createElement("style");
  style.innerHTML = `
    #ai-widget-button {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #000;
      color: #fff;
      border-radius: 50%;
      width: 60px;
      height: 60px;
      font-size: 28px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999999;
    }

    #ai-widget-box {
      position: fixed;
      bottom: 90px;
      right: 20px;
      width: 320px;
      height: 420px;
      background: white;
      border: 1px solid #ddd;
      display: none;
      flex-direction: column;
      z-index: 999999;
      font-family: Arial, sans-serif;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    #ai-messages {
      flex: 1;
      padding: 10px;
      overflow-y: auto;
      font-size: 14px;
    }

    #ai-messages div {
      margin-bottom: 8px;
    }

    #ai-input {
      border: none;
      border-top: 1px solid #ddd;
      padding: 10px;
      width: 100%;
      box-sizing: border-box;
      font-size: 14px;
      outline: none;
    }
  `;
  document.head.appendChild(style);

  // =========================
  // HTML
  // =========================
  const button = document.createElement("div");
  button.id = "ai-widget-button";
  button.innerText = "💬";

  const box = document.createElement("div");
  box.id = "ai-widget-box";
  box.innerHTML = `
    <div id="ai-messages"></div>
    <input id="ai-input" placeholder="Écris un message..." />
  `;

  document.body.appendChild(button);
  document.body.appendChild(box);

  let conversationId = null;

  // =========================
  // LECTURE DU CONTENU DU SITE
  // =========================
  function getPageContent() {
    let text = "";

    document.querySelectorAll("main, section, article, body").forEach(el => {
      if (el && el.innerText) {
        text += el.innerText + "\n";
      }
    });

    return text.slice(0, 6000);
  }

  // =========================
  // DEBUG (TEMPORAIRE)
  // =========================
  console.log("🧠 Contenu du site envoyé à l'IA :");
  console.log(getPageContent());

  // =========================
  // TOGGLE OUVERTURE
  // =========================
  button.onclick = () => {
    box.style.display = box.style.display === "none" ? "flex" : "none";
  };

  // =========================
  // CHAT
  // =========================
  const input = box.querySelector("#ai-input");
  const messages = box.querySelector("#ai-messages");

  input.addEventListener("keydown", async (e) => {
    if (e.key === "Enter" && input.value.trim()) {
      const userText = input.value.trim();
      input.value = "";

      messages.innerHTML += `<div><b>Moi :</b> ${userText}</div>`;

      try {
        const res = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: userText,
            conversation_id: conversationId,
            page_content: getPageContent()
          })
        });

        if (!res.ok) {
          throw new Error("Erreur serveur");
        }

        const data = await res.json();
        conversationId = data.conversation_id;

        messages.innerHTML += `<div><b>IA :</b> ${data.reply}</div>`;
        messages.scrollTop = messages.scrollHeight;

      } catch (err) {
        messages.innerHTML += `<div style="color:red"><b>Erreur :</b> IA indisponible</div>`;
      }
    }
  });
})();

(function () {
  // === CONFIG ===
  const API_URL = "https://ai-assistant-backend-clean-iz6y.onrender.com/chat";

  // === STYLE ===
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
      z-index: 9999;
    }
    #ai-widget-box {
      position: fixed;
      bottom: 90px;
      right: 20px;
      width: 300px;
      height: 400px;
      background: white;
      border: 1px solid #ddd;
      display: none;
      flex-direction: column;
      z-index: 9999;
    }
    #ai-messages {
      flex: 1;
      padding: 10px;
      overflow-y: auto;
      font-size: 14px;
    }
    #ai-input {
      border: none;
      border-top: 1px solid #ddd;
      padding: 10px;
      width: 100%;
      box-sizing: border-box;
    }
  `;
  document.head.appendChild(style);

  // === HTML ===
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

  // === TOGGLE ===
  button.onclick = () => {
    box.style.display = box.style.display === "none" ? "flex" : "none";
  };

  // === CHAT ===
  const input = box.querySelector("#ai-input");
  const messages = box.querySelector("#ai-messages");

  input.addEventListener("keydown", async (e) => {
    if (e.key === "Enter" && input.value.trim()) {
      const userText = input.value;
      input.value = "";

      messages.innerHTML += `<div><b>Moi :</b> ${userText}</div>`;

      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userText,
          conversation_id: conversationId
        })
      });

      const data = await res.json();
      conversationId = data.conversation_id;

      messages.innerHTML += `<div><b>IA :</b> ${data.reply}</div>`;
      messages.scrollTop = messages.scrollHeight;
    }
  });
})();

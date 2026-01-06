import { useState, useRef, useEffect } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const chatEndRef = useRef(null);

  // Création auto d’une conversation au premier lancement
  useEffect(() => {
    if (conversations.length === 0) {
      createNewConversation();
    }
    // eslint-disable-next-line
  }, []);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversations, loading]);

  const createNewConversation = () => {
    const id = Date.now();
    const newConv = {
      id,
      name: `Conversation n°${conversations.length + 1}`,
      messages: []
    };
    setConversations(prev => [...prev, newConv]);
    setCurrentConversationId(id);
  };

  const deleteConversation = (id) => {
    const index = conversations.findIndex(c => c.id === id);
    const newConvs = conversations.filter(c => c.id !== id);
    setConversations(newConvs);

    if (id === currentConversationId) {
      const next = newConvs[index] || newConvs[index - 1];
      setCurrentConversationId(next ? next.id : null);
    }
  };

  const renameConversation = (id, newName) => {
    setConversations(prev =>
      prev.map(c => c.id === id ? { ...c, name: newName } : c)
    );
  };

  const sendMessage = async () => {
    if (!message.trim() || currentConversationId === null) return;

    const userMessage = { from: "user", text: message };
    setMessage("");
    setLoading(true);

    setConversations(prev =>
      prev.map(conv =>
        conv.id === currentConversationId
          ? { ...conv, messages: [...conv.messages, userMessage] }
          : conv
      )
    );

    try {
      const response = await fetch("http://127.0.0.1:3000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.text })
      });

      const data = await response.json();
      const botMessage = { from: "bot", text: data.reply || data.error };

      setConversations(prev =>
        prev.map(conv =>
          conv.id === currentConversationId
            ? { ...conv, messages: [...conv.messages, botMessage] }
            : conv
        )
      );
    } catch (err) {
      const errorMsg = { from: "bot", text: "Erreur : " + err.message };
      setConversations(prev =>
        prev.map(conv =>
          conv.id === currentConversationId
            ? { ...conv, messages: [...conv.messages, errorMsg] }
            : conv
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  const currentConversation =
    conversations.find(c => c.id === currentConversationId);

  const currentMessages = currentConversation?.messages || [];

  return (
    <div style={{
      display: "flex",
      height: "100vh",
      fontFamily: "Arial",
      backgroundColor: "#f5f5f5"
    }}>

      {/* SIDEBAR */}
      <div style={{
        width: "260px",
        backgroundColor: "#1f2937",
        color: "#fff",
        padding: "1rem",
        display: "flex",
        flexDirection: "column"
      }}>
        <h2 style={{ marginBottom: "1rem" }}>💬 Discussions</h2>

        <button
          onClick={createNewConversation}
          style={{
            padding: "0.6rem",
            borderRadius: "6px",
            border: "none",
            backgroundColor: "#3b82f6",
            color: "#fff",
            fontWeight: "bold",
            cursor: "pointer",
            marginBottom: "1rem"
          }}
        >
          + Nouvelle discussion
        </button>

        <div style={{ overflowY: "auto" }}>
          {conversations.map(conv => (
            <div
              key={conv.id}
              onClick={() => setCurrentConversationId(conv.id)}
              style={{
                padding: "0.5rem",
                borderRadius: "6px",
                cursor: "pointer",
                backgroundColor:
                  conv.id === currentConversationId ? "#374151" : "transparent",
                marginBottom: "0.3rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
              }}
            >
              {editingId === conv.id ? (
                <input
                  autoFocus
                  defaultValue={conv.name}
                  onBlur={(e) => {
                    renameConversation(conv.id, e.target.value);
                    setEditingId(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      renameConversation(conv.id, e.target.value);
                      setEditingId(null);
                    }
                  }}
                  style={{ width: "140px" }}
                />
              ) : (
                <span onDoubleClick={() => setEditingId(conv.id)}>
                  {conv.name}
                </span>
              )}

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(conv.id);
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#f87171",
                  cursor: "pointer"
                }}
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ZONE CHAT */}
      <div style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        padding: "1.5rem"
      }}>

        <h1 style={{ marginBottom: "1rem" }}>🤖 Assistant IA</h1>

        {/* MESSAGE D’ACCUEIL */}
        {currentMessages.length === 0 && !loading && (
          <div style={{
            backgroundColor: "#fff",
            padding: "2rem",
            borderRadius: "10px",
            boxShadow: "0 5px 15px rgba(0,0,0,0.1)",
            marginBottom: "1rem"
          }}>
            <h2>👋 Bienvenue</h2>
            <p>
              Je suis ton assistant IA.  
              Pose-moi une question ou démarre une discussion.
            </p>
          </div>
        )}

        {/* MESSAGES */}
        <div style={{ flex: 1, overflowY: "auto" }}>
          {currentMessages.map((msg, index) => (
            <div key={index} style={{
              display: "flex",
              justifyContent: msg.from === "user" ? "flex-end" : "flex-start",
              marginBottom: "0.8rem"
            }}>
              {msg.from === "bot" && <span style={{ marginRight: "0.4rem" }}>🤖</span>}
              <div style={{
                backgroundColor: msg.from === "user" ? "#3b82f6" : "#e5e7eb",
                color: msg.from === "user" ? "#fff" : "#000",
                padding: "0.6rem 1rem",
                borderRadius: "12px",
                maxWidth: "70%"
              }}>
                {msg.text}
              </div>
              {msg.from === "user" && <span style={{ marginLeft: "0.4rem" }}>🙂</span>}
            </div>
          ))}

          {loading && <div style={{ fontStyle: "italic" }}>🤖 L’IA réfléchit…</div>}
          <div ref={chatEndRef} />
        </div>

        {/* INPUT */}
        <div style={{ display: "flex", marginTop: "1rem" }}>
          <input
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Pose ta question ici…"
            style={{
              flex: 1,
              padding: "0.7rem",
              borderRadius: "6px",
              border: "1px solid #ccc",
              marginRight: "0.5rem"
            }}
          />
          <button
            onClick={sendMessage}
            style={{
              padding: "0.7rem 1.2rem",
              backgroundColor: "#3b82f6",
              color: "#fff",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer"
            }}
          >
            Envoyer
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;

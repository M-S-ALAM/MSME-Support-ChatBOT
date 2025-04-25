document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("user-input");
  const sendButton = document.getElementById("send-button");
  const micButton = document.getElementById("mic-button");

  sendButton.addEventListener("click", sendMessage);
  input.addEventListener("keydown", e => {
    if (e.key === "Enter") sendMessage();
  });
  micButton.addEventListener("click", toggleMic);
});

async function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message) return;

  addMessage(message, 'user');
  input.value = "";

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    const data = await res.json();
    addMessage(data.content, 'bot');
  } catch (err) {
    addMessage("⚠️ Failed to connect to server", 'bot');
  }
}

function addMessage(content, sender) {
  const box = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.textContent = content;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

// Voice recognition
let recognizing = false;
let recognition;

if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    recognizing = true;
    document.getElementById("mic-button").textContent = "🛑";
  };

  recognition.onend = () => {
    recognizing = false;
    document.getElementById("mic-button").textContent = "🎤";
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById("user-input").value = transcript;
    sendMessage();
  };
}

function toggleMic() {
  if (recognizing) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

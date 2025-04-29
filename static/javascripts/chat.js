const msgerForm = document.getElementById('msger-form');
const msgerInput = document.getElementById('textInput');
const msgerChat = document.getElementById('msger-chat');

const BOT_IMG = "https://cdn-icons-png.flaticon.com/512/4712/4712105.png";
const PERSON_IMG = "https://cdn-icons-png.flaticon.com/512/4712/4712121.png";
const BOT_NAME = "ChatBot";
const PERSON_NAME = "You";

msgerForm.addEventListener("submit", function(event) {
  event.preventDefault();

  const msgText = msgerInput.value;
  if (!msgText.trim()) return;

  appendMessage(PERSON_NAME, PERSON_IMG, "right", msgText);
  msgerInput.value = "";

  botResponse(msgText);
});

// Add mic button support and send both text and audio to backend
const micBtn = document.getElementById("mic-btn");

// Use both SpeechRecognition and webkitSpeechRecognition for compatibility
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (micBtn && SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";
  micBtn.onclick = function() {
    recognition.start();
    micBtn.classList.add("listening");
  };
  recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    msgerInput.value = transcript;
    micBtn.classList.remove("listening");
    // Optionally auto-send after speech
    msgerForm.dispatchEvent(new Event('submit'));
  };
  recognition.onerror = function() {
    micBtn.classList.remove("listening");
  };
  recognition.onend = function() {
    micBtn.classList.remove("listening");
  };
} else if (micBtn) {
  micBtn.disabled = true;
  micBtn.title = "Speech recognition not supported";
}

// Ensure logout button works even if script loads before DOM is ready
function setupLogoutBtn() {
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.onclick = function(event) {
      event.preventDefault(); // Prevent default form/button behavior
      window.location.replace("/"); // Redirect to root (login page)
    };
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", setupLogoutBtn);
} else {
  setupLogoutBtn();
}

function appendMessage(name, img, side, text) {
  const msgHTML = `
    <div class="msg ${side}-msg">
      <div class="msg-img" style="background-image: url('${img}')"></div>
      <div class="msg-bubble">
        <div class="msg-info">
          <div class="msg-info-name">${name}</div>
          <div class="msg-info-time">${formatDate(new Date())}</div>
        </div>
        <div class="msg-text">${text}</div>
      </div>
    </div>
  `;
  msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  msgerChat.scrollTop = msgerChat.scrollHeight; // Ensure always scrolls to bottom
}

// Modify botResponse to use fetch and POST to Python backend
function botResponse(rawText) {
  fetch("/get", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ msg: rawText })
  })
    .then(response => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then(data => {
      // Defensive: handle both {reply: ...} and plain string
      const reply = (typeof data === "object" && data.reply !== undefined)
        ? data.reply
        : (typeof data === "string" ? data : "No response");
      appendMessage(BOT_NAME, BOT_IMG, "left", reply);
    })
    .catch((err) => {
      appendMessage(BOT_NAME, BOT_IMG, "left", "Sorry, there was an error.");
      // Optionally log error for debugging
      // console.error(err);
    });
}

function formatDate(date) {
  const h = "0" + date.getHours();
  const m = "0" + date.getMinutes();
  return `${h.slice(-2)}:${m.slice(-2)}`;
}

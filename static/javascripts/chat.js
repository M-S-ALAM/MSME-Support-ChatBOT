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
  msgerChat.scrollTop += 500;
}

function botResponse(rawText) {
  $.get("/get", { msg: rawText }).done(function (data) {
    appendMessage(BOT_NAME, BOT_IMG, "left", data);
  });
}

function formatDate(date) {
  const h = "0" + date.getHours();
  const m = "0" + date.getMinutes();
  return `${h.slice(-2)}:${m.slice(-2)}`;
}

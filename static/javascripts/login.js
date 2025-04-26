function login() {
  const user = document.getElementById("username").value.trim();
  const pass = document.getElementById("password").value.trim();
  const validUser = "admin";
  const validPass = "msme123";

  if (user === validUser && pass === validPass) {
    localStorage.setItem("authenticated", "true");
    window.location.href = "chat.html";
  } else {
    alert("❌ Invalid username or password.");
  }
}

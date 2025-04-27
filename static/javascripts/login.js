function login(event) {
  if (event) event.preventDefault();
  const user = document.getElementById("username").value.trim();
  const pass = document.getElementById("password").value.trim();
  const validUser = "admin";
  const validPass = "msme123";

  if (user === validUser && pass === validPass) {
    localStorage.setItem("authenticated", "true");
    // Use absolute path to ensure navigation works from any route
    window.location.href = "/chat";
  } else {
    const errorDiv = document.getElementById("error-message");
    if (errorDiv) {
      errorDiv.textContent = "❌ Invalid username or password.";
    }
  }
}

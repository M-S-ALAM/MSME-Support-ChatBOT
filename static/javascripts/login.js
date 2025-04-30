function login(event) {
  if (event) event.preventDefault();
  const user = document.getElementById("username").value.trim();
  const pass = document.getElementById("password").value.trim();
  const errorDiv = document.getElementById("error-message");
  if (errorDiv) errorDiv.textContent = "";

  // Send credentials to backend for validation
  fetch("/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username: user, password: pass })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Store JWT access token in localStorage for authenticated requests
        if (data.access_token) {
          localStorage.setItem("access_token", data.access_token);
        }
        localStorage.setItem("authenticated", "true");
        window.location.href = "/chat";
      } else {
        if (errorDiv) errorDiv.textContent = "❌ " + (data.message || "Invalid username or password.");
      }
    })
    .catch(() => {
      if (errorDiv) errorDiv.textContent = "❌ An error occurred during login.";
    });

  return false; // Prevent default form submission
}

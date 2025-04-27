function signup(event) {
  if (event) event.preventDefault();
  const username = document.getElementById("signup-username").value.trim();
  const email = document.getElementById("email_id").value.trim();
  const password = document.getElementById("signup-password").value.trim();
  const errorDiv = document.getElementById("signup-error-message");

  // Clear previous error
  if (errorDiv) errorDiv.textContent = "";

  fetch("/signup", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username, email, password })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        window.location.href = "/"; // Redirect to login page on success
      } else {
        if (errorDiv) errorDiv.textContent = "❌ " + (data.message || "An error occurred during signup.");
      }
    })
    .catch(() => {
      if (errorDiv) errorDiv.textContent = "❌ An error occurred during signup.";
    });
}

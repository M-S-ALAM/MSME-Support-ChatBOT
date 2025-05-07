document.addEventListener("DOMContentLoaded", function() {
  // Password show/hide toggle for signup
  const pwdInput = document.getElementById('signup-password');
  const toggle = document.getElementById('toggleSignupPassword');
  if (toggle && pwdInput) {
    toggle.addEventListener('click', function() {
      if (pwdInput.type === "password") {
        pwdInput.type = "text";
        toggle.textContent = "🙈";
      } else {
        pwdInput.type = "password";
        toggle.textContent = "👁️";
      }
    });
  }
});

function signup(event) {
  if (event) event.preventDefault();
  const username = document.getElementById("signup-username").value.trim();
  const email = document.getElementById("email_id").value.trim();
  const mobile = document.getElementById("mobile").value.trim();
  const password = document.getElementById("signup-password").value.trim();
  const errorDiv = document.getElementById("signup-error-message");

  // Clear previous error
  if (errorDiv) errorDiv.textContent = "";

  // Basic validation
  if (!username || !email || !mobile || !password) {
    if (errorDiv) errorDiv.textContent = "❌ All fields are required.";
    return false;
  }
  if (!/^\d{10}$/.test(mobile)) {
    if (errorDiv) errorDiv.textContent = "❌ Enter a valid 10-digit mobile number.";
    return false;
  }

  fetch("/signup", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username, email, mobile, password })
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

  return false; // Prevent default form submission
}

// Password show/hide toggle
document.addEventListener("DOMContentLoaded", function() {
  const pwdInput = document.getElementById('password');
  const toggle = document.getElementById('togglePassword');
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

  // Ensure login form works if JS is loaded inline (for fallback)
  if (!window.login) {
    window.login = function(event) {
      event.preventDefault();
      const user = document.getElementById("username").value.trim();
      const pass = document.getElementById("password").value.trim();
      const errorDiv = document.getElementById("error-message");
      if (errorDiv) errorDiv.textContent = "";

      fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user, password: pass })
      })
        .then(response => {
          return response.json().then(data => {
            if (!response.ok) {
              throw new Error(data.message || "Login failed.");
            }
            return data;
          }).catch(() => {
            throw new Error("Login failed.");
          });
        })
        .then(data => {
          if (data.success) {
            // Store JWT access token in localStorage for authenticated requests
            if (data.access_token) {
              localStorage.setItem("access_token", data.access_token);
            }
            localStorage.setItem("authenticated", "true");
            // Always redirect to /chat after successful login
            window.location.replace("/chat");
          } else {
            if (errorDiv) errorDiv.textContent = "❌ " + (data.message || "Invalid username or password.");
          }
        })
        .catch((err) => {
          if (errorDiv) errorDiv.textContent = "❌ " + (err.message || "An error occurred during login.");
        });

      return false;
    };
  }
});

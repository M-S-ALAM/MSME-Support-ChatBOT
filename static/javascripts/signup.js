function signup() {
  const username = document.getElementById("signup-username").value.trim();
  const email = document.getElementById("email_id").value.trim();
  const password = document.getElementById("signup-password").value.trim();

  if (!username || !email || !password) {
    alert("❌ Please fill out all fields: Username, Email, and Password.");
    return;
  }

  const userData = {
    username: username,
    email: email,
    password: password,
  };

  fetch('http://localhost:8000/signup', {   // FastAPI runs at port 8000
    method: 'POST',
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(userData),
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert("✅ Signup successful! Now you can login.");
      window.location.href = "login.html";
    } else {
      alert(`❌ Signup failed: ${data.error}`);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('❌ An error occurred during signup.');
  });
}

let passwordInput = document.getElementById("password");
let signUpBtn = document.getElementById("signUpBtn");
let passwordHelp = document.getElementById("passwordHelp");
let hasAdminAccount = document.getElementsByClassName("hasAdminAccount");
let adminAccount = document.getElementById("adminAccount");

function checkAccount() {
  for (let i = 0; i < hasAdminAccount.length; i++) {
    if (hasAdminAccount[i].checked) {
      if (hasAdminAccount[i].value == "1") {
        adminAccount.removeAttribute("disabled");
      } else {
        adminAccount.setAttribute("disabled", "disabled");
      }
    }
  }
}

function validatePassword() {
  const password = passwordInput.value;

  let errors = [];

  // Length Validation
  if (password.length < 8) {
    errors.push("Password must be at least 8 characters long.");
  } else if (password.length > 64) {
    errors.push("Password must be at most 64 characters long.");
  }

  // Complexity Validation
  if (!/[A-Z]/.test(password)) {
    errors.push("Password must include at least one uppercase letter.");
  }
  if (!/[a-z]/.test(password)) {
    errors.push("Password must include at least one lowercase letter.");
  }
  if (!/\d/.test(password)) {
    errors.push("Password must include at least one number.");
  }
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push("Password must include at least one special character.");
  }

  if (errors.length > 0) {
    passwordHelp.innerHTML = `
        <ul>
          ${errors.map((error) => `<li>${error}</li>`).join("")}
        </ul>
      `;
    signUpBtn.disabled = true;
  } else {
    passwordHelp.innerHTML = "";
    signUpBtn.disabled = false;
  }
}

passwordInput.addEventListener("input", validatePassword);
checkAccount();

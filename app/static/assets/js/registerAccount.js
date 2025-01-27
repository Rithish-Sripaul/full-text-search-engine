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

checkAccount();

let hasAdminAccount = document.getElementById("hasAdminAccount");
let adminAccount = document.getElementById("adminAccount");

function checkAccount() {
    if (hasAdminAccount.value == "1") {
        adminAccount.removeAttribute("disabled");
    } else {
        adminAccount.setAttribute("disabled", "disabled");
    }
}

checkAccount();

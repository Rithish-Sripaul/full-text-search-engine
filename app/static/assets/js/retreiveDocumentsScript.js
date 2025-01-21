// RESET SEARCH FORM
let documentTitle = document.getElementById("document_title");
let documentNumber = document.getElementById("document_number");
let author = document.getElementById("author");
let year = document.getElementById("year");
let division = document.getElementById("division");
let reportType = document.getElementById("reportType");

document.getElementById("formReset").addEventListener("click", (e) => {
  documentTitle.value = "";
  documentNumber.value = "";
  author.value = "";
  year.value = "";
  division.selectedIndex = 0;
  reportType.selectedIndex = 0;
  displaySubReportType();
});

// RESET Sort Form
// let sortDocumentTitle = document.getElementById("sortDocumentTitle");
// let sortAuthor = document.getElementById("sortAuthor");
// let sortYear = document.getElementById("sortYear");
// let sortUploadedAt = document.getElementById("sortUploadedAt");

// document.getElementById("sortFormResetBtn").addEventListener("click", () => {
//   sortDocumentTitle.selectedIndex = 0;
//   sortAuthor.selectedIndex = 0;
//   sortYear.selectedIndex = 0;
//   sortUploadedAt.selectedIndex = 0;
// });

// Combine Search and Sort Forms
let submitBtnArray = document.querySelectorAll(".submit-btn");

submitBtnArray.forEach((b) => {
  b.addEventListener("click", () => {
    const searchForm = new FormData(document.getElementById("searchForm"));
    const sortForm = new FormData(document.getElementById("sortForm"));

    const params = new URLSearchParams();
    searchForm.forEach((value, key) => params.append(key, value));
    sortForm.forEach((value, key) => params.append(key, value));

    // Redirect with combined query parameters
    window.location.href = `/search/?${params.toString()}`;
  });
});

// SHOW/HIDE Sort Collapse
function showHideCollapse(order) {
  console.log(order);
  document.querySelector(".collapseControl").classList.add(order);
  return true;
}

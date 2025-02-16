let fileNameCard = document.getElementById("file-name-card");
let uploadedFile = document.getElementById("uploadedFile");

async function upload() {
  let isValid = await validateFile();
  if (isValid) {
    fileNameCard.innerHTML = `Uploaded File: <br> ${uploadedFile.value
      .split("\\")
      .pop()}`;
  } else {
    uploadedFile.value = "";
  }
}

// Author and email input creation
let addAuthorBtn = document.getElementById("addAuthorBtn");
let authorCount = 2;

addAuthorBtn.addEventListener("click", addAuthor);

function addAuthor(e) {
  const authorContainer = document.getElementById("author-section");
  const newAuthor = `
            <div class="newAuthorSection mb-3">
              <div class="row">
              <div class="col-md-6" >
                <div>
                  <label for="author_name">Author ${authorCount}</label>
                  <input name="author_name[]" class="form-control" id="first_name" type="text"
                      placeholder="Enter Author name" required>
                </div>
              </div>
              <div class="col-md-6">
                  <div class="form-group">
                      <div class="d-flex flex-row justify-content-between mb-0">
                        <label for="email">Author Email ${authorCount}</label>
                        <button type="button" class="btn-close" onclick='deleteAuthorSection(this)'></button>
                      </div>
                      <input name="email[]" class="form-control" id="email" type="email" placeholder="Email">
                  </div>
              </div>
              </div>
            </div>`;
  authorCount++;
  authorContainer.insertAdjacentHTML("beforeend", newAuthor);
}

// Modal for spinner
let uploadForm = document.getElementById("uploadForm");
var ocrModal = new bootstrap.Modal(document.getElementById("exampleModal"), {
  keyboard: false,
});

uploadForm.addEventListener("submit", () => {
  ocrModal.toggle();
});

// Reset the form
function resetForm() {
  let subReportTypeContainer = document.getElementById(
    "subReportTypeContainer"
  );
  subReportTypeContainer.remove();
}

// Deleting Author Section
function deleteAuthorSection(btn) {
  let parent = btn.closest(".newAuthorSection");
  parent.remove();
  authorCount--;
}

// Removing required from title, author and year when generateTitle checkbox is checked
let generateTitle = document.getElementById("generateTitle");
let title = document.getElementById("title");
let author = document.getElementById("author");
let year = document.getElementById("document_year");

generateTitle.addEventListener("change", () => {
  if (generateTitle.checked) {
    title.removeAttribute("required");
    author.removeAttribute("required");
    year.removeAttribute("required");
  } else {
    title.setAttribute("required", "");
    author.setAttribute("required", "");
    year.setAttribute("required", "");
  }
});

// Checking file extension
let fileInput = document.getElementById("uploadedFile");
let allowedExtensions = [".pdf"];

function validateFile() {
  // Call a modal if the file is not in allowedExtensions
  if (!allowedExtensions.includes(fileInput.value.slice(-4))) {
    let modal = new bootstrap.Modal(
      document.getElementById("validateFileExtension")
    );
    let validateBtn = document.getElementById("validateFileExtensionBtn");
    let closeBtn = document.getElementById("validateCloseBtn");
    modal.show();

    return new Promise((resolve) => {
      validateBtn.addEventListener("click", () => {
        modal.hide();
        resolve(true);
      });
      closeBtn.addEventListener("click", () => {
        modal.hide();
        resolve(false);
      });
    });
  }
  return Promise.resolve(true);
}

// Avoid AI

function avoidAICheck() {
  let avoidAICheck = document.getElementById("avoidAI").checked;
  let generateTitle = document.getElementById("generateTitle");
  if (avoidAICheck) {
    generateTitle.checked = false;
    generateTitle.disabled = true;
  } else {
    generateTitle.disabled = false;
  }
}

avoidAICheck();

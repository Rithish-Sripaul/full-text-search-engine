let fileNameCard = document.getElementById("file-name-card");
let uploadedFile = document.getElementById("uploadedFile");

function upload() {
  console.log(uploadedFile);
  fileNameCard.innerHTML = `Uploaded File: <br> ${uploadedFile.value
    .split("\\")
    .pop()}`;
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

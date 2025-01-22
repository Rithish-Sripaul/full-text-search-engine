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
  const newAuthor = `<div class="col-md-6 mb-3">
                            <div>
                                <label for="author_name">Author ${authorCount}</label>
                                <input name="author_name[]" class="form-control" id="first_name" type="text"
                                    placeholder="Enter Author name" required>
                            </div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <div class="form-group">
                                <label for="email">Author Email ${authorCount}</label>
                                <input name="email[]" class="form-control" id="email" type="email" placeholder="Email">
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

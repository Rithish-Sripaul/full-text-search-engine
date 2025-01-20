# ----------------- IMPORTS -----------------

import os
import datetime
from datetime import datetime as dt
import math
import requests
import io

from flask import render_template, send_file, redirect, request, url_for, Blueprint, flash, session, make_response
from flask_login import (
    current_user,
    login_user,
    logout_user
)

import pymongo
from database import get_db
from authentication import login_required
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

import gridfs
from gridfs import GridFS

from pypdf import PdfReader
import ocrmypdf

bp = Blueprint("documents", __name__, url_prefix='')

# ----------------- SEARCH -----------------

@bp.route("/search/", methods=["GET", "POST"])
@login_required
def search():
    backPageUrl = "documents.search"

    db = get_db()
    document_collection = db["documents"]

    # Report types
    report_type_collection = db["reportType"]
    reportTypeList = list(report_type_collection.find())

    # Division types
    divisions_collection = db["divisions"]
    divisionList = list(divisions_collection.find())
    
    list_number_of_documents_per_page = [5, 10, 20, 40]
    number_of_pages = 1
    number_of_documents_per_page = 5
    current_page = 0

    yearList = document_collection.distinct("year")

    # CONSTRUCTING THE METADATA
    searchMetaData = {}

    refreshDocumentTitle = ""
    refreshDocumentNumber = ""
    refreshAuthorName = ""
    refreshDocumentYear = ""
    refreshDivision = ""
    refreshReportType = ""
    
    # document_title
    if request.args.get("document_title", default = "") != "":
        searchMetaData["$text"] = {"$search": request.args.get("document_title", default="")}
        refreshDocumentTitle = request.args.get("document_title")
    else:
        searchMetaData.pop("$text", None)
    # document_number
    if request.args.get("document_number", default = "") != "":
        searchMetaData["document_number"] = request.args.get("document_number")
        refreshDocumentNumber = request.args.get("document_number")
    else:
        searchMetaData.pop("document_number", None)
    # author_name
    if request.args.get("author", default = "") != "":
        searchMetaData["author"] = request.args.get("author")
        refreshAuthorName = request.args.get("author")
    else:
        searchMetaData.pop("author", None)
    # document_year
    if request.args.get("year", default = "") != "":
        searchMetaData["year"] = request.args.get("year")
        refreshDocumentYear = request.args.get("year")
    else:
        searchMetaData.pop("year", None)
    # division
    if request.args.get("division", default = "") != "":
        searchMetaData["division"] = request.args.get("division")
        refreshDivision = request.args.get("division")
    else:
        searchMetaData.pop("division", None)
    # report type
    if request.args.get("reportType", default = "") != "":
        searchMetaData["reportType"] = request.args.get("reportType")
        refreshReportType = request.args.get("reportType")
    else:
        searchMetaData.pop("reportType", None)

    # CONSTRUCTING SORTING META DATA
    sortMetaData = {}
    refreshSortData = {}

    if request.args.get("sortBy", default="") == "uploaded_at_asc":
        sortMetaData["uploaded_at"] = 1
    elif request.args.get("sortBy", default="") == "uploaded_at_desc":
        sortMetaData["uploaded_at"] = -1
    elif request.args.get("sortBy", default="") == "title_asc":
        sortMetaData["title"] = 1
    elif request.args.get("sortBy", default="") == "title_desc":
        sortMetaData["title"] = -1
    elif request.args.get("sortBy", default="") == "author_asc":
        sortMetaData["author"] = 1
    elif request.args.get("sortBy", default="") == "author_desc":
        sortMetaData["author"] = -1
    elif request.args.get("sortBy", default="") == "year_asc":
        sortMetaData["year"] = 1
    elif request.args.get("sortBy", default="") == "year_desc":
        sortMetaData["year"] = -1



    # document_title
    # if request.args.get("sortDocumentTitle", default="") == "asc":
    #     sortMetaData["document_title"] = 1
    #     refreshSortData["document_title"] = request.args.get("sortDocumentTitle")
    # elif request.args.get("sortDocumentTitle", default="") == "desc":
    #     sortMetaData["document_title"] = -1
    #     refreshSortData["document_title"] = request.args.get("sortDocumentTitle")
    # else:
    #     sortMetaData.pop("document_title", None)
    #     refreshSortData.pop("document_title", None)
        
    # # author
    # if request.args.get("sortAuthor", default="") == "asc":
    #     sortMetaData["author"] = 1
    #     refreshSortData["author"] = request.args.get("sortAuthor")
    # elif request.args.get("sortAuthor", default="") == "desc":
    #     sortMetaData["author"] = -1
    #     refreshSortData["author"] = request.args.get("sortAuthor")
    # else:
    #     sortMetaData.pop("author", None)
    #     refreshSortData.pop("author", None)
    
    # # year
    # if request.args.get("sortYear", default="") == "asc":
    #     sortMetaData["year"] = 1
    #     refreshSortData["year"] = request.args.get("sortYear")
    # elif request.args.get("sortYear", default="") == "desc":
    #     sortMetaData["year"] = -1
    #     refreshSortData["year"] = request.args.get("sortYear")
    # else:
    #     sortMetaData.pop("year", None)
    #     refreshSortData.pop("year", None)
    
    # # uploaded_at
    # if request.args.get("sortUploadedAt", default="") == "asc":
    #     sortMetaData["uploaded_at"] = 1
    #     refreshSortData["uploaded_at"] = request.args.get("sortUploadedAt")
    # elif request.args.get("sortUploadedAt", default="") == "desc":
    #     sortMetaData["uploaded_at"] = -1
    #     refreshSortData["uploaded_at"] = request.args.get("sortUploadedAt")
    # else:
    #     sortMetaData.pop("uploaded_at", None)
    #     refreshSortData.pop("uploaded_at", None)
    
    if sortMetaData == {}:
        sortMetaData["uploaded_at"] = -1

    print(sortMetaData)
    print(refreshSortData)
    print(searchMetaData)
    # OPEN/CLOSE the SORT COLLAPSIBLE
    sortCollapse = ""
    if refreshSortData == {}:
        sortCollapse = ""
    else:
        sortCollapse = "show"
    print(sortCollapse)
    # DEFAULT VIEW: Recently uploaded documents
    search_results = list(document_collection.find(searchMetaData))

    totalNumberOfDocuments = len(search_results)
    
    # Setting up pagination details
    if request.args.get("docppag") is not None:
        session["number_of_documents_per_page"] = request.args.get("docppag", type=int)
    number_of_documents_per_page = session["number_of_documents_per_page"]
    current_page = request.args.get('page', default=0, type=int)
    number_of_pages = math.ceil(totalNumberOfDocuments / number_of_documents_per_page)

    searchResultsTrimmed = list(document_collection.find(
        searchMetaData,
        skip = number_of_documents_per_page * current_page,
        limit = number_of_documents_per_page,
        sort = sortMetaData
    ))

    searchResultsTrimmedLen = len(searchResultsTrimmed)
    print(refreshSortData.get("document_title", ""))
    return render_template(
        "search/retreiveDocuments.html",
        backPageUrl = backPageUrl,
        yearList = sorted(yearList),
        searchResults = searchResultsTrimmed, 
        lenSearchResults = searchResultsTrimmedLen,
        reportTypeList = reportTypeList,
        divisionList = divisionList,
        number_of_pages = number_of_pages,
        list_number_of_documents_per_page = list_number_of_documents_per_page,
        number_of_documents_per_page = number_of_documents_per_page,
        current_page = current_page,
        refreshDocumentTitle = refreshDocumentTitle,
        refreshDocumentNumber = refreshDocumentNumber,
        refreshAuthorName = refreshAuthorName,
        refreshDocumentYear = refreshDocumentYear,
        refreshDivision = refreshDivision,
        refreshReportType = refreshReportType,
        refreshSortDocumentTitle = refreshSortData.get("document_title", ""),
        refreshSortAuthor = refreshSortData.get("author", ""),
        refreshSortYear = refreshSortData.get("year", ""),
        refreshSortDivision = refreshSortData.get("division", ""),
        refreshSortUploadedAt = refreshSortData.get("uploaded_at", ""),
        sortCollapse = sortCollapse
    )


# ----------------- UPLOAD -----------------

@bp.route("/upload/", methods=["GET", "POST"])
@login_required
def upload():
    backPageUrl = "documents.search"

    db = get_db()
    document_collection = db["documents"]
    file_collection = db["fs.files"]
    
    # Parent Report types
    report_type_collection = db["reportType"]
    parentReportTypeList = list(
        report_type_collection.find(
            {
                "isSubReportType": False
            }
        )
    )
    parentReportTypeListLen = len(parentReportTypeList)

    # Sub Report types
    subReportTypeList = list(
        report_type_collection.find(
            {
                "isSubReportType": True
            }
        )
    )

    # Division types
    divisions_collection = db["divisions"]
    divisionList = list(divisions_collection.find())


    totalNumberOfDocuments = document_collection.count_documents({
        "uploadedBy" : ObjectId(session["user_id"])
    })

    # Setting up Pagination Details
    list_number_of_documents_per_page = [5, 10, 20, 40]
    if request.args.get('docppag') is not None:
        session["number_of_documents_per_page"] = request.args.get("docppag", type=int)
    number_of_documents_per_page = session["number_of_documents_per_page"]
        
    current_page = request.args.get('page', default=0, type=int)
    number_of_pages = math.ceil(totalNumberOfDocuments / number_of_documents_per_page)
    uploadedDocuments = list(
        document_collection
        .find({"uploadedBy" : ObjectId(session["user_id"])})
        .sort({"uploaded_at": -1})
        .skip(number_of_documents_per_page * current_page)
        .limit(number_of_documents_per_page)
    )
    

    if request.method == "POST":
        db = get_db()
        document_collection = db["documents"]
        fs = gridfs.GridFS(db)

        title = request.form["document_title"]
        document_number = request.form["document_number"]
        year = request.form["document_year"]
        division = request.form["division"]
        author_list = request.form.getlist("author_name[]")
        email_list = request.form.getlist("email[]")
        reportType = request.form["report_type"]
        file_data = request.files["documents"]
        ocrValue = request.form.getlist("ocrValue")
        print(ocrValue)
        
        author = author_list[0]
        email = email_list[0]

        checkFileExists = list(file_collection.find({"filename": file_data.filename}))
        print(checkFileExists)
        checkFileExists = True if len(checkFileExists) != 0 else False
        print(checkFileExists)

        if checkFileExists:
            flash("File already exists. Please choose another file.")
            redirect(url_for("documents.upload"))
        else:
            content = []
            if "true" in ocrValue:
                file_data.save(os.path.join("converted_pdf/", "input_pdf_test.pdf"))
                ocrmypdf.ocr("converted_pdf/input_pdf_test.pdf", "converted_pdf/ouptut_pdf.pdf", deskew=True, force_ocr=True)
                converted_file_data = open("converted_pdf/ouptut_pdf.pdf", 'rb')
                file_id = fs.put(converted_file_data, filename=file_data.filename)
                reader = PdfReader(converted_file_data)
            else:
                file_id = fs.put(file_data, filename=file_data.filename)
                reader = PdfReader(file_data)

            for page in reader.pages:
                content.append(page.extract_text())
            content = str(content)
            content = content.replace("\\n", " ")
            
            document_metadata = {
                "uploadedBy": ObjectId(session["user_id"]),
                "title": title,
                "year": year,
                "document_number": document_number,
                "division": division,
                "author": author,
                "reportType": reportType,
                "email": email,
                "author_list": author_list,
                "email_list": email_list,
                "file_id": file_id,
                "isApproved": 0,
                "approvedBy": None,
                "approved_at": None,
                "content": str(content),
                "uploaded_at": datetime.datetime.now()
            }



            try:
                document_collection.insert_one(document_metadata)
                divisions_collection.update_one(
                    {
                        "name": str(division)
                    },
                    {
                        "$inc": {
                            "document_count": 1
                        }
                    }
                )
                divisions_collection.update_one(
                    {
                        "name": division
                    },
                    {
                        "$inc": {
                            "reportTypes.$[type].document_count": 1
                        }
                    },
                    array_filters = [
                            {
                                "type.name": reportType
                            }
                        ]
                )
                print("Successfully uploaded the document")
            except:
                print("some error")

            return redirect(url_for("documents.upload"))

    return render_template(
        "search/uploadDocuments.html",
        backPageUrl = backPageUrl,
        uploadedDocuments = uploadedDocuments,
        uploadedDocumentsLen = len(uploadedDocuments),
        totalNumberOfDocuments = totalNumberOfDocuments,
        number_of_pages = number_of_pages,
        list_number_of_documents_per_page = list_number_of_documents_per_page,
        number_of_documents_per_page = number_of_documents_per_page,
        current_page = current_page,
        parentReportTypeList = parentReportTypeList,
        divisionList = divisionList,
        current_year = dt.now().year
    )
    
@bp.route("/details/")
@bp.route("/details/<id>")
@login_required

def details(id=None):
    backPageUrl = "documents.search"
    db = get_db()
    document_collection = db["documents"]
    searchHistory_collection = db["searchHistory"]

    searchResults = document_collection.find_one({"_id": ObjectId(id)})
    
    
    if request.args.get("fromSearchPage", type=bool, default=False) == True:
        print("details from search apge")
        searchHistoryMetaData = {
            "user_id": ObjectId(session["user_id"]),
            "document_id": ObjectId(id),
            "timestamp": datetime.datetime.now()
        }
        searchHistory_collection.insert_one(searchHistoryMetaData)
    return render_template(
        "search/documentDetails.html", 
        backPageUrl = backPageUrl,
        searchResults = searchResults,
        numOfAuthors = len(searchResults["author_list"]),
        isAdmin = session["isAdmin"]
    )

@bp.route("/download/<id>")
@login_required

def download(id = None):
    db = get_db()
    grid_fs = GridFS(db)
    file_data = grid_fs.find_one({'_id': ObjectId(id)})
    # Read the file content
    file_stream = io.BytesIO(file_data.read())
    # Send the file as a response
    return send_file(
        file_stream,
        as_attachment=True,
        download_name=file_data.filename,
        mimetype=file_data.content_type
    )

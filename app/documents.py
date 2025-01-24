# ----------------- IMPORTS -----------------

import os
import datetime
from datetime import datetime as dt
import math
import requests
import io

from flask import render_template, send_file, redirect, request, url_for, Blueprint, flash, session, make_response, jsonify, Response
from flask_login import (
    current_user,
    login_user,
    logout_user
)

import pymongo
from database import get_db
from authentication import login_required
from werkzeug.security import generate_password_hash, check_password_hash
from bson import json_util
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
    backPageUrl = "dashboard.home"

    db = get_db()
    document_collection = db["documents"]

    # Report types
    report_type_collection = db["reportType"]
    reportTypeList = list(report_type_collection.find())

    # Parent Report Types
    parentReportTypeList = list(
        report_type_collection.find(
            {
                "isSubReportType": False
            }
        )
    )

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
    refreshSubReportType = ""
    
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
        searchMetaData["author_list"] = request.args.get("author")
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
        searchMetaData["reportType"] = report_type_collection.find_one({"_id": ObjectId(request.args.get("reportType"))})["name"]
        refreshReportType = report_type_collection.find_one({"_id": ObjectId(request.args.get("reportType"))})["name"]
    else:
        searchMetaData.pop("reportType", None)
    # sub report type
    if request.args.get("subReportType", default = "") != "":
        searchMetaData["subReportType"] = report_type_collection.find_one({"_id": ObjectId(request.args.get("subReportType"))})["name"]
        refreshSubReportType = report_type_collection.find_one({"_id": ObjectId(request.args.get("subReportType"))})["name"]
    else:
        searchMetaData.pop("subReportType", None)
    
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
    
    if sortMetaData == {}:
        sortMetaData["uploaded_at"] = -1

    print(sortMetaData)
    print(refreshSortData)
    print(searchMetaData)
    print(refreshReportType)
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
        parentReportTypeList = parentReportTypeList,
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
        refreshSubReportType = refreshSubReportType,
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

    # Toast Message
    try:
        if session["toastMessage"] != "":
            flash(session["toastMessage"], session["toastMessageCategory"])
            print("Toast Message sent")
            session["toastMessage"] = ""
            session["toastMessageCategory"] = ""
    except:
        pass

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

        reportTypeId = ObjectId(request.form["report_type"])
        if request.form.get("sub_report_type", False) != False:
            subReportTypeId = ObjectId(request.form["sub_report_type"])
        else:
            subReportTypeId = None

        file_data = request.files["documents"]
        ocrValue = request.form.getlist("ocrValue")
        
        reportType = report_type_collection.find_one({"_id": reportTypeId})["name"]
        if subReportTypeId != None:
            subReportType = report_type_collection.find_one({"_id": subReportTypeId})["name"]
        else:
            subReportType = None
        
        author = author_list[0]
        email = email_list[0]

        checkFileExists = list(file_collection.find({"filename": file_data.filename}))
        print(checkFileExists)
        checkFileExists = True if len(checkFileExists) != 0 else False
        print(checkFileExists)

        if checkFileExists:
            # flash("File already exists. Please choose another file.", "Alert")
            session["toastMessage"] = "File already exists. Please choose another file."
            session["toastMessageCategory"] = "Alert"
            return redirect(url_for("documents.upload"))
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
                "year": int(year),
                "document_number": document_number,
                "division": division,
                "author": author,
                "reportType": reportType,
                "subReportType": subReportType,
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
                            "documentCount": 1
                        }
                    }
                )

                report_type_collection.update_one(
                    {
                        "name": str(reportType)
                    },
                    {
                        "$inc": {
                            "documentCount": 1
                        }
                    }
                )
                if subReportType != None:
                    report_type_collection.update_one(
                        {
                            "name": str(subReportType)
                        },
                        {
                            "$inc": {
                                "documentCount": 1
                            }
                        }
                    )
                print("Successfully uploaded the document")
                session["toastMessage"] = "Document uploaded successfully"
                session["toastMessageCategory"] = "Success"
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


# ----------------- EDIT DOCUMENTS -----------------
@bp.route("/details/editDocument/", methods=["GET", "POST"])
@bp.route("/details/editDocument/<id>", methods=["GET", "POST"])
@login_required
def editDocument(id = None):
    backPageUrl = "documents.search"
    db = get_db()
    document_collection = db["documents"]

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

    # Current Document Details
    currentDocument = document_collection.find_one({"_id": ObjectId(id)})
    authorListLen = len(currentDocument["author_list"])
    
    if request.method == "POST":
        db = get_db()
        document_collection = db["documents"]
        fs = gridfs.GridFS(db)

        title = request.form["new_title"]
        document_number = request.form["new_document_number"]
        year = request.form["new_document_year"]
        author_list = request.form.getlist("new_author_name[]")
        email_list = request.form.getlist("new_email[]")
        
        reportTypeId = ObjectId(request.form["new_report_type"])
        if request.form.get("new_sub_report_type", False) != False:
            subReportTypeId = ObjectId(request.form["new_sub_report_type"])
        else:
            subReportTypeId = None

        reportType = report_type_collection.find_one({"_id": reportTypeId})["name"]
        if subReportTypeId != None:
            subReportType = report_type_collection.find_one({"_id": subReportTypeId})["name"]
        else:
            subReportType = None

        author = author_list[0]
        email = email_list[0]

        if reportType != currentDocument["reportType"]:
            report_type_collection.update_one(
                {
                    "name": currentDocument["reportType"]
                },
                {
                    "$inc": {
                        "documentCount": -1
                    }
                }
            )
            report_type_collection.update_one(
                {
                    "name": reportType
                },
                {
                    "$inc": {
                        "documentCount": 1
                    }
                }
            )
        if subReportType != None:
            report_type_collection.update_one(
                {
                    "name": currentDocument["subReportType"]
                },
                {
                    "$inc": {
                        "documentCount": -1
                    }
                }
            )

            report_type_collection.update_one(
                {
                    "name": subReportType
                },
                {
                    "$inc": {
                        "documentCount": 1
                    }
                }
            )

        document_collection.update_one(
            {
                "_id": ObjectId(id)
            },
            {
                "$set": {
                    "title": title,
                    "year": int(year),
                    "document_number": document_number,
                    "author": author,
                    "reportType": reportType,
                    "subReportType": subReportType,
                    "email": email,
                    "author_list": author_list,
                    "email_list": email_list,
                    "editedAt": datetime.datetime.now()
                }
            }
        )

        # Toast
        session["toastMessage"] = "Document edited successfully"
        session["toastMessageCategory"] = "Success"
        return redirect(url_for("documents.details", id=id))

    return render_template(
        "edit/editDocuments.html",
        backPageUrl = backPageUrl,
        parentReportTypeList = parentReportTypeList,
        subReportTypeList = subReportTypeList,
        divisionList = divisionList,
        current_year = dt.now().year,
        currentDocument = currentDocument,
        authorListLen = authorListLen
    )

# ----------------- DELETE DOCUMENTS -----------------
@bp.route("/details/deleteDocument/")
@bp.route("/details/deleteDocument/<id>", methods=["GET", "POST"])
@login_required
def deleteDocument(id = None):
    db = get_db()
    document_collection = db["documents"]
    report_collection = db["reportType"]
    divisions_collection = db["divisions"]

    divisions_collection.update_one(
        {
            "name": document_collection.find_one({"_id": ObjectId(id)})["division"]
        },
        {
            "$inc": {
                "documentCount": -1
            }
        }
    )
    report_collection.update_one(
        {
            "name": document_collection.find_one({"_id": ObjectId(id)})["reportType"]
        }, 
        {
            "$inc": {
                "documentCount": -1
            }
        }
    )
    report_collection.update_one(
        {
            "name": document_collection.find_one({"_id": ObjectId(id)})["subReportType"]
        }, 
        {
            "$inc": {
                "documentCount": -1
            }
        }
    )
    document_collection.delete_one({"_id": ObjectId(id)})
    print("Deleted document confirmation")
    return redirect(url_for("documents.search"))


# ----------------- Backend Function for getting Report Types in JS -----------------
@bp.route("/upload/getReportTypes")
@login_required
def getReportTypes():
    db = get_db()
    report_type_collection = db["reportType"]
    reportTypeList = list(report_type_collection.find())
    
    return Response(json_util.dumps(reportTypeList), mimetype="application/json")


# ----------------- DETAILS -----------------
@bp.route("/details/")
@bp.route("/details/<id>")
@login_required
def details(id=None):
    backPageUrl = "documents.search"
    db = get_db()
    document_collection = db["documents"]
    searchHistory_collection = db["searchHistory"]

    searchResults = document_collection.find_one({"_id": ObjectId(id)})

    # Toast
    try:
        if session["toastMessage"] != "":
            flash(session["toastMessage"], session["toastMessageCategory"])
            print("Toast Message sent")
            session["toastMessage"] = ""
            session["toastMessageCategory"] = ""
    except:
        pass
    
    print(searchResults)
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


# ----------------- DOWNLOAD DOCUMENT -----------------
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


# ----------------- SEARCH HISTORY -----------------
@bp.route("/search/searchHistory/")
@login_required
def searchHistory():
    backPageUrl = "documents.search"
    db = get_db()
    searchHistory_collection = db["searchHistory"]
    document_collection = db["documents"]
    user_collection = db["users"]
    
    # Search History of Current User
    searchHistoryList = list(
        searchHistory_collection
        .aggregate([
        {
            "$match": { "user_id": ObjectId(session["user_id"]) }
        },
        {
            "$lookup": {
                "from": "documents",
                "localField": "document_id",
                "foreignField": "_id",
                "as": "document_details"
            }
        },
        {
            "$unwind": "$document_details"
        },
        {
            "$project": {
                "document_details.title": 1,
                "document_details.document_number": 1,
                "document_details.year": 1,
                "document_details.author": 1,
                "document_details.division": 1,
                "document_details.reportType": 1,
                "document_details.uploaded_at": 1,
                "timestamp": 1
            }
        },
        { "$sort": { "timestamp": -1 } },
        ])
    )
    searchHistoryListLen = len(searchHistoryList)

    # Setting up pagination details
    list_number_of_documents_per_page = [5, 10, 20, 40, 60, 80]
    if request.args.get("docppag") is not None:
        session["number_of_documents_per_page"] = request.args.get("docppag", type=int)
    number_of_documents_per_page = session["number_of_documents_per_page"]
    current_page = request.args.get('page', default=0, type=int)
    number_of_pages = math.ceil(searchHistoryListLen / number_of_documents_per_page)

    searchHistoryList = list(
        searchHistory_collection
        .aggregate([
        {
            "$match": { "user_id": ObjectId(session["user_id"]) }
        },
        {
            "$lookup": {
                "from": "documents",
                "localField": "document_id",
                "foreignField": "_id",
                "as": "document_details"
            }
        },
        {
            "$unwind": "$document_details"
        },
        {
            "$project": {
                "document_id": 1,
                "document_details.title": 1,
                "document_details.document_number": 1,
                "document_details.year": 1,
                "document_details.author": 1,
                "document_details.division": 1,
                "document_details.reportType": 1,
                "document_details.uploaded_at": 1,
                "timestamp": 1
            }
        },
        { "$sort": { "timestamp": -1 } },
        { "$skip": number_of_documents_per_page * current_page },
        { "$limit": number_of_documents_per_page },
        ])
    )
    searchHistoryListLen = len(searchHistoryList)

    return render_template(
        "search/searchHistory.html",
        backPageUrl = backPageUrl,
        searchHistoryList = searchHistoryList,
        searchHistoryListLen = searchHistoryListLen,
        number_of_pages = number_of_pages,
        list_number_of_documents_per_page = list_number_of_documents_per_page,
        number_of_documents_per_page = number_of_documents_per_page,
        current_page = current_page
    )


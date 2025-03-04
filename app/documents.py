# ----------------- IMPORTS -----------------

import os
import json
import datetime
from datetime import datetime as dt
import math
import requests
import io
import zipfile

from flask import render_template, send_file, redirect, request, url_for, Blueprint, flash, session, make_response, jsonify, Response
from flask_login import (
    current_user,
    login_user,
    logout_user
)

import pymongo
from database import get_db, get_llm
from authentication import login_required
from helper import log_action
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
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
    print(request.path)
    db = get_db()
    user_collection = db["users"]
    document_collection = db["documents"]

    userDivision = user_collection.find_one({"_id": ObjectId(session["user_id"])})["division"]

    # Toast
    try:
        if session["toastMessage"] != "":
            flash(session["toastMessage"], session["toastMessageCategory"])
            print("Toast Message sent")
            session["toastMessage"] = ""
            session["toastMessageCategory"] = ""
    except:
        pass

    # Report types
    report_type_collection = db["reportType"]
    reportTypeList = list(report_type_collection.find( {"divisionID": ObjectId(session["userDivisionID"]) }))
    # Parent Report Types

    # Get the list of existing Parent report types 
    parentReportTypeList = list(
        report_type_collection.find(
            {
                "$or": [
                { "isSubReportType": False, "divisionID": ObjectId(session["userDivisionID"]) },
                { "isSubReportType": False, "isCommonToAllDivisions": True, }
                ]
            },
        ).sort("name", 1)
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
    refreshDocumentContent = ""
    refreshDocumentNumber = ""
    refreshAuthorName = ""
    refreshDocumentYear = ""
    refreshDivision = ""
    refreshReportType = ""
    refreshSubReportType = ""
    
    # document_title
    if request.args.get("document_title", default = "") != "":
        searchMetaData["title"] = {"$regex": request.args.get("document_title"), "$options": "i"}
        refreshDocumentTitle = request.args.get("document_title")
    else:
        searchMetaData.pop("title", None)
    # document_content
    if request.args.get("document_content", default = "") != "":
        searchMetaData["$text"] = {"$search": request.args.get("document_content", default="")}
        refreshDocumentContent = request.args.get("document_content")
    else:
        searchMetaData.pop("$text", None)
    # document_number
    if request.args.get("document_number", default = "") != "":
        searchMetaData["document_number"] = {"$regex": request.args.get("document_number"), "$options": "i"}    
        refreshDocumentNumber = request.args.get("document_number")
    else:
        searchMetaData.pop("document_number", None)
    # author_name
    if request.args.get("author", default = "") != "":
        searchMetaData["author_list"] = request.args.get("author")
        searchMetaData["author_list"] = {"$regex": request.args.get("author"), "$options": "i"}
        refreshAuthorName = request.args.get("author")
    else:
        searchMetaData.pop("author", None)
    # document_year
    if request.args.get("year", default = "") != "":
        searchMetaData["year"] = int(request.args.get("year"))
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

    # OPEN/CLOSE the SORT COLLAPSIBLE
    sortCollapse = ""
    if refreshSortData == {}:
        sortCollapse = ""
    else:
        sortCollapse = "show"
    print(sortCollapse)
    print(searchMetaData)

    # If searchMetaData is empty, show all common reportType documents from every division
    if (searchMetaData == {}) or (len(searchMetaData) == 1 and "division" in searchMetaData and searchMetaData["division"] != session["userDivision"]):
        if "division" in searchMetaData and searchMetaData["division"] != session["userDivision"]:
            searchDivisionType = searchMetaData["division"]
            search_results = list(
                document_collection.aggregate([
                    {
                        "$lookup": {
                            "from": "reportType",
                            "localField": "reportTypeID",
                            "foreignField": "_id",
                            "as": "reportTypeDetails"
                        }
                    },
                    {
                        "$match": {
                            "reportTypeDetails.isCommonToAllDivisions": True,
                            "division": searchDivisionType
                        }
                    },
                    {
                        "$project": {
                            "reportTypeDetails": 0,
                            "content": 0,
                            "summary": 0,
                            "summaryHTML": 0
                        }
                    }
                ])
            )
        else:
            search_results = list(
                document_collection.aggregate([
                    {
                        "$lookup": {
                            "from": "reportType",
                            "localField": "reportTypeID",
                            "foreignField": "_id",
                            "as": "reportTypeDetails"
                        }
                    },
                    {
                        "$match": {
                            "$or": [
                                { "division": session["userDivision"] },
                                { "reportTypeDetails.isCommonToAllDivisions": True }
                            ]
                        }
                    },
                    {
                        "$project": {
                            "reportTypeDetails": 0,
                            "content": 0,
                            "summary": 0,
                            "summaryHTML": 0
                        }
                    }
                ])
            )
    else:
        # DEFAULT VIEW: Recently uploaded documents
        search_results = list(document_collection.find(
                searchMetaData,
                { "content": 0, "summary": 0, "summaryHTML": 0 }
            )
        )


    print(search_results)
    totalNumberOfDocuments = len(search_results)
    
    # Setting up pagination details
    if request.args.get("docppag") is not None:
        session["number_of_documents_per_page"] = request.args.get("docppag", type=int)
    number_of_documents_per_page = session["number_of_documents_per_page"]
    current_page = request.args.get('page', default=0, type=int)
    number_of_pages = math.ceil(totalNumberOfDocuments / number_of_documents_per_page)

    if (searchMetaData == {}) or (len(searchMetaData) == 1 and "division" in searchMetaData and searchMetaData["division"] != session["userDivision"]):
        if "division" in searchMetaData and searchMetaData["division"] != session["userDivision"]:
            searchResultsTrimmed = list(
                document_collection.aggregate([
                    {
                        "$lookup": {
                            "from": "reportType",
                            "localField": "reportTypeID",
                            "foreignField": "_id",
                            "as": "reportTypeDetails"
                        }
                    },
                    {
                        "$match": {
                            "reportTypeDetails.isCommonToAllDivisions": True,
                            "division": searchMetaData["division"]
                        }
                    },
                    {
                        "$project": {
                            "content": 0,
                            "summary": 0,
                            "summaryHTML": 0
                        }
                    },
                    { "$sort" : sortMetaData },
                    { "$skip" : number_of_documents_per_page * current_page },
                    { "$limit" : number_of_documents_per_page },
                ])
            )
        else:
            searchResultsTrimmed = list(
                document_collection.aggregate([
                    {
                        "$lookup": {
                            "from": "reportType",
                            "localField": "reportTypeID",
                            "foreignField": "_id",
                            "as": "reportTypeDetails"
                        }
                    },
                    {
                        "$match": {
                            "$or": [
                                { "division": session["userDivision"] },
                                { "reportTypeDetails.isCommonToAllDivisions": True }
                            ]
                        }
                    },
                    {
                        "$project": {
                            "content": 0,
                            "summary": 0,
                            "summaryHTML": 0
                        }
                    },
                    { "$sort" : sortMetaData },
                    { "$skip" : number_of_documents_per_page * current_page },
                    { "$limit" : number_of_documents_per_page },
                ])
            )

    else:
        searchResultsTrimmed = list(document_collection.find(
            searchMetaData,
            { "content": 0, "summary": 0, "summaryHTML": 0 },
            sort = sortMetaData,
            skip = number_of_documents_per_page * current_page,
            limit = number_of_documents_per_page,
        ))

    searchResultsTrimmedLen = len(searchResultsTrimmed)
    print(refreshSortData.get("document_title", ""))
    return render_template(
        "search/retreiveDocuments.html",
        backPageUrl = backPageUrl,
        userDivision = userDivision,
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
        refreshDocumentContent = refreshDocumentContent,
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
    user_collection = db["users"]
    file_collection = db["fs.files"]
    isMaster = session["isMaster"]

    # Allowed file extensions
    allowed_file_extensions = ["pdf"]

    userDivision = user_collection.find_one({"_id": ObjectId(session["user_id"])})["division"]
    
    # Parent Report types sort by alphabetical order
    report_type_collection = db["reportType"]
    reportTypeList = list(report_type_collection.find( {"divisionID": ObjectId(session["userDivisionID"]) }))

    # Get the list of existing Parent report types 
    parentReportTypeList = list(
        report_type_collection.find(
            {
                "$or": [
                { "isSubReportType": False, "divisionID": ObjectId(session["userDivisionID"]) },
                { "isSubReportType": False, "isCommonToAllDivisions": True, }
                ]
            }
        ).sort("name", 1)
    )

    subReportTypeList = list(
        report_type_collection.find(
            {
                "isSubReportType": True,
                "divisionID": ObjectId(session["userDivisionID"])
            }
        ).sort("name", pymongo.ASCENDING)
    )
    parentReportTypeListLen = len(parentReportTypeList)

    if isMaster:
        # Get all the parent report types regardless of the division
        parentReportTypeList = list(
            report_type_collection.find(
                {
                    "isSubReportType": False
                }
            ).sort("name", 1)
        )

        # Get all the sub report types regardless of the division
        subReportTypeList = list(
            report_type_collection.find(
                {
                    "isSubReportType": True
                }
            ).sort("name", pymongo.ASCENDING)
        )

    # Sub Report types

    

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

        generateTitleAutomatic = request.form.getlist("generateTitle")
        if "true" not in generateTitleAutomatic:
            title = request.form["document_title"].strip()
            document_number = request.form["document_number"]
            year = request.form["document_year"]
            author_list = request.form.getlist("author_name[]")
            author = author_list[0]

        division = request.form["division"]
        email_list = request.form.getlist("email[]")
        email = email_list[0]

        reportTypeId = ObjectId(request.form["report_type"])
        if request.form.get("sub_report_type", default="") != "":
            subReportTypeId = ObjectId(request.form.get("sub_report_type"))
        else:
            subReportTypeId = None

        file_data = request.files["documents"]
        file_extension = file_data.filename.split(".")[-1]
        ocrValue = request.form.getlist("ocrValue")
        
        reportType = report_type_collection.find_one({"_id": reportTypeId})["name"]
        if subReportTypeId != None:
            subReportType = report_type_collection.find_one({"_id": subReportTypeId})["name"]
        else:
            subReportType = None
        
        checkFileExists = list(file_collection.find({"filename": file_data.filename}))
        checkFileExists = True if len(checkFileExists) != 0 else False

        avoidAI = request.form.getlist("avoidAI")


        if False:
            # flash("File already exists. Please choose another file.", "Alert")
            session["toastMessage"] = "File already exists. Please choose another file."
            session["toastMessageCategory"] = "Alert"
            return redirect(url_for("documents.upload"))
        elif file_extension not in allowed_file_extensions:
            # Compressing the file to ZIP
            filename = secure_filename(file_data.filename)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                zip_file.writestr(filename, file_data.read())

            zip_buffer.seek(0)
            file_id = fs.put(zip_buffer, filename=f"{filename}.zip")
            document_metadata = {
                "uploadedBy": ObjectId(session["user_id"]),
                "title": title,
                "year": int(year),
                "document_number": document_number,
                "division": division,
                "divisionID": ObjectId(session["userDivisionID"]),
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
                "content": "",
                "uploaded_at": datetime.datetime.now(),
                "summary": "",
                "summaryHTML": "",
                "reportTypeID": reportTypeId,
                "subReportTypeID": subReportTypeId
            }
            try:
                inserted_document = document_collection.insert_one(document_metadata)
                document_id = inserted_document.inserted_id

                # Check if the report type is common
                if report_type_collection.find_one({"name": reportType})["isCommonToAllDivisions"] == False:
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
                else:
                    divisions_collection.update_one(
                        {
                            "name": str(division)
                        },
                        {
                            "$inc": {
                                "common_document_count": 1
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

                # Log Action
                log_action(
                    action="document_upload",
                    user_id=session["user_id"],
                    document_id=document_id,
                    division_id=session["userDivisionID"],
                    details={},
                    comment="The files type was not supported. The file was compressed to a ZIP file and uploaded."
                )

                print("Successfully uploaded the document")
                session["toastMessage"] = "Document uploaded successfully"
                session["toastMessageCategory"] = "Success"
            except:
                print("some error")

            return redirect(url_for("documents.upload"))
        else:
            content = []
            if "true" in ocrValue:
                file_data.save(os.path.join("converted_pdf/", "input_pdf_test.pdf"))
                ocrmypdf.ocr("converted_pdf/input_pdf_test.pdf", "converted_pdf/ouptut_pdf.pdf", deskew=True, force_ocr=True,output_type="pdf" )
                converted_file_data = open("converted_pdf/ouptut_pdf.pdf", 'rb')
                file_name = secure_filename(title + ".pdf")
                file_id = fs.put(converted_file_data, filename=file_name)
                reader = PdfReader(converted_file_data)
            else:
                file_name = secure_filename(file_data.filename)
                file_id = fs.put(file_data, filename=file_name)
                reader = PdfReader(file_data)

            for page in reader.pages:
                content.append(page.extract_text())
            content = str(content)
            content = content.replace("\\n", " ")

            # SUMMARY GENERATION
            if "true" not in avoidAI:
                llm = get_llm()
                prompt = f"""
                You are an intelligent assistant designed to help students understand complex topics. Your goal is to read and restructure the contents of a given PDF in a way that makes learning easier.

                Task:
                    •	Summarize and explain the concepts clearly.
                    •	Use simple language and avoid unnecessary complexity.
                    •	Organize content with proper headings and subheadings.
                    •	Include meaningful examples with explanations.
                    •	State the reasoning behind each example to improve comprehension.
                
                Output Format:
                Ensure the explanation is well-structured with:
                    1.	Headings & Subheadings
                    2.	Concise explanations
                    3.	Relevant examples with explanations
                
                Your goal is to make learning engaging, structured, and easy to understand for students.

                Here is the content:
                {content}
                """
                summary = llm.invoke(prompt)

                # HTML generation from the summary
                promptHTML = f"""
                You are an AI that converts textual content into structured HTML format. 
                Ensure proper usage of <h5>, <h6>, <p>, <ul>/<li>, <b> and <i> tags where appropriate.

                Convert the following text into valid HTML:

                {summary}

                Output only the generated HTML code.
                """
                summaryHTML = llm.invoke(promptHTML)

                if "true" in generateTitleAutomatic:
                    # Get document title, document number and year in JSON format
                    promptTitle = f"""
                    Extract the **title**, **document number**, **year**, and **author** from the following PDF content.

                    PDF Content:
                    {content}

                    Provide the output strictly in JSON format with the following structure:
                    {{
                        "title": "<Title of the document>",
                        "document_number": "<Document number>",
                        "year": "<Year>",
                        "author": "<Author>",
                    }}

                    
                    Ensure the question is well-structured and aligned with the given content.
                    Output only the JSON.
                    """
                    titleDocumentNumberYear = llm.invoke(promptTitle)
                    titleDocumentNumberYearJSON = json.loads(titleDocumentNumberYear)

                    title = titleDocumentNumberYearJSON["title"]
                    document_number = titleDocumentNumberYearJSON["document_number"]
                    year = titleDocumentNumberYearJSON["year"]
                    if not year or type(year) != int:
                        year = dt.now().year
                    author = titleDocumentNumberYearJSON["author"]
                    author_list = [author]
            else:
                summary = ""
                summaryHTML = ""
                title = request.form["document_title"]
                document_number = request.form["document_number"]
                year = request.form["document_year"]
                author_list = request.form.getlist("author_name[]")
                author = author_list[0]
            
            document_metadata = {
                "uploadedBy": ObjectId(session["user_id"]),
                "title": title,
                "year": int(year),
                "document_number": document_number,
                "division": division,
                "divisionID": ObjectId(session["userDivisionID"]),
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
                "uploaded_at": datetime.datetime.now(),
                "summary": summary,
                "summaryHTML": summaryHTML,
                "reportTypeID": reportTypeId,
                "subReportTypeID": subReportTypeId
            }



            try:
                inserted_document = document_collection.insert_one(document_metadata)
                document_id = inserted_document.inserted_id
                # Check if the report type is common
                if report_type_collection.find_one({"name": reportType})["isCommonToAllDivisions"] == False:
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
                else:
                    divisions_collection.update_one(
                        {
                            "name": str(division)
                        },
                        {
                            "$inc": {
                                "common_document_count": 1
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
                # Log Action
                log_action(
                    action="document_upload",
                    user_id=session["user_id"],
                    document_id=document_id,
                    division_id=session["userDivisionID"],
                    details={},
                    comment="The file was uploaded successfully."
                )
                print("Successfully uploaded the document")
                session["toastMessage"] = "Document uploaded successfully"
                session["toastMessageCategory"] = "Success"
            except:
                print("some error")

            return redirect(url_for("documents.upload"))

    return render_template(
        "search/uploadDocuments.html",
        isMaster = session["isMaster"],
        uploadedDocuments = uploadedDocuments,
        uploadedDocumentsLen = len(uploadedDocuments),
        totalNumberOfDocuments = totalNumberOfDocuments,
        number_of_pages = number_of_pages,
        list_number_of_documents_per_page = list_number_of_documents_per_page,
        number_of_documents_per_page = number_of_documents_per_page,
        current_page = current_page,
        parentReportTypeList = parentReportTypeList,
        divisionList = divisionList,
        current_year = dt.now().year,   
        userDivision = userDivision
    )


# ----------------- EDIT DOCUMENTS -----------------
@bp.route("/details/editDocument/", methods=["GET", "POST"])
@bp.route("/details/editDocument/<id>", methods=["GET", "POST"])
@login_required
def editDocument(id = None):
    backPageUrl = "documents.search"
    db = get_db()
    document_collection = db["documents"]
    report_type_collection = db["reportType"]

    # Parent Report types
    parentReportTypeList = list(
        report_type_collection.find(
            {
                "$or": [
                { "isSubReportType": False, "divisionID": ObjectId(session["userDivisionID"]) },
                { "isSubReportType": False, "isCommonToAllDivisions": True, }
                ]
            }
        ).sort("name", 1)
    )

    subReportTypeList = list(
        report_type_collection.find(
            {
                "isSubReportType": True,
                "divisionID": ObjectId(session["userDivisionID"])
            }
        ).sort("name", pymongo.ASCENDING)
    )
    parentReportTypeListLen = len(parentReportTypeList)
        
    # Division types
    divisions_collection = db["divisions"]
    divisionList = list(divisions_collection.find())

    # Current Document Details
    currentDocument = document_collection.find_one({"_id": ObjectId(id)})

    if "subReportTypeID" in currentDocument:
        subReportTypeId = currentDocument["subReportTypeID"]
    else:
        subReportTypeId = None

    if "reportTypeID" in currentDocument:
        reportTypeId = currentDocument["reportTypeID"]
    else:
        reportTypeId = None
    oldDetails = {
        "title": currentDocument["title"],
        "year": currentDocument["year"],
        "document_number": currentDocument["document_number"],
        "author": currentDocument["author"],
        "reportType": currentDocument["reportType"],
        "reportTypeID": reportTypeId,
        "subReportType": currentDocument["subReportType"],
        "subReportTypeID": subReportTypeId,
        "email": currentDocument["email"],
        "author_list": currentDocument["author_list"],
        "email_list": currentDocument["email_list"]
    }
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
        if request.form.get("new_sub_report_type", "") != "":
            subReportTypeId = ObjectId(request.form["new_sub_report_type"])
        else:
            subReportTypeId = None

        newParentReportType = report_type_collection.find_one({"_id": reportTypeId})
        if subReportTypeId != None:
            newSubReportType = report_type_collection.find_one({"_id": subReportTypeId})
        else:
            newSubReportType = None
        reportType = report_type_collection.find_one({"_id": reportTypeId})["name"]
        if subReportTypeId != None:
            subReportType = report_type_collection.find_one({"_id": subReportTypeId})["name"]
        else:
            subReportType = None

        author = author_list[0]
        email = email_list[0]

        # If the document is a PDF file, check if re-OCR is required
        file_id = currentDocument["file_id"]
        file = fs.get(file_id)
        file_extension = file.filename.split(".")[-1]
        # Check if document is a PDF file
        if file_extension == "pdf":
            # apply OCR using ocrmypdf
            ocrValue = request.form.getlist("ocrValue")
            if "true" in ocrValue:
                file_data = fs.get(file_id)
                file_bytes = file_data.read()

                # Save the input PDF to disk
                input_pdf_path = "converted_pdf/input_pdf_test.pdf"
                output_pdf_path = "converted_pdf/output_pdf.pdf"
                
                with open(input_pdf_path, "wb") as f:
                    f.write(file_bytes)

                # Apply OCR using ocrmypdf
                ocrmypdf.ocr(input_pdf_path, output_pdf_path, deskew=True, force_ocr=True, output_type="pdf")

                # Store the converted file in MongoDB GridFS
                with open(output_pdf_path, 'rb') as converted_file:
                    file_id = fs.put(converted_file, filename=file.filename)

                # Extract text from the OCR-processed PDF
                reader = PdfReader(output_pdf_path)
                content = []
                for page in reader.pages:
                    content.append(page.extract_text())
                content = " ".join(content).replace("\\n", " ")

            else:
                content = currentDocument["content"]


            # SUMMARY GENERATION
            llm = get_llm()
            summaryGenerate = request.form.getlist("regenerateSummary")            
            if "true" in summaryGenerate:
                prompt = f"""
                You are an intelligent assistant designed to help students understand complex topics. Your goal is to read and restructure the contents of a given PDF in a way that makes learning easier.

                Task:
                    •	Summarize and explain the concepts clearly.
                    •	Use simple language and avoid unnecessary complexity.
                    •	Organize content with proper headings and subheadings.
                    •	Include meaningful examples with explanations.
                    •	State the reasoning behind each example to improve comprehension.
                
                Output Format:
                Ensure the explanation is well-structured with:
                    1.	Headings & Subheadings
                    2.	Concise explanations
                    3.	Relevant examples with explanations
                
                Your goal is to make learning engaging, structured, and easy to understand for students.

                Here is the content:
                {content}
                """
                summary = llm.invoke(prompt)

                # HTML generation from the summary
                promptHTML = f"""
                You are an AI that converts textual content into structured HTML format. 
                Ensure proper usage of <h5>, <h6>, <p>, <ul>/<li>, <b> and <i> tags where appropriate.

                Convert the following text into valid HTML:

                {summary}

                Output only the generated HTML code.
                """
                summaryHTML = llm.invoke(promptHTML)
            else:
                summary = currentDocument["summary"]
                summaryHTML = currentDocument["summaryHTML"]
        else:
            content = currentDocument["content"]
            summary = currentDocument["summary"]
            summaryHTML = currentDocument["summaryHTML"]
        newDetails = {
                    "title": title,
                    "year": int(year),
                    "document_number": document_number,
                    "author": author,
                    "reportType": reportType,
                    "reportTypeID": reportTypeId,
                    "subReportType": subReportType,
                    "subReportTypeID": subReportTypeId,
                    "email": email,
                    "author_list": author_list,
                    "email_list": email_list,
                    "file_id": file_id,
                    "content": content,
                    "summary": summary,
                    "summaryHTML": summaryHTML,
                    "editedAt": datetime.datetime.now()
                }
        
        # If the report type is changes, check if the previous report type is common or not and change the document count accordingly
        previousParentReportType = report_type_collection.find_one({"_id": oldDetails["reportTypeID"]})
        previousSubReportType = report_type_collection.find_one({"_id": oldDetails["subReportTypeID"]})
        print("Previout Parent Report Type", previousParentReportType)
        print("Previout Parent Report Type", previousSubReportType)
        if previousParentReportType != None:
            if previousParentReportType["isCommonToAllDivisions"] == False:
                divisions_collection.update_one(
                    {
                        "name": currentDocument["division"]
                    },
                    {
                        "$inc": {
                            "documentCount": -1
                        }
                    }
                )
            else:
                divisions_collection.update_one(
                    {
                        "name": currentDocument["division"]
                    },
                    {
                        "$inc": {
                            "common_document_count": -1
                        }
                    }
                )

            
        if newParentReportType["isCommonToAllDivisions"] == False:
            divisions_collection.update_one(
                {
                    "name": currentDocument["division"]
                },
                {
                    "$inc": {
                        "documentCount": 1
                    }
                }
            )
        else:
            divisions_collection.update_one(
                {
                    "name": currentDocument["division"]
                },
                {
                    "$inc": {
                        "common_document_count": 1
                    }
                }
            )

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
        if subReportType != currentDocument["subReportType"]:
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
                "$set": newDetails
            }
        )

        # Log Action
        log_action(
            action="document_edit",
            user_id=session["user_id"],
            document_id=ObjectId(id),
            division_id=session["userDivisionID"],
            details={
                "oldDetails": oldDetails,
                "newDetails": newDetails
            },
            comment="The document was edited successfully.",
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
    
    fs = gridfs.GridFS(db)
    document_details = document_collection.find_one({"_id": ObjectId(id)})
    document_details = {
        "title": document_details["title"],
        "year": document_details["year"],
        "document_number": document_details["document_number"],
        "author": document_details["author"],
        "reportType": document_details["reportType"],
        "subReportType": document_details["subReportType"],
        "email": document_details["email"],
        "author_list": document_details["author_list"],
        "email_list": document_details["email_list"]
    }

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
    file_id = document_collection.find_one({"_id": ObjectId(id)})["file_id"]
    fs.delete(file_id)
    document_collection.delete_one({"_id": ObjectId(id)})
    
    # Log Action
    log_action(
        action="document_delete",
        user_id=session["user_id"],
        document_id=ObjectId(id),
        division_id=session["userDivisionID"],
        details=document_details,
        comment="The document was deleted successfully."
    )

    # Toast
    session["toastMessage"] = "Document deleted successfully"
    session["toastMessageCategory"] = "Success"
    print("Deleted document confirmation")
    return redirect(url_for("documents.search"))


# ----------------- Backend Function for getting Report Types in JS -----------------
@bp.route("/upload/getReportTypes")
@login_required
def getReportTypes():
    db = get_db()
    report_type_collection = db["reportType"]
    reportTypeList = list(report_type_collection.find().sort("name", pymongo.ASCENDING))
    
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

    searchResults = document_collection.find_one(
        {"_id": ObjectId(id)},
        {"content": 0}
    )

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
    
    # Check if the current user the one who uploaded the document
    isUploader = False
    if searchResults["uploadedBy"] == ObjectId(session["user_id"]):
        isUploader = True
    return render_template(
        "search/documentDetails.html", 
        backPageUrl = backPageUrl,
        searchResults = searchResults,
        numOfAuthors = len(searchResults["author_list"]),
        isAdmin = session["isAdmin"],
        isMaster = session["isMaster"],
        isUploader = isUploader
    )


@bp.route("/download/<id>")
@login_required
def download(id=None):
    db = get_db()
    grid_fs = GridFS(db)
    file_data = grid_fs.find_one({'_id': ObjectId(id)})
    
    # Read the file content
    file_stream = io.BytesIO(file_data.read())

    # Send the file as a response with 'attachment' to force download
    response = send_file(
        file_stream,
        as_attachment=True,  # Force download
        download_name=file_data.filename,
        mimetype=file_data.content_type
    )
    
    return response


# ----------------- VIEW FILE -----------------
@bp.route("/viewFile/<id>")
@login_required
def viewFile(id = None):
    db = get_db()
    grid_fs = GridFS(db)
    file_data = grid_fs.find_one({'_id': ObjectId(id)})
    # Read the file content
    file_stream = io.BytesIO(file_data.read())

    # Send the file as a response
    response = send_file(
        file_stream,
        as_attachment=False,
        download_name=file_data.filename,
        mimetype=file_data.content_type
    )
    
    # Force the file to open in a new tab with the correct name
    response.headers["Content-Disposition"] = f"inline; filename={file_data.filename}"
    return response

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


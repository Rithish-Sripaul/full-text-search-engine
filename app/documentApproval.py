import os
import datetime
import math
from flask import render_template, redirect, request, url_for, Blueprint, flash, session, make_response
from flask_login import (
    current_user,
    login_user,
    logout_user
)

import pymongo
from database import get_db
from authentication import login_required
from bson.objectid import ObjectId

bp = Blueprint("documentApproval", __name__, url_prefix='')

@bp.route("/approval")
@login_required
def approval(id=None):
    backPageUrl = "documents.search"

    db = get_db()
    document_collection = db["documents"]
    user_collection = db["users"]
    current_user = user_collection.find_one({"_id": ObjectId(session["user_id"])})
    print(current_user)
    
    notApprovedDocuments = list(
        document_collection.aggregate(
            [
                {
                    "$lookup" : {
                        "from" : "users",
                        "localField" : "uploadedBy",
                        "foreignField" : "_id",
                        "as" : "uploadedUser"
                    }
                },
                {
                    "$match" : {
                        "uploadedUser.adminAccount": current_user["_id"],
                        "isApproved": 0
                    }
                },
                { "$project":  {"uploadedUser": 0} },
                { "$sort": {"uploaded_at": -1} }
            ]
        )
    )
    totalNumberOfDocuments = len(notApprovedDocuments)

    # Setting up pagination details
    list_number_of_documents_per_page = [5, 10, 20, 40]
    if request.args.get("docppag") is not None:
        session["number_of_documents_per_page"] = request.args.get("docppag", type=int)
    number_of_documents_per_page = session["number_of_documents_per_page"]

    current_page = request.args.get('page', default=0, type=int)
    number_of_pages = math.ceil(totalNumberOfDocuments / number_of_documents_per_page)
    notApprovedDocuments = list(
        document_collection.aggregate(
            [
                {
                    "$lookup" : {
                        "from" : "users",
                        "localField" : "uploadedBy",
                        "foreignField" : "_id",
                        "as" : "uploadedUser"
                    }
                },
                {
                    "$match" : {
                        "uploadedUser.adminAccount": current_user["_id"],
                        "isApproved": 0
                    }
                },
                { "$project":  {"uploadedUser": 0} },
                { "$skip": number_of_documents_per_page * current_page },
                { "$limit": number_of_documents_per_page },
                { "$sort": {"uploaded_at": -1} }
            ]
        )
    )


    return render_template(
        "search/approveDocuments.html",
        backPageUrl = backPageUrl,
        user_collection = user_collection,
        notApprovedDocuments = notApprovedDocuments,
        notApprovedDocumentsLen = len(notApprovedDocuments),
        totalNumberOfDocuments = totalNumberOfDocuments,
        number_of_pages = number_of_pages,
        list_number_of_documents_per_page = list_number_of_documents_per_page,
        number_of_documents_per_page = number_of_documents_per_page,
        current_page = current_page
    )

@bp.route("/approvalDocumentDetails/")
@bp.route("/approvalDocumentDetails/<id>", methods=["GET", "POST"])
@login_required
def approvalDocumentDetails(id = None):
    backPageUrl = "documentApproval.approval"

    db = get_db()
    document_collection = db["documents"]
    user_collection = db["users"]
    currentDocument = document_collection.find_one({ "_id" : ObjectId(id) })
    uploadedUser = user_collection.find_one({ "_id": currentDocument["uploadedBy"] })

    if request.method == "POST":
        if "approve" in request.form:
            query_filter = { "_id": ObjectId(id) }
            update_operation = {
                "$set": {
                    "isApproved": 1,
                    "approvedBy": ObjectId(session["user_id"]),
                    "approved_at": datetime.datetime.now() 
                },
                "$currentDate": { "lastUpdated" : True }
            }

            document_collection.update_one(query_filter, update_operation)
        elif "deny" in request.form:
            query_filter = { "_id": ObjectId(id) }
            update_operation = {
                "$set": {
                    "isApproved": -1,
                    "approvedBy": ObjectId(session["user_id"]),
                    "approved_at": datetime.datetime.now() 
                },
                "$currentDate": { "lastUpdated" : True }
            }
            
            document_collection.update_one(query_filter, update_operation)
        return redirect(url_for("documentApproval.approval"))


    return render_template(
        "search/documentDetailsApproval.html",
        backPageUrl = backPageUrl,
        currentDocument = currentDocument,
        uploadedUser = uploadedUser
    )
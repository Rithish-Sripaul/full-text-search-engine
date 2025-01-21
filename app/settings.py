import os
import datetime
import math
from flask import render_template, redirect, request, url_for, Blueprint, flash, session, make_response
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from authentication import login_required
import pymongo
from database import get_db
from bson.objectid import ObjectId

bp = Blueprint("settings", __name__, url_prefix="")

@bp.route("/settings/reportType/", methods=["GET", "POST"])
@login_required
def reportType():
  backPageUrl = "documents.search"

  db = get_db()
  report_collection = db["reportType"]
  divisions_collection = db["divisions"]
 
  # Get the list of existing Parent report types
  parentReportTypeList = list(
    report_collection.find({"isSubReportType": False})
  )

  # Get the list of existing report types
  reportTypesListLen = report_collection.count_documents({})

  # Setting up pagination details
  list_number_of_documents_per_page = [5, 10, 20, 40]
  if request.args.get("docppag") is not None:
    session["number_of_documents_per_page"] = request.args.get("docppag", type=int)
  number_of_documents_per_page = session["number_of_documents_per_page"]

  current_page = request.args.get('page', default=0, type=int)
  number_of_pages = math.ceil(reportTypesListLen / number_of_documents_per_page)

  reportTypesList = list(
      report_collection.aggregate([
          {
              "$lookup": {
                  "from": "reportType",
                  "localField": "parentReportType",
                  "foreignField": "_id",
                  "as": "parentReportTypeDetails"
              }
          },
          {
              "$addFields": {
                  "parentReportTypeName": {
                    "$arrayElemAt": ["$parentReportTypeDetails.name", 0]
                  }
              }
          },
          {
              "$project": {
                  "parentReportTypeDetails": 0
              }
          },
          { "$sort": {"uploadedAt": -1} },
          { "$skip": number_of_documents_per_page * current_page },
          { "$limit": number_of_documents_per_page },

      ])
    )
  if request.method == "POST":
    # NEW REPORT TYPE
    if "report-type-submit" in request.form:
      reportTypeName = request.form["report_type_name"]

      document_metadata = {
        "name": reportTypeName,
        "uploaded_by": ObjectId(session["user_id"]),
        "hasSubReportType": False,
        "isSubReportType": False,
        "parentReportType": None,
        "documentCount": 0,
        "uploadedAt": datetime.datetime.now(),
      }

      try:
        report_collection.insert_one(document_metadata)
        return redirect(url_for("settings.reportType"))
      except:
        print("Couldn't upload report type")
    
    # NEW SUB REPORT TYPE
    elif "sub-report-type-submit" in request.form:
      parentReportType = request.form["parent_report_type"]
      subReportTypeName = request.form["sub_report_type"]
      print(parentReportType)
  
      document_metadata = {
        "name": subReportTypeName,
        "uploaded_by": ObjectId(session["user_id"]),
        "hasSubReportType": False,
        "isSubReportType": True,
        "parentReportType": ObjectId(parentReportType),
        "documentCount": 0,
        "uploadedAt": datetime.datetime.now(),
      }

      # Upload sub report type and update parent report type
      try:
        report_collection.insert_one(document_metadata)
        report_collection.update_one(
          { "_id": ObjectId(parentReportType) },
          {
            "$set": {
              "hasSubReportType": True
            }
          }
        )
        return redirect(url_for("settings.reportType"))
      except:
        print("Couldn't upload sub report type")

  return render_template(
    "settings/reportType.html",
    backPageUrl = backPageUrl,
    reportTypesList = reportTypesList,
    reportTypesListLen = len(reportTypesList),
    parentReportTypeList = parentReportTypeList,
    number_of_pages = number_of_pages,
    list_number_of_documents_per_page = list_number_of_documents_per_page,
    number_of_documents_per_page = number_of_documents_per_page,
    current_page = current_page,
  )
  
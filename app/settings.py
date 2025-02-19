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
from helper import log_action
import pymongo
from database import get_db
from bson.objectid import ObjectId

bp = Blueprint("settings", __name__, url_prefix="")

# ----------------- ADD REPORT TYPE -----------------
@bp.route("/settings/reportType/", methods=["GET", "POST"])
@login_required
def reportType():
  backPageUrl = "documents.search"

  # Toast Message
  try:
    if session["toastMessage"] != "":
      flash(session["toastMessage"], session["toastMessageCategory"])
      print("Toast Message sent")
      session["toastMessage"] = ""
  except:
    pass

  db = get_db()
  report_collection = db["reportType"]
  divisions_collection = db["divisions"]
 
  # Get the list of existing Parent report types 
  parentReportTypeList = list(
    report_collection.find(
      {
        "$or": [
          { "isSubReportType": False, "divisionID": ObjectId(session["userDivisionID"]) },
          { "isSubReportType": False, "isCommonToAllDivisions": True }
        ]
      }
    )
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
            "$match": {
              "$or": [
                {"divisionID": ObjectId(session["userDivisionID"])},
                {"isCommonToAllDivisions": True}
              ]
            }
          },
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
      if "true" in request.form.getlist("is_common_to_all_divisions"):
        isCommonToAllDivisions = True
      else:
        isCommonToAllDivisions = False

      documentExists = report_collection.find_one({"name": reportTypeName, "divisionID": ObjectId(session["userDivisionID"])})
      if documentExists:
        session["toastMessage"] = "Report Type already exists"
        session["toastMessageCategory"] = "Alert"
        return redirect(url_for("settings.reportType"))

      document_metadata = {
        "name": reportTypeName,
        "uploaded_by": ObjectId(session["user_id"]),
        "hasSubReportType": False,
        "isSubReportType": False,
        "parentReportType": None,
        "documentCount": 0,
        "divisionID": ObjectId(session["userDivisionID"]),
        "isCommonToAllDivisions": isCommonToAllDivisions,
        "uploadedAt": datetime.datetime.now(),
      }

      try:
        insertedReportType = report_collection.insert_one(document_metadata)
        reportTypeID = insertedReportType.inserted_id
        session["toastMessage"] = "Report Type uploaded successfully"
        session["toastMessageCategory"] = "Success"

        # Log Action
        log_action(
          action="report_type_created",
          user_id=session["user_id"],
          details={
            "reportTypeID": ObjectId(reportTypeID),
            "reportTypeName": reportTypeName,
            "isCommonToAllDivisions": isCommonToAllDivisions
          },
          division_id=session["userDivisionID"],
          comment="Report Type Created"
        )

        return redirect(url_for("settings.reportType"))
      except:
        print("Couldn't upload report type")
    
    # NEW SUB REPORT TYPE
    elif "sub-report-type-submit" in request.form:
      parentReportType = request.form["parent_report_type"]
      subReportTypeName = request.form["sub_report_type"]

      isCommonToAllDivisions = report_collection.find_one({"_id": ObjectId(parentReportType)})["isCommonToAllDivisions"]

      documentExists = report_collection.find_one(
        {
          "name": subReportTypeName,
          "parentReportType": ObjectId(parentReportType)
        })
      if documentExists:
        session["toastMessage"] = "Sub Report Type already exists"
        session["toastMessageCategory"] = "Alert"
        return redirect(url_for("settings.reportType"))
      document_metadata = {
        "name": subReportTypeName,
        "uploaded_by": ObjectId(session["user_id"]),
        "hasSubReportType": False,
        "isSubReportType": True,
        "parentReportType": ObjectId(parentReportType),
        "documentCount": 0,
        "divisionID": ObjectId(session["userDivisionID"]),
        "isCommonToAllDivisions": isCommonToAllDivisions,
        "uploadedAt": datetime.datetime.now(),
      }

      # Upload sub report type and update parent report type
      try:
        insertedReportType = report_collection.insert_one(document_metadata)
        reportTypeID = insertedReportType.inserted_id
        report_collection.update_one(
          { "_id": ObjectId(parentReportType) },
          {
            "$set": {
              "hasSubReportType": True
            }
          }
        )
        session["toastMessage"] = "Sub Report Type uploaded successfully"
        session["toastMessageCategory"] = "Success"

        # Log Action
        log_action(
          action="sub_report_type_created",
          user_id=session["user_id"],
          details={
            "parentReportTypeName": report_collection.find_one({"_id": ObjectId(parentReportType)})["name"],
            "parentReportTypeID": ObjectId(parentReportType),
            "reportTypeID" : reportTypeID,
            "subReportTypeName": subReportTypeName,
            "isCommonToAllDivisions": isCommonToAllDivisions
          },
          division_id=session["userDivisionID"],
          comment="Sub Report Type Created"
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


# ----------------- ACTION LOGS -----------------
@bp.route("/settings/actionLogs/", methods=["GET"])
@login_required
def actionLogs():
  db = get_db()
  action_collection = db["actionLogs"]

  actionLogList = list(
    action_collection.find(
      {
        "$or": [
          { "adminID": ObjectId(session["user_id"]) },
          { "user_id": ObjectId(session["user_id"]) }
        ]
      }
    )
  )

  actionLogListLen = len(actionLogList)


  list_number_of_documents_per_page = [5, 10, 20, 40, 60, 80]
  if request.args.get("docppag") is not None:
    session["number_of_documents_per_page"] = request.args.get("docppag", type=int)
  number_of_documents_per_page = session["number_of_documents_per_page"]
  current_page = request.args.get('page', default=0, type=int)
  number_of_pages = math.ceil(actionLogListLen / number_of_documents_per_page)

  actionLogList = list(
    action_collection.find(
      {
        "$or": [
          { "adminID": ObjectId(session["user_id"]) },
          { "user_id": ObjectId(session["user_id"]) }
        ]
      },
      sort=[("timestamp", pymongo.DESCENDING)],
      skip=number_of_documents_per_page * current_page,
      limit=number_of_documents_per_page
    )
  )
  actionLogListLen = len(actionLogList)


  return render_template(
    "settings/actionLogs.html",
    actionLogList = actionLogList,
    actionLogListLen = actionLogListLen,
    number_of_pages = number_of_pages,
    list_number_of_documents_per_page = list_number_of_documents_per_page,
    number_of_documents_per_page = number_of_documents_per_page,
    current_page = current_page,
  )
import os
import datetime
import math
from flask import render_template, redirect, request, url_for, Blueprint, flash, session, make_response, Response
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from authentication import login_required
from helper import log_action
import pymongo
from werkzeug.utils import secure_filename
from database import get_db
from bson.objectid import ObjectId

import gridfs
from gridfs import GridFS

bp = Blueprint("settings", __name__, url_prefix="")

# ----------------- SETTINGS -----------------
@bp.route("/settings/settings/", methods=["GET", "POST"])
@login_required
def settings():
  db = get_db()
  user_collection = db["users"]
  divisions_collection = db["divisions"]

  return render_template(
    "settings/settingsDash.html",
  )


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


# ----------------- EDIT REPORT TYPE -----------------
@bp.route("/settings/reportType/edit/<reportTypeID>", methods=["GET", "POST"])
@login_required
def editReportType(reportTypeID=None):
  db = get_db()
  report_collection = db["reportType"]
  documents_collection = db["documents"]

  reportTypeDetails = report_collection.find_one({"_id": ObjectId(reportTypeID)})

  if request.method == "POST":
    reportTypeName = request.form["report_type_name"]

    # Update report type name
    try:
      report_collection.update_one(
        { "_id": ObjectId(reportTypeID) },
        {
          "$set": {
            "name": reportTypeName
          }
        }
      )
      session["toastMessage"] = "Report Type updated successfully"
      session["toastMessageCategory"] = "Success"

      # Update all documents with the previous report type name
      if reportTypeDetails["isSubReportType"] == False:
        documents_collection.update_many(
          { "reportTypeID": ObjectId(reportTypeID) },
          {
            "$set": {
              "reportType": reportTypeName
            }
          }
        )
      else:
        documents_collection.update_many(
          { "subReportTypeID": ObjectId(reportTypeID) },
          {
            "$set": {
              "subReportType": reportTypeName
            }
          }
        )

      # Log Action
      log_action(
        action="report_type_updated",
        user_id=session["user_id"],
        details={
          "reportTypeID": ObjectId(reportTypeID),
          "oldReportTypeName": reportTypeDetails["name"],
          "reportTypeName": reportTypeName
        },
        division_id=session["userDivisionID"],
        comment="Report Type Updated"
      )

      session["toastMessage"] = "Report Type updated successfully"
      session["toastMessageCategory"] = "Success"

      return redirect(url_for("settings.reportType"))
    except:
      print("Couldn't update report type")

  return render_template(
    "settings/editReportType.html",
    reportTypeID = reportTypeID,
    reportTypeDetails = reportTypeDetails,
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


# ----------------- PROFILE SETTINGS -----------------
@bp.route("/settings/profile/", methods=["GET", "POST"])
@login_required
def profile():
  db = get_db()
  user_collection = db["users"]

  userDetails = user_collection.find_one(
    {"_id": ObjectId(session["user_id"])},
    {
      "username": 1,
      "email": 1,
      "division": 1,
      "isAdmin": 1,
      "hasAdminAccount": 1,
      "created_at": 1,
      "profile_picture": 1,
      "adminAccount": 1,
    }
  )

  adminAccountDetails = None
  if userDetails["hasAdminAccount"]:
    adminAccountDetails = user_collection.find_one(
      {"_id": ObjectId(userDetails["adminAccount"])},
      {
        "username": 1,
        "email": 1,
        "division": 1,
        "isAdmin": 1,
        "hasAdminAccount": 1,
        "created_at": 1,
        "profile_picture": 1,
      }
    )

  # Checking if the user has a profile picture 
  profilePictureExists = False

  if userDetails.get('profile_picture', None) is not None:
    profilePictureExists = True
  else:
    profilePictureExists = False

  if request.method == "POST":
    db = get_db()
    fs = gridfs.GridFS(db)
    user_collection = db["users"]
    profile_picture_upload = request.files["profile_picture"]

    gridfs_id = fs.put(
      profile_picture_upload, 
      filename=secure_filename(profile_picture_upload.filename), 
      contentType=profile_picture_upload.content_type
    )

    user_collection.update_one(
      { "_id": ObjectId(session["user_id"]) },
      {
        "$set": {
          "profile_picture": {
            "gridfs_id": gridfs_id,
            "filename": secure_filename(profile_picture_upload.filename),
            "contentType": profile_picture_upload.content_type
          }
        }
      }
    )

    # Log Action
    log_action(
      action="profile_picture_uploaded",
      user_id=session["user_id"],
      details={
        "profile_picture_filename": secure_filename(profile_picture_upload.filename),
        "profile_picture_contentType": profile_picture_upload.content_type
      },
      division_id=session["userDivisionID"],
      comment="Profile Picture Uploaded"
    )

    session["toastMessage"] = "Profile Picture uploaded successfully"
    session["toastMessageCategory"] = "Success"

    session["profilePictureExists"] = True
    session["profilePictureID"] = str(gridfs_id)

    return redirect(url_for("settings.profile"))
    
  return render_template(
    "settings/settingsProfile.html",
    userDetails = userDetails,
    adminAccountDetails = adminAccountDetails,
    profilePictureExists = profilePictureExists,
  )


# ----------------- SERVE PROFILE PICTURE -----------------
@bp.route('/profile_picture/<string:file_id>')
def serve_profile_picture(file_id):
    fs = GridFS(get_db())
    try:
        # Get the image from GridFS
        file = fs.get(ObjectId(file_id))
        return Response(file.read(), content_type=file.content_type)
    except:
        # Return a default image if the file is not found
        return Response(open('static/default_profile.png', 'rb').read(), content_type='image/png')
    
# ----------------- SLIDE SHOW IMAGES -----------------
@bp.route("/settings/slideshowImages/", methods=["GET", "POST"])
@login_required
def slideshow_images():
  db = get_db()
  slideshow_collection = db["slideshowImages"]

  # SLIDESHOW IMAGES WITH THE NAME OF THE UPLOADER
  slideshowImagesList = list(
    slideshow_collection.aggregate([
      {
        "$match": {

        }
      },
      {
        "$lookup": {
          "from": "users",
          "localField": "uploaded_by",
          "foreignField": "_id",
          "as": "uploadedByDetails"
        }
      },
      {
        "$addFields": {
          "uploadedBy": {
            "$arrayElemAt": ["$uploadedByDetails.username", 0]
          }
        }
      },
      {
        "$project": {
          "uploadedByDetails": 0
        }
      },
      { "$sort": {"uploadedAt": -1} }
    ])
  )

  slideshowImagesListLen = len(slideshowImagesList)

  print(slideshowImagesList)

  if request.method == "POST":
    db = get_db()
    fs = gridfs.GridFS(db)
    slideshow_image_upload = request.files["slideshow_image"]

    gridfs_id = fs.put(
      slideshow_image_upload, 
      filename=secure_filename(slideshow_image_upload.filename), 
      contentType=slideshow_image_upload.content_type
    )

    document_metadata = {
      "gridfs_id": gridfs_id,
      "filename": secure_filename(slideshow_image_upload.filename),
      "contentType": slideshow_image_upload.content_type,
      "uploaded_by": ObjectId(session["user_id"]),
      "divisionID": ObjectId(session["userDivisionID"]),
      "uploadedAt": datetime.datetime.now(),
    }

    try:
      insertedSlideshowImage = slideshow_collection.insert_one(document_metadata)
      session["toastMessage"] = "Slideshow Image uploaded successfully"
      session["toastMessageCategory"] = "Success"

      # Log Action
      log_action(
        action="slideshow_image_uploaded",
        user_id=session["user_id"],
        details={
          "slideshow_image_filename": secure_filename(slideshow_image_upload.filename),
          "slideshow_image_contentType": slideshow_image_upload.content_type
        },
        division_id=session["userDivisionID"],
        comment="Slideshow Image Uploaded"
      )

      return redirect(url_for("settings.slideshow_images"))
    except:
      print("Couldn't upload slideshow image")

  return render_template(
    "settings/slideshowImages.html",
    slideshowImagesList = slideshowImagesList,
    slideshowImagesListLen = slideshowImagesListLen,
  )

# ----------------- DELETE SLIDESHOW IMAGE -----------------
@bp.route("slideshow_image/delete/<slideshowImageID>")
def delete_slideshow_image(slideshowImageID):
  db = get_db()
  slideshow_collection = db["slideshowImages"]

  slideshowImageDetails = slideshow_collection.find_one({"_id": ObjectId(slideshowImageID)})

  try:
    slideshow_collection.delete_one({"_id": ObjectId(slideshowImageID)})

    # Log Action
    log_action(
      action="slideshow_image_deleted",
      user_id=session["user_id"],
      details={
        "slideshowImageID": ObjectId(slideshowImageID),
        "slideshowImageFilename": slideshowImageDetails["filename"]
      },
      division_id=session["userDivisionID"],
      comment="Slideshow Image Deleted"
    )

    session["toastMessage"] = "Slideshow Image deleted successfully"
    session["toastMessageCategory"] = "Success"
  except:
    print("Couldn't delete slideshow image")

  return redirect(url_for("settings.slideshow_images"))
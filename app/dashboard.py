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
import pymongo
from database import get_db
from bson.objectid import ObjectId

import gridfs
from gridfs import GridFS

bp = Blueprint("dashboard", __name__, url_prefix="")

@bp.route("/home")
@login_required
def home():
  backPageUrl = "dashboard.home"
  isAdmin = session["isAdmin"]

  try:
    if session["toastMessage"] != "":
      flash(session["toastMessage"], "Success")
      print("Toast Message sent")
      session["toastMessage"] = ""
  except:
    pass

  db = get_db()
  document_collection = db["documents"]
  user_collection = db["users"]
  searchHistory_collection = db["searchHistory"]
  divisions_collection = db["divisions"]
  slideshows_collection = db["slideshowImages"]

  # SLIDESHOW IMAGES
  slideshowImages = list(slideshows_collection.find({}))
  slideshowImagesLen = len(slideshowImages)

  # SEARCH HISTORY
  searchHistory = list(
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
      {
        "$sort": {
          "timestamp": -1
        }
      },
      {
        "$limit": 5
      }
    ])
  )

  # PAST UPLOADS
  pastUploads_limit = 5 # No. of documents to show
  pastUploads = list(
    document_collection
    .find({"uploadedBy" : ObjectId(session["user_id"])})
    .sort({"uploaded_at": -1})
    .limit(pastUploads_limit)
  )

  # DIVISION ANALYTICS
  division_wind_tunnel = divisions_collection.find_one(
      {
        "name": "WT"
      }
  )

  division_hstt = divisions_collection.find_one(
    {
      "name": "HSTT"
    }
  )

  division_smb = divisions_collection.find_one(
    {
      "name": "SMB"
    }
  )

  division_ct = divisions_collection.find_one(
    {
      "name": "CT"
    }
  )

  division_cfd = divisions_collection.find_one(
    {
      "name": "CFD"
    }
  )

  division_lct = divisions_collection.find_one(
    {
      "name": "LCT"
    }
  )

  # Chart Details
  # Get the current month
  all_months_alphabet = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  current_month = datetime.datetime.now().month
  current_year = datetime.datetime.now().year + 1
  months = []
  for i in range(5):
    if current_month == 0:
      current_month = 12
      current_year -= 1
    months.append(current_month)
    current_month -= 1
  months.reverse()

  chosen_months_alphabet = []
  for m in months:
    chosen_months_alphabet.append(all_months_alphabet[m - 1])


  # Generate a count of documents uploaded in the past 5 months for Wind Tunnel Division
  wind_tunnel_monthly_uploads = []
  for month in months:
    wind_tunnel_monthly_uploads.append(
      document_collection.count_documents(
        {
          "divisionID": ObjectId(division_wind_tunnel["_id"]),
          "uploaded_at": {
            "$gte": datetime.datetime(current_year, month, 1),
            "$lt": datetime.datetime(current_year, month, 28)
          }
        }
      )
    )
  print(current_year, months, wind_tunnel_monthly_uploads)


  # LATEST GLOBAL UPLOADS
  latestGlobalUploads = list(
    document_collection
    .find({"divisionID": ObjectId(session["userDivisionID"])})
    .sort({"uploaded_at": -1})
    .limit(5)
  )


  return render_template(
    "home/dashboard.html",
    backPageUrl = backPageUrl,
    slideshowImages = slideshowImages,
    slideshowImagesLen = slideshowImagesLen,
    isAdmin = isAdmin,
    searchHistory = searchHistory,
    pastUploads = pastUploads,
    division_wind_tunnel = division_wind_tunnel,
    division_hstt = division_hstt,
    division_smb = division_smb,
    division_ct = division_ct,
    division_cfd = division_cfd,
    division_lct = division_lct,
    latestGlobalUploads = latestGlobalUploads,
    chosen_months_alphabet = chosen_months_alphabet,
    months = months,
    wind_tunnel_monthly_uploads = wind_tunnel_monthly_uploads
  )

@bp.route("slideshowImages/get/<string:file_id>")
@login_required
def serve_slideshow_images(file_id):
  fs = GridFS(get_db())
  try:
      # Get the image from GridFS
      file = fs.get(ObjectId(file_id))
      return Response(file.read(), content_type=file.content_type)
  except:
      # Return a default image if the file is not found
      return Response(open('static/default_profile.png', 'rb').read(), content_type='image/png')
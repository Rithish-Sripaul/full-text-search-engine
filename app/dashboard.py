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
  isMaster = session["isMaster"]

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
  report_type_collection = db["reportType"]

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

  # Get the sum of all common_document_count from all divisions
  total_common_document_count = 0
  for division in divisions_collection.find({}):
    total_common_document_count += division["common_document_count"]


  # Chart Details
  # Get the current month
  import datetime
  import calendar

  all_months_alphabet = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  current_month = datetime.datetime.now().month
  current_year = datetime.datetime.now().year
  months_with_years = []

  # Get the last 5 months along with their corresponding years
  for i in range(12):
      if current_month < 1:
          current_month = 12
          current_year -= 1
      months_with_years.append((current_month, current_year))
      current_month -= 1

  # Reverse to maintain chronological order
  months_with_years.reverse()

  chosen_months_alphabet = []
  for m, y in months_with_years:
      chosen_months_alphabet.append(all_months_alphabet[m - 1])

  # Step 1: Get all non-common reportType IDs
  non_common_report_type_ids = [
      rt["_id"] for rt in report_type_collection.find(
          {"isCommonToAllDivisions": {"$ne": True}},
          {"_id": 1}
      )
  ]

  # Step 2: Count documents excluding common report types
  wind_tunnel_monthly_uploads = []
  for month, year in months_with_years:
      last_day = calendar.monthrange(year, month)[1]
      wind_tunnel_monthly_uploads.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_wind_tunnel["_id"]),
                  "reportTypeID": {"$in": non_common_report_type_ids},
                  "uploaded_at": {
                      "$gte": datetime.datetime(year, month, 1),
                      "$lt": datetime.datetime(year, month, last_day)
                  }
              }
          )
      )

  # Get the total number of documents uploaded in the past 5 months for CFD
  cfd_monthly_uploads = []
  for month, year in months_with_years:
      last_day = calendar.monthrange(year, month)[1]
      cfd_monthly_uploads.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_cfd["_id"]),
                  "reportTypeID": {"$in": non_common_report_type_ids},
                  "uploaded_at": {
                      "$gte": datetime.datetime(year, month, 1),
                      "$lt": datetime.datetime(year, month, last_day)
                  }
              }
          )
      )

  # Get the total number of documents uploaded in the past 5 months for LCT
  lct_monthly_uploads = []
  for month, year in months_with_years:
      last_day = calendar.monthrange(year, month)[1]
      lct_monthly_uploads.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_lct["_id"]),
                  "reportTypeID": {"$in": non_common_report_type_ids},
                  "uploaded_at": {
                      "$gte": datetime.datetime(year, month, 1),
                      "$lt": datetime.datetime(year, month, last_day)
                  }
              }
          )
      )

  # Get the total number of documents uploaded in the past 5 months for CT
  ct_monthly_uploads = []
  for month, year in months_with_years:
      last_day = calendar.monthrange(year, month)[1]
      ct_monthly_uploads.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_ct["_id"]),
                  "reportTypeID": {"$in": non_common_report_type_ids},
                  "uploaded_at": {
                      "$gte": datetime.datetime(year, month, 1),
                      "$lt": datetime.datetime(year, month, last_day)
                  }
              }
          )
      )

  # Get the total number of documents uploaded in the past 5 months for SMB
  smb_monthly_uploads = []
  for month, year in months_with_years:
      last_day = calendar.monthrange(year, month)[1]
      smb_monthly_uploads.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_smb["_id"]),
                  "reportTypeID": {"$in": non_common_report_type_ids},
                  "uploaded_at": {
                      "$gte": datetime.datetime(year, month, 1),
                      "$lt": datetime.datetime(year, month, last_day)
                  }
              }
          )
      )

  # Get the total number of documents uploaded in the past 5 months for HSTT
  hstt_monthly_uploads = []
  for month, year in months_with_years:
      last_day = calendar.monthrange(year, month)[1]
      hstt_monthly_uploads.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_hstt["_id"]),
                  "reportTypeID": {"$in": non_common_report_type_ids},
                  "uploaded_at": {
                      "$gte": datetime.datetime(year, month, 1),
                      "$lt": datetime.datetime(year, month, last_day)
                  }
              }
          )
      )

  # UPLOADED YEAR GRAPH
  # Year Ranges
  year_ranges = [
      (2020, 2025),
      (2010, 2020),
      (2000, 2010),
      (1990, 2000),
      (1980, 1990),
      (1970, 1980),
  ]

  choosen_years = []
  for start_year, end_year in year_ranges:
      choosen_years.append(f"{start_year} - {end_year}")

  # Count documents for each year range 
  # WIND TUNNEL
  wt_uploads_by_year = []
  for start_year, end_year in year_ranges:
      wt_uploads_by_year.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_wind_tunnel["_id"]),                 
                  "year": {
                      "$gte": start_year,
                      "$lt": end_year
                  },
                  "reportTypeID": {"$in": non_common_report_type_ids}
              }
          )
      )

  # CFD
  cfd_uploads_by_year = []
  for start_year, end_year in year_ranges:
      cfd_uploads_by_year.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_cfd["_id"]),
                  "year": {
                      "$gte": start_year,
                      "$lt": end_year
                  },
                  "reportTypeID": {"$in": non_common_report_type_ids}
              }
          )
      )
  
  # LCT
  lct_uploads_by_year = []
  for start_year, end_year in year_ranges:
      lct_uploads_by_year.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_lct["_id"]),
                  "year": {
                      "$gte": start_year,
                      "$lt": end_year
                  },
                  "reportTypeID": {"$in": non_common_report_type_ids}
              }
          )
      )
  
  # CT
  ct_uploads_by_year = []
  for start_year, end_year in year_ranges:
      ct_uploads_by_year.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_ct["_id"]),
                  "year": {
                      "$gte": start_year,
                      "$lt": end_year
                  },
                  "reportTypeID": {"$in": non_common_report_type_ids}
              }
          )
      )
  
  # SMB
  smb_uploads_by_year = []
  for start_year, end_year in year_ranges:
      smb_uploads_by_year.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_smb["_id"]),
                  "year": {
                      "$gte": start_year,
                      "$lt": end_year
                  },
                  "reportTypeID": {"$in": non_common_report_type_ids}
              }
          )
      )
  
  # HSTT
  hstt_uploads_by_year = []
  for start_year, end_year in year_ranges:
      hstt_uploads_by_year.append(
          document_collection.count_documents(
              {
                  "divisionID": ObjectId(division_hstt["_id"]),
                  "year": {
                      "$gte": start_year,
                      "$lt": end_year
                  },
                  "reportTypeID": {"$in": non_common_report_type_ids}
              }
          )
      )
  
  # Reverse all the year lists to maintain chronological order
  wt_uploads_by_year.reverse()
  cfd_uploads_by_year.reverse()
  lct_uploads_by_year.reverse()
  ct_uploads_by_year.reverse()
  smb_uploads_by_year.reverse()
  hstt_uploads_by_year.reverse()
  choosen_years.reverse()
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
    isMaster = isMaster,
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
    wind_tunnel_monthly_uploads = wind_tunnel_monthly_uploads,
    cfd_monthly_uploads = cfd_monthly_uploads,
    lct_monthly_uploads = lct_monthly_uploads,
    ct_monthly_uploads = ct_monthly_uploads,
    smb_monthly_uploads = smb_monthly_uploads,
    hstt_monthly_uploads = hstt_monthly_uploads,
    total_common_document_count = total_common_document_count,
    wt_uploads_by_year = wt_uploads_by_year,
    cfd_uploads_by_year = cfd_uploads_by_year,
    lct_uploads_by_year = lct_uploads_by_year,
    ct_uploads_by_year = ct_uploads_by_year,
    smb_uploads_by_year = smb_uploads_by_year,
    hstt_uploads_by_year = hstt_uploads_by_year,
    choosen_years = choosen_years
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
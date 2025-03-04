import os
import datetime
import math
from flask import render_template, redirect, request, url_for, Blueprint, flash, session, make_response, Response, jsonify
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

  hstt_monthly_uploads = []
  wind_tunnel_monthly_uploads = []
  cfd_monthly_uploads = []
  lct_monthly_uploads = []
  ct_monthly_uploads = []
  smb_monthly_uploads = []

  for month, year in months_with_years:
    # Calculate the first day of the next month
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    # Count documents for HSTT
    hstt_monthly_uploads.append(
        document_collection.count_documents(
            {
                "divisionID": ObjectId(division_hstt["_id"]),
                "reportTypeID": {"$in": non_common_report_type_ids},
                "uploaded_at": {
                    "$gte": datetime.datetime(year, month, 1),
                    "$lt": datetime.datetime(next_year, next_month, 1)
                }
            }
        )
    )

    # Count documents for Wind Tunnel
    wind_tunnel_monthly_uploads.append(
        document_collection.count_documents(
            {
                "divisionID": ObjectId(division_wind_tunnel["_id"]),
                "reportTypeID": {"$in": non_common_report_type_ids},
                "uploaded_at": {
                    "$gte": datetime.datetime(year, month, 1),
                    "$lt": datetime.datetime(next_year, next_month, 1)
                }
            }
        )
    )

    # Count documents for CFD
    cfd_monthly_uploads.append(
        document_collection.count_documents(
            {
                "divisionID": ObjectId(division_cfd["_id"]),
                "reportTypeID": {"$in": non_common_report_type_ids},
                "uploaded_at": {
                    "$gte": datetime.datetime(year, month, 1),
                    "$lt": datetime.datetime(next_year, next_month, 1)
                }
            }
        )
    )

    # Count documents for LCT
    lct_monthly_uploads.append(
        document_collection.count_documents(
            {
                "divisionID": ObjectId(division_lct["_id"]),
                "reportTypeID": {"$in": non_common_report_type_ids},
                "uploaded_at": {
                    "$gte": datetime.datetime(year, month, 1),
                    "$lt": datetime.datetime(next_year, next_month, 1)
                }
            }
        )
    )

    # Count documents for CT
    ct_monthly_uploads.append(
        document_collection.count_documents(
            {
                "divisionID": ObjectId(division_ct["_id"]),
                "reportTypeID": {"$in": non_common_report_type_ids},
                "uploaded_at": {
                    "$gte": datetime.datetime(year, month, 1),
                    "$lt": datetime.datetime(next_year, next_month, 1)
                }
            }
        )
    )

    # Count documents for SMB
    smb_monthly_uploads.append(
        document_collection.count_documents(
            {
                "divisionID": ObjectId(division_smb["_id"]),
                "reportTypeID": {"$in": non_common_report_type_ids},
                "uploaded_at": {
                    "$gte": datetime.datetime(year, month, 1),
                    "$lt": datetime.datetime(next_year, next_month, 1)
                }
            }
        )
    )

    print(datetime.datetime(year, month, 1))
    print(datetime.datetime(next_year, next_month, 1))




  # UPLOADED YEAR GRAPH
  # Year Ranges
  year_ranges = [
      (2020, 2025),
      (2010, 2020),
      (2000, 2010),
      (1990, 2000),
      (1980, 1990),
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
                      "$gt": start_year,
                      "$lte": end_year
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
                      "$gt": start_year,
                      "$lte": end_year
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
                      "$gt": start_year,
                      "$lte": end_year
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
                      "$gt": start_year,
                      "$lte": end_year
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
                      "$gt": start_year,
                      "$lte": end_year
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
                      "$gt": start_year,
                      "$lte": end_year
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

def generate_year_ranges(start_year, end_year, interval):
    """Generates year ranges based on the given interval."""
    return [(year, year + interval) for year in range(start_year, end_year, interval)]

@bp.route("/graphYear", methods=["GET"])
@login_required
def graphYear():
    db = get_db()
    division_collection = db["divisions"]

    # Get the divisions
    division_wind_tunnel = division_collection.find_one({"name": "WT"})
    division_hstt = division_collection.find_one({"name": "HSTT"})
    division_smb = division_collection.find_one({"name": "SMB"})
    division_ct = division_collection.find_one({"name": "CT"})
    division_cfd = division_collection.find_one({"name": "CFD"})
    division_lct = division_collection.find_one({"name": "LCT"})
    document_collection = db["documents"]
    report_type_collection = db["reportType"]

      # Step 1: Get all non-common reportType IDs
    non_common_report_type_ids = [
        rt["_id"] for rt in report_type_collection.find(
            {"isCommonToAllDivisions": {"$ne": True}},
            {"_id": 1}
        )
    ]

    # Get zoom_index from request and convert to int (with a fallback default)
    zoom_index = request.args.get("zoom_index", default=0, type=int)

    # Define zoom levels
    ZOOM_LEVELS = [10, 5, 2]  # Available zoom levels

    # Validate zoom_index to prevent out-of-range errors
    if zoom_index < 0 or zoom_index >= len(ZOOM_LEVELS):
        return jsonify({"error": "Invalid zoom index"}), 400

    # Generate year ranges based on the zoom level
    start_year, end_year = 1970, 2025
    year_ranges = generate_year_ranges(start_year, end_year, ZOOM_LEVELS[zoom_index])

    # Generate labels for the graph
    if ZOOM_LEVELS[zoom_index] == 10:
        choosen_years = [f"{start}-{end}" for start, end in year_ranges]
    elif ZOOM_LEVELS[zoom_index] == 5:
        choosen_years = []
        for start, end in year_ranges:
            start_formatted = f"{start % 100:02d}"  # Ensures two-digit format (e.g., 85 instead of 1985, 05 instead of 2005)
            end_formatted = f"{end % 100:02d}"      # Same formatting for the end year
            choosen_years.append(f"{start_formatted}-{end_formatted}")
    else:
        choosen_years = []
        for start, end in year_ranges:
            start_formatted = f"{start % 100:02d}"
            choosen_years.append(f"{start_formatted}")



    def count_documents_by_year_ranges(division_id):
        """Counts documents for a given division across the generated year ranges."""
        return [
            document_collection.count_documents(
                {
                    "divisionID": ObjectId(division_id),
                    "year": {"$gt": start, "$lte": end},
                    "reportTypeID": {"$in": non_common_report_type_ids}
                }
            )
            for start, end in year_ranges
        ]

    # Generate document counts for each division
    wt_uploads_by_year = count_documents_by_year_ranges(division_wind_tunnel["_id"])
    cfd_uploads_by_year = count_documents_by_year_ranges(division_cfd["_id"])
    lct_uploads_by_year = count_documents_by_year_ranges(division_lct["_id"])
    ct_uploads_by_year = count_documents_by_year_ranges(division_ct["_id"])
    smb_uploads_by_year = count_documents_by_year_ranges(division_smb["_id"])
    hstt_uploads_by_year = count_documents_by_year_ranges(division_hstt["_id"])

    # Reverse lists to maintain chronological order
    # choosen_years.reverse()
    # wt_uploads_by_year.reverse()
    # cfd_uploads_by_year.reverse()
    # lct_uploads_by_year.reverse()
    # ct_uploads_by_year.reverse()
    # smb_uploads_by_year.reverse()
    # hstt_uploads_by_year.reverse()

    return jsonify({
        "wt_uploads_by_year": wt_uploads_by_year,
        "cfd_uploads_by_year": cfd_uploads_by_year,
        "lct_uploads_by_year": lct_uploads_by_year,
        "ct_uploads_by_year": ct_uploads_by_year,
        "smb_uploads_by_year": smb_uploads_by_year,
        "hstt_uploads_by_year": hstt_uploads_by_year,
        "choosen_years": choosen_years
    })
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
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import json_util
from bson.objectid import ObjectId

import gridfs
from gridfs import GridFS

from pypdf import PdfReader
import ocrmypdf



# ----------------- ACTION LOGS -----------------
def log_action(action, user_id, document_id=None, details=None, comment=None, division_id=None):
    db = get_db()
    action_collection = db["actionLogs"]
    user_collection = db["users"]
    action_metadata = {
        "action": action,
        "user_id": ObjectId(user_id),
        "username": user_collection.find_one({"_id": ObjectId(user_id)})["username"],
        "adminID": user_collection.find_one({"_id": ObjectId(user_id)})["adminAccount"], 
        "email": user_collection.find_one({"_id": ObjectId(user_id)})["email"],
        "divisionID": ObjectId(division_id),
        "division": user_collection.find_one({"_id": ObjectId(user_id)})["division"],
        "documentID": ObjectId(document_id),
        "details": details,
        "comment": comment,
        "timestamp": datetime.datetime.now(),
    }
    action_collection.insert_one(action_metadata)
    return True
from flask import g, render_template, redirect, request, url_for, Blueprint, flash, session
from flask_login import (
    current_user,
    login_user,
    logout_user
)
import datetime
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import functools
from helper import log_action

bp = Blueprint("authentication", __name__, url_prefix='')
@bp.route('/')
def route_default():
    return redirect(url_for('authentication.login'))


# Login
@bp.route("/login/", methods=["GET", "POST"])
def login():
    session["number_of_documents_per_page"] = 10
    backPageUrl = "authentication.login"

    try:
        if session["toastMessage"] != "":
            flash(session["toastMessage"], session["toastMessageCategory"])
            print("Toast Message sent")
            session["toastMessage"] = ""
            session["toastMessageCategory"] = ""
    except:
        pass

    if g.user is not None:
        return redirect(url_for("dashboard.home"))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        user_collection = db["users"]
        division_collection = db["divisions"]
        error = None
        
        user = user_collection.find_one({"username": username})
        
        if user is None:
            error = "No user found"
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password"
        
        if error is not None:
            print("something wrong")
            session["toastMessage"] = "Incorrect username or password"
            session["toastMessageCategory"] = "Alert"
            return redirect(url_for("authentication.login"))

        if error is None:
            session.clear()
            session["user_id"] = str(user["_id"])
            session["username"] = username
            session["number_of_documents_per_page"] = 10
            session["logged_in"] = True
            session["isAdmin"] = user["isAdmin"]
            session["isMaster"] = user["isMaster"]
            session["userDivisionID"] = str(division_collection.find_one({"name": user["division"]})["_id"])
            session["userDivision"] = user["division"]
            session["toastMessage"] = "You have logged in Successfully"
            session["profilePictureExists"] = False
            if user.get("profile_picture", None) is not None:
                session["profilePictureExists"] = True
            
            session["profilePictureID"] = None
            if session["profilePictureExists"]:
                session["profilePictureID"] = str(user["profile_picture"]["gridfs_id"])

            log_action(
                action="login",
                user_id=ObjectId(session["user_id"]),
                document_id=None,
                division_id=str(division_collection.find_one({"name": user["division"]})["_id"]),
                comment=None
            )
            return redirect(url_for("dashboard.home"))

    return render_template("accounts/login.html")


# Logout
@bp.route("/logout/", methods=["GET", "POST"])
def logout():
    backPageUrl = "authentication.login"
    db = get_db()
    division_collection = db["divisions"]
    user_collection = db["users"]

    # Log the action    
    user = user_collection.find_one({"_id": ObjectId(session["user_id"])})
    log_action(
        action="logout",
        user_id=session["user_id"],
        document_id=None,
        division_id=str(division_collection.find_one({"name": user["division"]})["_id"]),
        comment=None
    )

    session.clear()
    session["toastMessage"] = "You have logged out Successfully"
    session["toastMessageCategory"] = "Success"
    g.user = None
    return redirect(url_for("authentication.login"))

# Checks if a user is logged in
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("authentication.login"))
        return view(**kwargs)
    return wrapped_view

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = user_id

# Registration
@bp.route("/register", methods=["GET", "POST"])
def register():
    db = get_db()
    user_collection = db["users"]
    division_collection = db["divisions"]

    divisionList = division_collection.find({})

    allUsers = list(user_collection.find({"isAdmin": True}))

    # Toast Message
    try:
        if session["toastMessage"] != "":
            flash(session["toastMessage"], session["toastMessageCategory"])
            print("Toast Message sent")
            session["toastMessage"] = ""
            session["toastMessageCategory"] = ""
    except:
        pass

    if request.method == "POST":
        db = get_db()
        user_collection = db["users"]
        division_collection = db["divisions"]

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        division = request.form["division"]
        isAdmin = request.form["isAdmin"]
        isMaster = False
        divisionID = division_collection.find_one({"name": division})["_id"]

        hasAdminAccount = True if request.form["hasAdminAccount"] == "1" else False
        if hasAdminAccount:
            adminAccount = request.form["adminAccount"]
        else:
            adminAccount = None
        isAdmin = True if isAdmin == "1" else False


        error = None
        if not username:
            error = "Username is required"
        elif not password:
            error = "Password is required"

        if user_collection.find_one({"username": username}):
            error = "User with username already exists."
        elif user_collection.find_one({"email": email}):
            error = "User with email already exists."
        if error is not None:
            session["toastMessage"] = error
            session["toastMessageCategory"] = "Alert"
            return redirect(url_for("authentication.register"))
        else:
            session["toastMessage"] = "User created successfully"
            session["toastMessageCategory"] = "Success"
            
        if error is None:
            if hasAdminAccount:
                insertedUser = user_collection.insert_one(
                    {
                        "username": username, 
                        "email": email, 
                        "password": generate_password_hash(password),
                        "division": division,
                        "isMaster": isMaster,
                        "isAdmin": isAdmin,
                        "hasAdminAccount": hasAdminAccount,
                        "adminAccount": ObjectId(adminAccount),
                        "created_at": datetime.datetime.now()
                    }
                )
                user_id = insertedUser.inserted_id
                division_collection.update_one(
                    {"name": division},
                    {
                        "$inc": {
                            "userCount": 1
                        }
                    }
                )

                # Log Action
                log_action(
                    action="user_created",
                    user_id=user_id,
                    division_id=divisionID,
                    comment="User Created",
                    details={
                        "username": username,
                        "email": email,
                        "division": division,
                        "isMaster": isMaster,
                        "isAdmin": isAdmin,
                        "hasAdminAccount": hasAdminAccount,
                        "adminAccount": ObjectId(adminAccount),
                        "created_at": datetime.datetime.now()
                    }
                )
                return redirect(url_for("authentication.login"))
            elif not hasAdminAccount:
                insertedUser = user_collection.insert_one(
                    {
                        "username": username, 
                        "email": email, 
                        "password": generate_password_hash(password),
                        "division": division,
                        "isMaster": isMaster,
                        "isAdmin": isAdmin,
                        "hasAdminAccount": hasAdminAccount,
                        "adminAccount": None,
                        "created_at": datetime.datetime.now()
                    }
                )
                user_id = insertedUser.inserted_id
                division_collection.update_one(
                    {"name": division},
                    {
                        "$inc": {
                            "userCount": 1
                        }
                    }
                )

                # Log Action
                log_action(
                    action="user_created",
                    user_id=user_id,
                    division_id=divisionID,
                    comment="User Created",
                    details={
                        "username": username,
                        "email": email,
                        "division": division,
                        "isMaster": isMaster,
                        "isAdmin": isAdmin,
                        "hasAdminAccount": hasAdminAccount,
                        "adminAccount": None,
                        "created_at": datetime.datetime.now()
                    }
                )
                return redirect(url_for("settings.settings"))

    return render_template(
        "accounts/register.html",
        allUsersLen = len(allUsers),
        allUsers = allUsers,
        divisionList = divisionList
    )


# Profile
@bp.route("/profile", methods=["GET", "POST"])
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

  return render_template(
    "accounts/profile.html",
    userDetails = userDetails,
    adminAccountDetails = adminAccountDetails,
    profilePictureExists = profilePictureExists,
  )

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
            session["userDivisionID"] = str(division_collection.find_one({"name": user["division"]})["_id"])
            print(session["user_id"])
            session["toastMessage"] = "You have logged in Successfully"
            return redirect(url_for("dashboard.home"))

    return render_template("accounts/login.html")


# Logout
@bp.route("/logout/", methods=["GET", "POST"])
def logout():
    backPageUrl = "authentication.login"
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
                user_collection.insert_one(
                    {
                        "username": username, 
                        "email": email, 
                        "password": generate_password_hash(password),
                        "division": division,
                        "isAdmin": isAdmin,
                        "hasAdminAccount": hasAdminAccount,
                        "adminAccount": ObjectId(adminAccount),
                        "created_at": datetime.datetime.now()
                    }
                )
                division_collection.update_one(
                    {"name": division},
                    {
                        "$inc": {
                            "userCount": 1
                        }
                    }
                )
                return redirect(url_for("authentication.login"))
            elif not hasAdminAccount:
                user_collection.insert_one(
                    {
                        "username": username, 
                        "email": email, 
                        "password": generate_password_hash(password),
                        "division": division,
                        "isAdmin": isAdmin,
                        "hasAdminAccount": hasAdminAccount,
                        "adminAccount": None
                    }
                )
                division_collection.update_one(
                    {"name": division},
                    {
                        "$inc": {
                            "userCount": 1
                        }
                    }
                )
                return redirect(url_for("authentication.login"))

    return render_template(
        "accounts/register.html",
        allUsersLen = len(allUsers),
        allUsers = allUsers,
        divisionList = divisionList
    )
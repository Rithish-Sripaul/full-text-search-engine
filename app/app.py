import os   
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask import render_template, send_file, redirect, request, url_for, Blueprint, flash, session, make_response
from flask_login import (
    current_user,
    login_user,
    logout_user
)
app = Flask(__name__)

# app.config["MONGO_URI"] = 'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_DATABASE']

app.config["MONGO_URI"] = "mongodb://mongo:27017/dev"
app.config.from_mapping(SECRET_KEY="dev")

mongo = PyMongo(app)
db = mongo.db

@app.route("/")
def index():
    return redirect(url_for("authentication.login"))

def register_blueprints(app):
    import authentication
    import documents
    import documentApproval
    import settings
    import dashboard
    app.register_blueprint(authentication.bp)
    app.register_blueprint(documents.bp)
    app.register_blueprint(documentApproval.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(dashboard.bp)

def create_ocr_ditectory():
    directory_path = "./converted_pdf"
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print("Directory created")
    else:
        print("Directory already exists")

register_blueprints(app)
create_ocr_ditectory()

if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("APP_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("APP_PORT", 5000)
    app.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)
    
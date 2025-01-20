from pymongo import MongoClient
import click
from flask import current_app, g
from flask_pymongo import PyMongo


def init_db():
    db = get_db()
    

def get_db():
    if "db" not in g:
        # Docker Container
        # mongo = PyMongo(current_app)
        # g.db = mongo.db

        # Flask Development Server
        client = MongoClient(
            port=27017,
            username="admin",
            password="1234",
            authSource="testDB"
        )
        g.db = client["testDB"]
    return g.db


def close_db(e=None):
    db = g.pop("db", None)

@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database")

def init_app(app):
    app.teardown_appcontext(close_db)

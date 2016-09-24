from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config.from_object('config')

# Mongo
mongo = PyMongo(app)

from app import routes
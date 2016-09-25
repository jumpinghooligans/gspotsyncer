from flask import Flask
from flask_pymongo import PyMongo
from flask_cache import Cache

app = Flask(__name__)
app.config.from_object('config')

# Mongo
mongo = PyMongo(app)

# Memcached
cache = Cache(app)

from app import routes
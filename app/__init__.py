import os

from flask import Flask
from flask_pymongo import PyMongo
from flask_caching import Cache

app = Flask(__name__)
app.config.from_object('config')

# Mongo
mongo = PyMongo(app, os.environ.get('DB_ENV', 'MONGO'))

# Memcached
cache = Cache(app)

from app import routes
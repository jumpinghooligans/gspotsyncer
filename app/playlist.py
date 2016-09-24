from app import app, mongo, user

from flask import flash
from bson.objectid import ObjectId

import urllib, urllib2, json, time, md5


def get_playlist(id):
	return mongo.db.playlists.find_one({ '_id' : ObjectId(id) })

def get_user_playlists(user):
	cursor = mongo.db.playlists.find({
		'username' : user.username
	})

	playlists = []
	for doc in cursor:
		playlists.append(Playlist(doc))

	return playlists


class Playlist():
	def __init__(self, playlist):
		for key, value in playlist.items():
			setattr(self, key, value)

	def save(self):
		playlist = None

		if hasattr(self, '_id'):
			playlist = mongo.db.playlists.find_one({ '_id' : self._id })

		if playlist is None:
			playlist = {
				'username' : user.current_user.username
			}

		# update the mongo obj
		for var in vars(self):
			playlist[var] = getattr(self, var)

		# save to db
		return mongo.db.playlists.insert_one(dict(playlist))
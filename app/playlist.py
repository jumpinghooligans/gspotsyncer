from app import app
from flask import flash
from flask_dynamo import Dynamo

import urllib, urllib2, json, time

# db
dynamo = Dynamo(app)

class Playlist():
	def __init__(self, playlist):
		for key, value in playlist.items():
			setattr(self, key, value)

		if not hasattr(self, 'playlist_id'):
			self.playlist_id = int(round(time.time() * 1000))

	def save(self):
		playlist = dynamo.playlists.get_item(username='asdf')

		# update the dynamo obj
		for obj in vars(self):
			playlist[obj] = getattr(self, obj)

		# save to db
		return playlist.save(overwrite=True)
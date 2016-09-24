from app import app, mongo, user

from flask import flash

import urllib, urllib2, json, time


def get_playlists(u):
	return mongo.db.playlists.find({
		'username' : u.username
	})


class Playlist():
	def __init__(self, playlist):
		for key, value in playlist.items():
			setattr(self, key, value)

		if not hasattr(self, 'playlist_id'):
			self.playlist_id = int(round(time.time() * 1000))

	def save(self):
		playlist = mongo.db.playlists.find_one({ 'playlist_id' : self.playlist_id })

		if playlist is None:
			playlist = {
				'username' : user.current_user.username
			}

		# update the mongo obj
		for var in vars(self):
			playlist[var] = getattr(self, var)

		# save to db
		return mongo.db.playlists.save(dict(playlist))
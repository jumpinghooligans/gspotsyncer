from app import app, mongo, cache, gmusic, spotify

from flask import flash
from bson.objectid import ObjectId

class Track():

	def get_track(self, track=None):

		if not track:
			track = self;

		t = {}
		for var in vars(track):
			if var == 'raw_data':
				continue

			t[var] = getattr(track, var)

		return t

	def save(self):
		track = {}

		# update the mongo obj
		for var in vars(self):
			track[var] = getattr(self, var)

		# convert to dict for mongo
		track = dict(track)

		# save to mongo - insert or replace
		if '_id' in track:
			return mongo.db.tracks.replace_one({ '_id' : track['_id'] }, track)

		# its stupid this isn't handled by mongo...
		return mongo.db.tracks.insert_one(track)

	def delete(self):
		if self._id:
			return mongo.db.tracks.delete_one({ '_id' : self._id })

		return False

class SpotifyTrack(Track):

	def __init__(self, spotify_track):
		s = spotify.Spotify()

		# check if it exists
		t = self.get_existing_track(spotify_track)

		# create and save it if it doesn't
		if not t:
			t = s.format_generic_track(spotify_track)

			if t:
				for k, v in t.iteritems():
					setattr(self, k, v)

				result = self.save()
				if hasattr(result, 'inserted_id'):
					self._id = getattr(result, 'inserted_id')

	def get_existing_track(self, track):
		s = spotify.Spotify()

		track_id = s.get_track_id(track)

		# if we have a track id - check if it exists in mongo
		if track_id:
			track = mongo.db.tracks.find_one({ 'remote_track_id' : track_id })

			if track:
				return track

		return None

class GoogleTrack(Track):

	def __init__(self, google_track):
		g = gmusic.GoogleMusic()

		t = g.format_generic_track(google_track)

		for k, v in t:
			app.logger.info(k)
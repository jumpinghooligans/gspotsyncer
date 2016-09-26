from app import app, mongo, cache, user, gmusic, spotify

from flask import flash
from bson.objectid import ObjectId

import urllib, urllib2, json, md5

def get_user_playlists(user):
	cursor = mongo.db.playlists.find({
		'user_id' : user._id
	})

	playlists = []
	for doc in cursor:
		playlists.append(Playlist(doc))

	return playlists


class Playlist():
	def __init__(self, playlist):
		if type(playlist) is str:
			playlist = mongo.db.playlists.find_one({ '_id' : ObjectId(playlist) })

		if not playlist:
			playlist = {}

		for key, value in playlist.items():
			setattr(self, key, value)

	# def process(self, actions = {}, save = True):
	# 	results = {}
	# 	for action, params in actions.iteritems():
	# 		if hasattr(self, action):
	# 			func = getattr(self, action)
	# 			results[action] = func(params)

	# 	if save:
	# 		results['save'] = self.save()

	# 	return results

	def publish_tracks(self):

		# if masterslave
			# clear slaves track cache
			# get_tracks
			#
			# find tracks in get_tracks not on self.tracks
			# 	delete them
			# find tracks in self.tracks not on get_tracks
			# 	add them

		u = user.User(str(self.user_id))

		service = None
		g = gmusic.GoogleMusic(u)
		s = spotify.Spotify(u)

		if self.type == 'masterslave':
			# todo: clear cache

			# remote_track_ids - what currently exists and what we're going to edit
			# with whats in self.tracks.{{service}}_ids

			if self.master == 'spotify':
				remote_track_ids = self.get_track_ids(self.google_tracks, 'google')
				local_track_ids = self.get_track_ids(self.tracks, 'generic_google')
				service = g

			if self.master == 'google':
				remote_track_ids = self.get_track_ids(self.spotify_tracks, 'spotify')
				local_track_ids = self.get_track_ids(self.tracks, 'generic_spotify')
				service = s

			# as long as we have something to do
			if local_track_ids:
				# delete, whats on the remote and not in local
				delete_ids = list(set(remote_track_ids) - set(local_track_ids))

				# insert whats in local and not on the remote
				insert_ids = list(set(local_track_ids) - set(remote_track_ids))

				service.playlist_remove(self, delete_ids)
				service.playlist_add(self, insert_ids)

		return False

	def find_missing_tracks(self):
		if not self.tracks:
			return False

		u = user.User(str(self.user_id))

		g = gmusic.GoogleMusic(u)
		s = spotify.Spotify(u)

		for idx, track in enumerate(self.tracks):
			query = track['title'] + ' ' + track['artists'][0]['name'] + ' ' + track['album']['name']

			if not track['google_id']:
				matching_tracks = g.search_songs(query)

				# real dumb right now
				if matching_tracks:
					self.tracks[idx]['google_id'] = matching_tracks[0]['track']['nid']

			if not track['spotify_id']:
				app.logger.info('Search for spotify track')

		return True

	def get_track_ids(self, tracks, service):
		# Id location varies by service...
		track_ids = []
		for track in tracks:
			if service == 'spotify':
				# spotify n.track.id
				track_ids.append(track['track']['id'])

			if service == 'google':
				track_ids.append(track['trackId'])

			if service == 'generic_spotify':
				# generic_spotify n.spotify_id - these can be None
				if track['spotify_id']:
					track_ids.append(track['spotify_id'])

			if service == 'generic_google':
				# generic_google n.google_id
				if track['google_id']:
					track_ids.append(track['google_id'])

		return track_ids

	def refresh_external_tracks(self):
		u = user.User(str(self.user_id))

		g = gmusic.GoogleMusic(u)
		s = spotify.Spotify(u)

		self.spotify_tracks = s.get_tracks(self.spotify_playlist_data)
		self.google_tracks = g.get_tracks(self.google_playlist_data)

	def generate_track_list(self):
		if self.type == 'masterslave':
			# build a track list
			if self.master == 'spotify':
				self.tracks = self.build_tracks(self.spotify_tracks, 'spotify')

			if self.master == 'google':
				self.tracks = self.build_tracks(self.google_tracks, 'google')

			return True

		return False

	def build_tracks(self, new_tracks, service):
		service_api = None
		u = user.User(str(self.user_id))

		if service == 'google':
			service_api = gmusic.GoogleMusic(u)

		if service == 'spotify':
			service_api = spotify.Spotify(u)

		existing_tracks = []
		if hasattr(self, 'tracks'):
			existing_tracks = self.tracks

		formatted_tracks = []
		if service_api:
			for track in new_tracks:
				formatted_tracks.append(service_api.format_generic_track(track, existing_tracks))

		return formatted_tracks

	def save(self):
		playlist = {}

		# update the mongo obj
		for var in vars(self):
			playlist[var] = getattr(self, var)

		# convert to dict for mongo
		playlist = dict(playlist)

		# save to mongo - insert or replace
		if '_id' in playlist:
			return mongo.db.playlists.replace_one({ '_id' : playlist['_id'] }, playlist)

		# its stupid this isn't handled by mongo...
		return mongo.db.playlists.insert_one(playlist)
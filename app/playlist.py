from app import app, mongo, cache, user, gmusic, spotify
from track import Track, SpotifyTrack, GoogleTrack

from flask import flash
from bson.objectid import ObjectId
from random import shuffle

import urllib, json, md5, re, time

def get_user_playlists(user):
	cursor = mongo.db.playlists.find({
		'user_id' : user._id
	}).sort([
		('last_published', -1),
		('last_refreshed', -1),
		('created', -1)
	])

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

		# some defaults
		setattr(self, 'tracks', [])
		setattr(self, 'spotify_tracks', [])
		setattr(self, 'google_tracks', [])
		setattr(self, 'remote_spotify_tracks', [])
		setattr(self, 'remote_google_tracks', [])

		# override them if we have values
		for key, value in playlist.items():
			setattr(self, key, value)

	def publish_tracks(self):
		u = user.User(str(self.user_id))

		service = None
		g = gmusic.GoogleMusic(u)
		s = spotify.Spotify(u)

		if self.type == 'masterslave':
			# todo: clear cache

			# remote_track_ids - what currently exists and what we're going to edit
			# with whats in self.tracks.{{service}}_ids

			if self.master == 'spotify':
				slave = 'google'
				service = g

			if self.master == 'google':
				slave = 'spotify'
				service = s

			remote_track_ids = self.get_track_ids(getattr(self, slave + '_tracks'), slave)
			local_track_ids = self.get_track_ids(self.tracks, 'generic_' + slave)

			# as long as we have something to do
			if local_track_ids:

				# delete, whats on the remote and not in local
				delete_ids = list(set(remote_track_ids) - set(local_track_ids))

				# insert whats in local and not on the remote
				insert_ids = list(set(local_track_ids) - set(remote_track_ids))

				# reorder insert ids
				order_insert_ids = [ o for o in local_track_ids if o in insert_ids]

				service.playlist_remove(self, delete_ids)
				service.playlist_add(self, order_insert_ids)

				# update last published date
				self.last_published = time.strftime("%m/%d/%Y %H:%M:%S")

				return True

		return False

	def find_missing_tracks(self):
		if not self.tracks:
			return False

		u = user.User(str(self.user_id))

		g = gmusic.GoogleMusic(u)
		s = spotify.Spotify(u)

		for idx, track in enumerate(self.tracks):

			if not track['google_id']:
				matching_tracks = self.search_songs(g, track)

				# real dumb right now
				if matching_tracks:

					# make it similar to regular playlist tracks
					for t in matching_tracks:
						t['trackId'] = t['track']['nid']

					matching_track = matching_tracks.pop()

					# attach other results as 'similar' tracks
					matching_track['similar_tracks'] = matching_tracks[0:3]

					# trackId is nid in search results
					self.tracks[idx]['google_id'] = matching_track['track']['nid']

					self.google_tracks.append(matching_track)
					self.google_tracks += matching_tracks

			if not track['spotify_id']:
				matching_tracks = self.search_songs(s, track)

				# still dumb
				if matching_tracks:
					matching_track = matching_tracks.pop(0)

					matching_track['similar_tracks'] = matching_tracks[0:3]

					self.tracks[idx]['spotify_id'] = matching_track['uri']
					self.spotify_tracks.append(matching_track)
					self.spotify_tracks += matching_tracks

		return True

	def search_songs(self, service, track):
		matching_tracks = []

		title = track['title']
		primary_artist = track['artists'][0]['name']
		album = track['album']['name']

		# start complex and get more basics
		queries = []

		# base query
		base_query = ' '.join(
			(title, primary_artist, album)
		).encode('utf-8').strip()

		# simpler base query
		simple_base_query = ' '.join(
			(title, primary_artist)
		).encode('utf-8').strip()

		# split on first paren (seems to work fairly well)
		part_paren = lambda x: x.partition('(')[0]
		part_dash = lambda x: x.partition('-')[0]

		split_paren_query = ' '.join(map(
			part_paren, (title, primary_artist, album)
		)).encode('utf-8').strip()

		simple_split_paren_query = ' '.join(map(
			part_paren, (title, primary_artist)
		)).encode('utf-8').strip()
		
		split_dash_query = ' '.join(map(
			part_dash, (title, primary_artist, album)
		)).encode('utf-8').strip()

		simple_split_dash_query = ' '.join(map(
			part_dash, (title, primary_artist)
		)).encode('utf-8').strip()

		# full query, then alpha numeric only
		queries.append(base_query)
		queries.append(re.sub(r'([^\s\w]|_)+', '', base_query))

		# simple query, then alpha numeric only
		queries.append(simple_base_query)
		queries.append(re.sub(r'([^\s\w]|_)+', '', simple_base_query))

		queries.append(split_paren_query)
		queries.append(simple_split_paren_query)
		
		queries.append(split_dash_query)
		queries.append(simple_split_dash_query)

		# should probably be checking search 'scores'
		# and doing some better sorting here
		for query in queries:
			matching_tracks += service.search_songs(query)
			if len(matching_tracks) > 0:
				app.logger.info('Found ' + str(len(matching_tracks)) + ' results - moving to next song')
				break

		return matching_tracks


	def get_track_ids(self, tracks, service):
		# Id location varies by service...
		track_ids = []
		for track in tracks:
			if service == 'spotify':
				# spotify n.track.id
				track_ids.append(track['track']['uri'])

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

		# formatted tracks we'll save
		remote_spotify_tracks = []
		remote_google_tracks = []

		# refresh data from the source - spotify
		track_data = s.get_tracks(self.spotify_playlist_data)
		for track in track_data:
			# creates a generic track
			remote_spotify_tracks.append(SpotifyTrack(track).get_track())

		app.logger.info(remote_google_tracks)

		# do the same for google
		track_data = g.get_tracks(self.google_playlist_data)
		for track in track_data:
			# creates a generic track
			remote_google_tracks.append(GoogleTrack(track).get_track())

		self.remote_spotify_tracks = remote_spotify_tracks
		self.remote_google_tracks = remote_google_tracks


		app.logger.info(self.remote_google_tracks)

		# update the last refreshed timestamp
		self.last_refreshed = time.strftime("%m/%d/%Y %H:%M:%S")

	def generate_track_list(self, from_remote=False):
		spotify_tracks = self.spotify_tracks
		google_tracks = self.google_tracks

		# use the remote list if its flagged
		if from_remote:
			spotify_tracks = self.remote_spotify_tracks
			google_tracks = self.remote_google_tracks

		if self.type == 'masterslave':
			# build a track list
			if self.master == 'spotify':
				self.tracks = spotify_tracks

			if self.master == 'google':
				self.tracks = google_tracks

			return True

		return False

	def build_tracks(self, new_tracks):

		formatted_tracks = []

		for track in new_tracks:
			formatted_track = service_api.format_generic_track(track, self.tracks)
			formatted_track['_id'] = ObjectId()

			if formatted_track:
				formatted_tracks.append(formatted_track)
			else:
				app.logger.error('Cannot format track: ' + str(track))

		return formatted_tracks

	def attach_random_album_art(self):
		if len(self.tracks) > 0:
			# shuffle them so its random
			shuffled_tracks = self.tracks
			shuffle(shuffled_tracks)

			for t in shuffled_tracks:
				if t.get('album').get('art'):
					self.random_album_art = t.get('album').get('art')
					break

	def attach_external_track_data(self):
		if len(self.tracks) > 0:
			u = user.User(str(self.user_id))

			g = gmusic.GoogleMusic(u)
			s = spotify.Spotify(u)

			for t in self.tracks:
				google_track = g.get_track_from_id(self.google_tracks, t.get('google_id'))

				if google_track:
					similar_tracks = google_track.get('similar_tracks', [])

					google_track = g.format_generic_track(google_track)
					google_track['similar_tracks'] = map(g.format_generic_track, similar_tracks)

				t['google_data'] = google_track

				t['spotify_data'] = s.format_generic_track(s.get_track_from_uri(self.spotify_tracks, t.get('spotify_id')))

		return None

	def get_track_by_id(self, track_id):
		if len(self.tracks) > 0:
			for t in self.tracks:
				if str(t.get('_id')) == track_id:
					return t

		return None

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

	def delete(self):
		if self._id:
			return mongo.db.playlists.delete_one({ '_id' : self._id })

		return False

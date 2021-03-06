from app import app, cache
from flask import flash
from gmusicapi import Mobileclient
from uuid import getnode as get_mac

class GoogleMusic():
	def __init__(self, user):
		self.user = user

	def __repr__(self):
		return "%s:%s" % (self.__class__.__name__,self.user._id)

	def get_api(self):
		if hasattr(self, 'api'):
			return self.api

		api = Mobileclient()

		logged_in = api.login(self.user.google_credentials['google_id'], self.user.google_credentials['google_password'], api.FROM_MAC_ADDRESS)

		if logged_in:
			self.api = api
			return self.api
		return False

	def connect(self, google_id, google_password):
		# set the credentials
		self.user.google_credentials = {
			'google_id' : google_id,
			'google_password' : google_password
		}

		# attempt a api verification
		if self.get_api():
			app.logger.info('Successfully connected google account ID: ' + google_id)
			flash('Successfully connected your Google Play Music account')

			return self.user.save()
		else:
			app.logger.info('Failed to connect google account ID: ' + google_id)
			flash('Unable to validate Google ID and password')

			# make sure we clear out anything that was there
			self.disconnect()
			return False

	def disconnect(self):
		if hasattr(self.user, 'google_credentials'):
			del(self.user.google_credentials)
		return self.user.save()

	@cache.memoize(5 * 60)
	def search_songs(self, query):
		app.logger.info('Searching for song: ' + query)

		songs = []
		full_results = self.search(query)

		if full_results['song_hits']:
			songs = full_results['song_hits']

		return songs

	def search(self, query):
		api = self.get_api()
		results = []

		if api:
			results = api.search(query)

		return results

	def playlist_remove(self, playlist, delete_ids):
		app.logger.info('Removing ' + str(delete_ids) + ' from ' + str(playlist._id))

		# we need to translate trackIds into entry Ids
		# trackIds are used to add, but you need the specific
		# instance of this track in the playlist to delete
		delete_nids = self.get_nids_from_ids(playlist.google_tracks, delete_ids)

		app.logger.info('Translated into entriy IDs: ' + str(delete_nids))

		api = self.get_api()

		if api:
			return api.remove_entries_from_playlist(delete_nids)

		return False

	def playlist_add(self, playlist, insert_ids):
		app.logger.info('Adding ' + str(insert_ids) + ' from ' + str(playlist._id))

		playlist_id = playlist.google_playlist_data['id']

		if playlist_id and insert_ids:
			api = self.get_api()

			if api:
				return api.add_songs_to_playlist(playlist_id, insert_ids)

		return False

	def playlist_create(self, playlist_name):
		if not playlist_name.strip():
			return None

		api = self.get_api()

		if api:
			return api.create_playlist(playlist_name)

		return False

	# @cache.memoize(30 * 60)
	def get_playlists(self):
		api = self.get_api()
		playlists = []

		if api:
			playlists = api.get_all_playlists()

		return playlists

	# just a pass through, spotify is different
	def get_allowed_playlist(self, playlist_id):
		return self.get_my_playlist(playlist_id)

	def get_my_playlist(self, playlist_id):
		my_playlists = self.get_playlists()

		for playlist in my_playlists:
			if playlist_id == playlist['id']:
				return playlist

		return False

	def get_playlists_select(self):
		formatted_playlists = []

		playlists = self.get_playlists()

		for playlist in playlists:
			formatted_playlists.append(( playlist['id'], playlist['name'] ))

		return formatted_playlists

	def get_full_playlists(self):
		api = self.get_api()
		playlists = []

		if api:
			playlists = api.get_all_user_playlist_contents()

		return playlists

	# @cache.memoize(30)
	def get_tracks(self, playlist=None):
		# api work handled in playlist function
		if playlist:
			playlists = self.get_full_playlists()

			for p in playlists:
				if p['id'] == playlist['id']:
					return p['tracks']

		return []

	def format_generic_track(self, track, existing_tracks=None):
		if not track or 'track' not in track:
			return None

		track_data = track['track']

		# if this spotify id already exists in our existing
		# tracks we can just return that element
		if existing_tracks:
			existing = self.get_existing_track(track, existing_tracks)
			if existing:
				return existing

		# if we don't have it already, generate it
		return {
			'spotify_id' : None,
			'google_id' : track['trackId'],
			'title' : track_data['title'],
			'artists' : self.format_generic_artists(track_data),
			'album' : self.format_generic_album(track_data)
		}

	def format_generic_artists(self, track_data):
		formatted_artists = []

		formatted_artists.append({
			'name' : track_data['artist']
		})

		return formatted_artists

	def format_generic_album(self, track_data):
		album_image = None

		if len(track_data.get('albumArtRef', [])) > 0:
			album_image = track_data.get('albumArtRef', [ {} ])[0].get('url', None)

		return {
			'name' : track_data.get('album'),
			'art' : album_image
		}

	def get_existing_track(self, track, tracks):
		for existing in tracks:
			if existing['google_id'] == track['trackId']:
				return existing

		return None

	# tracks - spotify tracks
	# uri - uri
	def get_track_from_id(self, tracks, track_id):
		for track in tracks:
			if track.get('trackId', None) == track_id:
				return track

		return None

	def get_nids_from_ids(self, tracks, track_ids):
		entry_ids = []

		for track in tracks:
			if track.get('trackId', None) in track_ids:
				nid = track.get('id', None)

				if nid:
					entry_ids.append(nid)

		return entry_ids
from app import app, cache
from gmusicapi import Mobileclient
from uuid import getnode as get_mac

class GoogleMusic():
	def __init__(self, user):
		self.user = user

	def __repr__(self):
		return "%s:%s" % (self.__class__.__name__,self.user._id)

	def get_api(self):
		if hasattr(self, 'api'):
			app.logger.info('Loaded cached Google API')
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
			app.logger.info('Succesfully connected google account ID: ' + google_id)
			return self.user.save()
		else:
			flash('Unable to validate Google ID and password')
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

	@cache.memoize(30 * 60)
	def get_playlists(self):
		api = self.get_api()
		playlists = []

		if api:
			playlists = api.get_all_playlists()

		return playlists

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

	def format_generic_track(self, track, existing_tracks):
		track_data = track['track']

		# if this spotify id already exists in our existing
		# tracks we can just return that element
		for existing in existing_tracks:
			if existing['google_id'] == track['trackId']:
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
		return {
			'name' : track_data['album']
		}

	def get_nids_from_ids(self, tracks, track_ids):
		entry_ids = []

		for track in tracks:
			if track.get('trackId', None) in track_ids:
				nid = track.get('id', None)

				if nid:
					entry_ids.append(nid)

		return entry_ids
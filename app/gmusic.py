from app import app, cache
from gmusicapi import Mobileclient
from uuid import getnode as get_mac

class GoogleMusic():
	def __init__(self, user):
		self.user = user

	def __repr__(self):
		return "%s:%s" % (self.__class__.__name__,self.user.username)

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
		if hasattr(self, 'google_credentials'):
			del(self.google_credentials)
		return self.save()

	def search_songs(self, query):
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

	@cache.memoize(600)
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

	@cache.memoize(600)
	def get_full_playlists(self):
		api = self.get_api()
		playlists = []

		if api:
			playlists = api.get_all_user_playlist_contents()

		return playlists

	def get_tracks(self, playlist):
		# api work handled in playlist function
		playlists = self.get_full_playlists()

		for p in playlists:
			if p['id'] == playlist['id']:
				return p['tracks']

		return [];

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
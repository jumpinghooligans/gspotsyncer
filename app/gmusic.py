from app import app
from gmusicapi import Mobileclient
from uuid import getnode as get_mac

class GoogleMusic():
	def __init__(self, user):
		self.google_id = user.google_id
		self.google_password = user.google_password

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

	def get_playlists(self):
		api = self.get_api()
		playlists = []

		if api:
			playlists = api.get_all_playlists()

		return playlists

	def get_full_playlists(self):
		api = self.get_api()
		playlists = []

		if api:
			playlists = api.get_all_user_playlist_contents()

		return playlists

	def get_api(self):
		app.logger.info(self.google_password)

		api = Mobileclient()
		# logged_in = api.login('ryankortmann@gmail.com', 'fdwjigsodltkljbf', api.FROM_MAC_ADDRESS)
		logged_in = api.login(self.google_id, self.google_password, api.FROM_MAC_ADDRESS)

		if logged_in:
			return api
		return False
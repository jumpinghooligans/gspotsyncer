from app import app
import urllib, urllib2, json
from urlparse import urlparse

class Spotify():
	def __init__(self, user):
		self.spotify_credentials = user.spotify_credentials

	def get_playlists(self):
		req = self.get_auth_request('https://api.spotify.com/v1/me/playlists')
		
		res = self.send_auth_request(req)
		if res.getcode() == 200:
			results = json.loads(res.fp.read())
			return results['items']

		return None

	def get_playlists_select(self):
		playlists = self.get_playlists()

		formatted_playlists = []
		if playlists:
			for playlist in playlists:
				formatted_playlists.append(( playlist['id'], playlist['name'] ))
		return formatted_playlists


	def send_auth_request(self, request, data={}):
		try:
			if data:
				return urllib2.urlopen(request, data)
			else:
				return urllib2.urlopen(request)

		except urllib2.HTTPError as err:
			return err

	def get_auth_request(self, url):
		generic_request = urllib2.Request(url)
		generic_request.add_header('Authorization', self.spotify_credentials['token_type'] + ' ' + self.spotify_credentials['access_token'])

		return generic_request

def get_return_uri(request_url):
	url = urlparse(request_url)
	hostname = url.hostname

	return 'http://' + hostname + '/spotify/return'
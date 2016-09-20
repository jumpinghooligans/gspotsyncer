from app import app
import urllib, urllib2, json

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
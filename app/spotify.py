from app import app, mongo, user
from flask import request, flash

import urllib, urllib2, json, base64

from urlparse import urlparse

class Spotify():
	def __init__(self, user):
		self.spotify_credentials = user.spotify_credentials

	def connect(self):
		# get and store auth codes
		spotify_auth_request = urllib2.Request('https://accounts.spotify.com/api/token')
		spotify_auth_request.add_header('Authorization', 'Basic ' + base64.b64encode(app.config['SPOTIFY_CLIENT_ID'] + ':' + app.config['SPOTIFY_CLIENT_SECRET']))
		params = {
			'grant_type' : 'authorization_code',
			'code' : request.args.get('code'),
			'redirect_uri' : get_return_url(request.url)
		}

		try:
			spotify_auth_response = urllib2.urlopen(spotify_auth_request, urllib.urlencode(params))
			spotify_credentials = json.loads(spotify_auth_response.read())

			# update our credentials
			self.spotify_credentials = spotify_credentials
			user.current_user.spotify_credentials = spotify_credentials

			if user.current_user.save():
				flash('Successfully updated Spotify credentials...')
				return True
			else:
				flash('Unknown error updating Spotify credentials...')
				return False

		except urllib2.HTTPError as err:
			response = json.loads(err.fp.read())
			flash(response)

	def refresh_token(self):
		refresh_request = urllib2.Request('https://accounts.spotify.com/api/token')
		refresh_request.add_header('Authorization', 'Basic ' + base64.b64encode(app.config['SPOTIFY_CLIENT_ID'] + ':' + app.config['SPOTIFY_CLIENT_SECRET']))
		params = {
			'grant_type' : 'refresh_token',
			'refresh_token' : self.spotify_credentials['refresh_token']
		}

		try:
			refresh_response = urllib2.urlopen(refresh_request, urllib.urlencode(params))
			spotify_credentials = json.loads(refresh_response.read())

			# spotify doesn't return our refresh token, so let's tack it back on
			spotify_credentials['refresh_token'] = self.spotify_credentials['refresh_token']

			# update our credentials
			self.spotify_credentials = spotify_credentials
			user.current_user.spotify_credentials = spotify_credentials

			if user.current_user.save():
				flash('Successfully updated Spotify credentials...')
				return True
			else:
				flash('Unknown error updating Spotify credentials...')
				return False

		except urllib2.HTTPError as err:
			response = json.loads(err.fp.read())
			flash(response)


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


	def send_auth_request(self, request, data={}, attempt_refresh=True):
		try:
			if data:
				return urllib2.urlopen(request, data)
			else:
				return urllib2.urlopen(request)

		except urllib2.HTTPError as err:
			# unauthorized - refresh
			if err.getcode() == 401 and attempt_refresh == True:
				app.logger.info("Received 401 - Refreshing Token")
				self.refresh_token()
				return self.send_auth_request(request, data, False)
			return err

	def get_auth_request(self, url):
		generic_request = urllib2.Request(url)
		generic_request.add_header('Authorization', self.spotify_credentials['token_type'] + ' ' + self.spotify_credentials['access_token'])

		return generic_request

#
#  General spotify helpers
#  
def get_connect_url(url):
	scope = " ".join(['playlist-read-private',
		'playlist-read-collaborative',
		'playlist-modify-public',
		'playlist-modify-private'])

	params = {
		'response_type' : 'code',
		'client_id' : app.config['SPOTIFY_CLIENT_ID'],
		'scope' : scope,
		'redirect_uri' : get_return_url(url)
	}

	return 'https://accounts.spotify.com/authorize?' + urllib.urlencode(params)

def get_return_url(request_url):
	url = urlparse(request_url)
	hostname = url.hostname

	return 'http://' + hostname + '/spotify/return'
from app import app, cache
from flask import request, flash

import urllib, urllib2, httplib2, json, base64

from urlparse import urlparse

class Spotify():
	def __init__(self, user):
		self.user = user

	def __repr__(self):
		return "%s:%s" % (self.__class__.__name__,self.user._id)

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
			self.user.spotify_credentials = spotify_credentials

			if self.user.save():
				self.refresh_user_data()
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
			'refresh_token' : self.user.spotify_credentials['refresh_token']
		}

		try:
			refresh_response = urllib2.urlopen(refresh_request, urllib.urlencode(params))
			spotify_credentials = json.loads(refresh_response.read())

			# spotify doesn't return our refresh token, so let's tack it back on
			spotify_credentials['refresh_token'] = self.user.spotify_credentials['refresh_token']

			# update our credentials
			self.user.spotify_credentials = spotify_credentials

			if self.user.save():
				self.refresh_user_data()
				flash('Successfully refreshed Spotify credentials...')
				return True
			else:
				flash('Unknown error refreshing Spotify credentials...')
				return False

		except urllib2.HTTPError as err:
			response = json.loads(err.fp.read())
			flash(response)
			return False

	def disconnect(self):
		if hasattr(self.user, 'spotify_credentials'):
			del(self.user.spotify_credentials)
		return self.user.save()

	def refresh_user_data(self):
		# get my user data
		data = self.get_me()

		# save it
		self.user.spotify_data = data
		return self.user.save()

	def get_me(self):
		req = self.get_auth_request('https://api.spotify.com/v1/me')
		res = self.send_auth_request(req)

		return json.loads(res.read())

	def search_songs(self, query):
		search_results = self.search(query, 'track')

		search_results = search_results.get('tracks', [])
		search_results = search_results.get('items', [])
		return search_results

	def search(self, query, result_type):
		params = {
			'q' : query,
			'type' : result_type
		}

		req = self.get_auth_request('https://api.spotify.com/v1/search?' + urllib.urlencode(params))
		res = self.send_auth_request(req)

		return json.loads(res.read())

	@cache.memoize(30 * 60)
	def get_playlists(self):
		req = self.get_auth_request('https://api.spotify.com/v1/me/playlists')
		res = self.send_auth_request(req)

		if res and res.getcode() == 200:
			results = json.loads(res.read())
			return results['items']

		return None

	def get_playlists_select(self):
		playlists = self.get_playlists()

		formatted_playlists = []
		if playlists:
			for playlist in playlists:
				formatted_playlists.append(( playlist['id'], playlist['name'] ))
		return formatted_playlists

	def playlist_remove(self, playlist, delete_ids):
		pass

		playlist_data = playlist.spotify_playlist_data

		uris = []
		for delete_id in delete_ids:
			uris.append({
				'uri' : delete_id
			})

		params = {
			'tracks' : uris
		}

		req = self.get_auth_request('https://api.spotify.com/v1/users/' + playlist_data['owner']['id'] +'/playlists/' + playlist_data['id'] + '/tracks', 'DELETE')
		res = self.send_auth_request(req, json.dumps(params))

		if res and res.getcode() == 200:
			return json.loads(res.read())

		return False

	def playlist_add(self, playlist, insert_ids):
		playlist_data = playlist.spotify_playlist_data

		params = {
			'uris' : insert_ids
		}

		req = self.get_auth_request('https://api.spotify.com/v1/users/' + playlist_data['owner']['id'] +'/playlists/' + playlist_data['id'] + '/tracks')
		res = self.send_auth_request(req, json.dumps(params))

		if res and res.getcode() == 200:
			return json.loads(res.read())

		return False

	# @cache.memoize(30)
	def get_tracks(self, playlist_data=None):
		if playlist_data:
			req = self.get_auth_request('https://api.spotify.com/v1/users/' + playlist_data['owner']['id'] +'/playlists/' + playlist_data['id'])
			res = self.send_auth_request(req)

			if res and res.getcode() == 200:
				return json.loads(res.read())['tracks']['items']

		return []

	def format_generic_track(self, track, existing_tracks):
		track = track['track']

		# if this spotify id already exists in our existing
		# tracks we can just return that element
		for existing in existing_tracks:
			if existing['spotify_id'] == track['id']:
				return existing

		# if we don't have it already, generate it
		return {
			'spotify_id' : track['uri'],
			'google_id' : None,
			'title' : track['name'],
			'artists' : self.format_generic_artists(track['artists']),
			'album' : self.format_generic_album(track['album'])
		}

	def format_generic_artists(self, artists):
		formatted_artists = []

		for artist in artists:
			formatted_artists.append({
				'name' : artist['name']
			})

		return formatted_artists

	def format_generic_album(self, album):
		return {
			'name' : album['name']
		}

	def send_auth_request(self, request, data={}, attempt_refresh=True):
		opener = urllib2.build_opener(urllib2.HTTPHandler)

		try:
			if data:
				return opener.open(request, data)
			else:
				return opener.open(request)

		except urllib2.HTTPError as err:
			# unauthorized - refresh
			if err.getcode() == 401 and attempt_refresh == True:
				app.logger.info("Received 401 - Refreshing Token")

				if self.refresh_token():
					request = self.get_auth_request(request.get_full_url())
					return self.send_auth_request(request, data, False)
			else:
				return err

	def get_auth_request(self, url, overrideMethod=None):
		generic_request = urllib2.Request(url)
		generic_request.add_header('Authorization', self.user.spotify_credentials['token_type'] + ' ' + self.user.spotify_credentials['access_token'])
		generic_request.add_header('Content-Type', 'application/json')

		if overrideMethod:
			generic_request.get_method = lambda: 'PUT'

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
from app import app, cache
from flask import request, flash

import urllib, requests, json, base64

from urlparse import urlparse

class Spotify():
	def __init__(self, user):
		self.user = user

	def __repr__(self):
		return "%s:%s" % (self.__class__.__name__,self.user._id)

	def connect(self):
		spotify_auth_response = requests.post(
			url='https://accounts.spotify.com/api/token',
			headers={ 'Authorization' : 'Basic ' + base64.b64encode(app.config['SPOTIFY_CLIENT_ID'] + ':' + app.config['SPOTIFY_CLIENT_SECRET']) },
			data={
				'grant_type' : 'authorization_code',
				'code' : request.args.get('code'),
				'redirect_uri' : get_return_url(request.url)
			}
		)

		if spotify_auth_response.status_code == requests.codes.ok:
			# update our credentials
			self.user.spotify_credentials = spotify_auth_response.json()

			app.logger.info(spotify_auth_response.json())

			if self.user.save():
				self.refresh_user_data()
				flash('Successfully updated Spotify credentials...')
				return True
			else:
				flash('Unknown error updating Spotify credentials...')
				return False
		else:
			flash(spotify_auth_response.json())
			return False

	def refresh_token(self):
		refresh_response = requests.post(
			url='https://accounts.spotify.com/api/token',
			headers={ 'Authorization' : 'Basic ' + base64.b64encode(app.config['SPOTIFY_CLIENT_ID'] + ':' + app.config['SPOTIFY_CLIENT_SECRET']) },
			data={
				'grant_type' : 'refresh_token',
				'refresh_token' : self.user.spotify_credentials['refresh_token']
			}
		)

		if refresh_response.status_code == requests.codes.ok:
			spotify_credentials = refresh_response.json()

			# update our credentials
			self.user.spotify_credentials.update(spotify_credentials)

			if self.user.save():
				self.refresh_user_data()
				flash('Successfully refreshed Spotify credentials...')
				return True
			else:
				flash('Unknown error refreshing Spotify credentials...')
				return False
		else:
			flash(refresh_response.json())
			return False

	def disconnect(self):
		if hasattr(self.user, 'spotify_credentials'):
			del(self.user.spotify_credentials)
		return self.user.save()

	def refresh_user_data(self):
		# get my user data
		data = self.get_me()

		if data and 'id' in data:
			# save it
			self.user.spotify_data = data
			return self.user.save()
		else:
			flash(data)
			return False

	def get_me(self):
		res = self.request('get',
			url='https://api.spotify.com/v1/me'
		)

		if res:
			return res.json()

		return False

	def search_songs(self, query):
		app.logger.info('Searching for song: ' + query)

		search_results = self.search(query, 'track')

		search_results = search_results.get('tracks', {})
		search_results = search_results.get('items', [])

		return search_results

	def search(self, query, result_type):
		params = {
			'q' : query,
			'type' : result_type
		}

		res = self.request('get',
			url='https://api.spotify.com/v1/search',
			params=params
		)

		return res.json()

	# @cache.memoize(30 * 60)
	def get_playlists(self):
		res = self.request('get',
			url='https://api.spotify.com/v1/me/playlists'
		)

		res = res.json()

		return res.get('items', [])

	def get_playlists_select(self):
		playlists = self.get_playlists()

		formatted_playlists = []
		if playlists:
			for playlist in playlists:
				formatted_playlists.append(( playlist['id'], playlist['name'] ))

		return formatted_playlists

	def playlist_remove(self, playlist, delete_uris):
		app.logger.info('Removing ' + str(delete_uris) + ' from ' + str(playlist._id))

		playlist_data = playlist.spotify_playlist_data

		uris = []
		for delete_uri in delete_uris:
			uris.append({
				'uri' : delete_uri
			})

		data = {
			'tracks' : uris
		}

		res = self.request('delete',
			url='https://api.spotify.com/v1/users/' + playlist_data['owner']['id'] +'/playlists/' + playlist_data['id'] + '/tracks',
			headers={ 'Content-Type' : 'application/json' },
			data=json.dumps(data)
		)

		return res.json()

	def playlist_add(self, playlist, insert_ids):
		app.logger.info('Adding ' + str(insert_ids) + ' from ' + str(playlist._id))

		playlist_data = playlist.spotify_playlist_data

		data = {
			'uris' : insert_ids
		}

		res = self.request('post',
			url='https://api.spotify.com/v1/users/' + playlist_data['owner']['id'] +'/playlists/' + playlist_data['id'] + '/tracks',
			headers={ 'Content-Type' : 'application/json' },
			data=json.dumps(data)
		)

		return res.json()

	def playlist_create(self, playlist_name):
		if not playlist_name.strip():
			return None

		user_id = self.user.spotify_data.get('id', 'me')
		data = {
			'name' : playlist_name
		}

		res = self.request('post',
			url='https://api.spotify.com/v1/users/' + user_id + '/playlists',
			data=json.dumps(data)
		)

		return res.json()

	# @cache.memoize(30)
	def get_tracks(self, playlist_data=None):
		if playlist_data:
			res = self.request('get',
				url='https://api.spotify.com/v1/users/' + playlist_data['owner']['id'] +'/playlists/' + playlist_data['id']
			)

			res = res.json()

			tracks = res.get('tracks', {})

			return tracks.get('items', {})

		return {}

	# track - spotify track
	# existing_tracks - generic tracks
	def format_generic_track(self, track, existing_tracks=None):
		if not track:
			return None

		track = track['track']

		# if this spotify id already exists in our existing
		# tracks we can just return that element
		if existing_tracks:
			existing = self.get_existing_track(track, existing_tracks)
			if existing:
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
		album_image = None

		if len(album.get('images', [])) > 0:
			album_image = album.get('images').pop(0).get('url')

		return {
			'name' : album.get('name', ''),
			'art' : album_image
		}

	def get_existing_track(self, track, tracks):
		for existing in tracks:
			if existing['spotify_id'] == track['uri']:
				return existing

		return None

	def get_uris_from_ids(self, tracks, ids):
		uris = []

		for track in tracks:
			track = track.get('track', {})

			if track.get('id', None) in ids:
				uri = track.get('uri', None)
				if uri:
					uris.append(uri)

		return uris

	def get_allowed_playlist(self, playlist_id):
		my_allowed_playlists = self.get_playlists()

		for playlist in my_allowed_playlists:
			if playlist_id == playlist['id']:
				return playlist

		return None

	def get_my_playlist(self, playlist_id):
		user_id = self.user.spotify_data.get('id', 'me')

		return 'https://api.spotify.com/v1/users/' + user_id + '/playlists/' + playlist_id
		res = self.request('get',
			url='https://api.spotify.com/v1/users/' + user_id + '/playlists/' + playlist_id
		)

		res = res.json()

		return res

	# tracks - spotify tracks
	# uri - uri
	def get_track_from_uri(self, tracks, uri):
		for track in tracks:
			if track.get('track', {}).get('uri', None) == uri:
				return track

		return None

	def request(self, verb, **kwargs):
		requester = getattr(requests, verb)

		# attach the user credentials
		if not kwargs.get('headers', None):
			kwargs['headers'] = {}

		kwargs['headers'].update({ 'Authorization' : self.user.spotify_credentials['token_type'] + ' ' + self.user.spotify_credentials['access_token'] })

		# hacky way of making sure we don't loop on 401s
		refresh_attempted = getattr(self, 'refresh_attempted', False)

		# make the request
		res = requester(**kwargs)

		# if we get a 401 - attempt a refresh
		if res.status_code == 401 and not refresh_attempted:
			app.logger.info("User " + str(self.user._id) + " Received 401 - Refreshing Token")

			# Don't get stuck in a unauthorized loop
			self.refresh_attempted = True

			if self.refresh_token():
				# update the kwargs
				kwargs['headers'] = { 'Authorization' : self.user.spotify_credentials['token_type'] + ' ' + self.user.spotify_credentials['access_token'] }

				# try this request again
				return self.request(verb, **kwargs)
			else:
				# we tried to refresh but failed, there's probably
				# some real issue, return the original request
				self.disconnect()
				return res
		else:
			# request is not a 401 - pass on through
			return res

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
	if url.port:
		hostname += ':' + str(url.port)

	return 'http://' + hostname + '/spotify/return'
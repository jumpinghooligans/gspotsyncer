from app import app
from gmusicapi import Mobileclient

def search_songs(query):
	songs = []
	full_results = search(query)

	if full_results['song_hits']:
		songs = full_results['song_hits']

	return songs

def search(query):
	api = get_api()
	results = []

	if api:
		results = api.search(query)

	return results

def get_playlists():
    api = get_api()
    playlists = []

    if api:
        playlists = api.get_all_playlists()

    return playlists

def get_full_playlists():
    api = get_api()
    playlists = []

    if api:
        playlists = api.get_all_user_playlist_contents()

    return playlists

def get_api():
    api = Mobileclient()
    logged_in = api.login('ryankortmann@gmail.com', 'fdwjigsodltkljbf', api.FROM_MAC_ADDRESS)

    if logged_in:
        return api
    return False
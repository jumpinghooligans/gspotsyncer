# Flask
from flask import render_template, request, flash, redirect

# Forms
from .forms import CreateForm, LoginForm, UserAccountForm, CreatePlaylistForm

# Service Manipulation
from app import app, gmusic, spotify, user, playlist

# General imports
import urllib, json, time

@app.route('/', methods=['GET', 'POST'])
def index():
	return render_template('index.html',
							title='Home')

@app.route('/login', methods=['GET', 'POST'])
@app.route('/account/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()

	if form.validate_on_submit():
		user.login(form.username.data, form.password.data)
		
		# Current User will return an Anonymous User, so we
		# need to check the actual ID (Anon returns 'None')
		if user.current_user.get_id():
			if request.args.get('next'):
				return redirect(request.args.get('next'))

			return redirect('/account')

	return render_template('account/login.html',
							title='Login',
							form=form)

@app.route("/logout")
@app.route('/account/logout')
@user.login_required
def logout():
    user.logout_user()
    return redirect('/')

@app.route('/account/create', methods=['GET', 'POST'])
def create_user():
	form = CreateForm()

	if form.validate_on_submit():
		result = user.register({
			'username' : form.username.data,
			'password' : form.password.data
		})

		if result:
			return redirect('/account')

	return render_template('account/create.html',
							title='Create User',
							form=form)


@app.route('/account', methods=['GET', 'POST'])
@user.login_required
def account():
	form = UserAccountForm()

	if form.validate_on_submit():
		# logged in user
		u = user.current_user

		# clear out the password key if nothing was passed
		# else hash it
		if form.password.data:
			form.password.data = user.hash_hex(form.password.data)
		else:
			del(form.password)

		# connect if we have values
		if form.google_id.data and form.google_password.data:
			g = gmusic.GoogleMusic(user.current_user)
			g.connect(form.google_id.data, form.google_password.data)

		# delete them so we don't store them flat on the user doc
		del(form.google_id)
		del(form.google_password)

		# overwrite with the form data
		form.populate_obj(u)

		# save the user
		u.save()

		return redirect('/account')


	return render_template('account/index.html',
							title='Account',
							form=form)

@app.route('/google/disconnect')
@user.login_required
def google_disconnect():
	g = gmusic.GoogleMusic(user.current_user)
	g.disconnect()

	return redirect('/account')

@app.route('/playlists', methods=['GET', 'POST'])
@user.login_required
def playlists():
	playlists = playlist.get_user_playlists(user.current_user)

	return render_template('playlists/index.html',
							title='Playlists',
							playlists=playlists)

@app.route('/playlists/create', methods=['GET', 'POST'])
@user.login_required
def create_playlist():
	if not user.current_user.can_modify_playlist():
		return redirect('/account')

	form = CreatePlaylistForm()

	s = spotify.Spotify(user.current_user)
	g = gmusic.GoogleMusic(user.current_user)

	spotify_choices = s.get_playlists_select()
	google_choices = g.get_playlists_select()

	form.spotify_playlist.choices = spotify_choices
	form.google_playlist.choices = google_choices

	if form.validate_on_submit():
		p = playlist.Playlist({})

		p.user_id = user.current_user._id

		p.type = form.playlist_type.data

		p.spotify_playlist_id = form.spotify_playlist.data
		full_spotify_playlists = s.get_playlists()
		for full_playlist in full_spotify_playlists:
			if p.spotify_playlist_id == full_playlist['id']:
				p.spotify_playlist_data = dict(full_playlist)
				break

		p.google_playlist_id = form.google_playlist.data
		full_google_playlists = g.get_playlists()
		for full_playlist in full_google_playlists:
			if p.google_playlist_id == full_playlist['id']:
				p.google_playlist_data = dict(full_playlist)
				break

		p.master = form.master.data

		# get get track lists
		p.refresh_external_tracks()

		save = p.save()

		return redirect('/playlists/' + str(save.inserted_id) + '/modify')


	return render_template('playlists/create.html',
							title='Create a Playlist',
							form=form)

@app.route('/playlists/<string:playlist_id>', methods=['GET', 'POST'])
@user.login_required
def view_playlist(playlist_id):
	p = playlist.Playlist(str(playlist_id))

	if not user.current_user.can_view_playlist(p):
		return redirect('/account')

	return render_template('playlists/playlist.html',
							title='View Playlist',
							playlist=p)

@app.route('/playlists/<string:playlist_id>/modify', methods=['GET', 'POST'])
@user.login_required
def modify_playlist(playlist_id):
	p = playlist.Playlist(str(playlist_id))

	if not user.current_user.can_modify_playlist(p):
		return redirect('/account')

	# refresh from the internet
	p.refresh_external_tracks()
	p.generate_track_list()
	p.save()

	return render_template('playlists/modify.html',
							title='Modify Playlist',
							playlist=p)

@app.route('/playlists/<string:playlist_id>/process', methods=['GET', 'POST'])
@user.login_required
def process_playlist(playlist_id):
	p = playlist.Playlist(str(playlist_id))

	# Using the type of playlist, and both sets of
	# playlist data, generate a master list
	p.generate_track_list()

	# Using track name/artist/album lookup any
	# missing service track IDs
	p.find_missing_tracks()

	# Do a diff and publish any tracks that exist
	# in the master list and don't exist on the
	# remote playlists - reverse for tracks on the
	# remote and not on the master list
	p.publish_tracks()

	# Refresh our external track data, this
	# should now reflect any playlist edits
	# we made above
	p.refresh_external_tracks()

	# Save all of our changes
	res = p.save()

	return redirect('/playlists/' + playlist_id)


@app.route('/spotify/connect')
@user.login_required
def spotify_connect():
	spotify_url = spotify.get_connect_url(request.url)

	return redirect(spotify_url)

@app.route('/spotify/refresh_token')
@user.login_required
def spotify_refresh():
	s = spotify.Spotify(user.current_user)
	s.refresh_token()

	return redirect('/account')

@app.route('/spotify/return')
@user.login_required
def spotify_return():
	# successful if we get a 'code' query param
	if request.args.get('code'):
		s = spotify.Spotify(user.current_user)
		s.connect()

	else:
		# in theory there should be an error
		flash(request.args.get('error', 'Something went wrong...'))

	return redirect('/account')

@app.route('/spotify/disconnect')
@user.login_required
def spotify_disconnect():
	s = spotify.Spotify(user.current_user)
	s.disconnect()

	return redirect('/account')

@app.route('/test')
@user.login_required
def test_method():
	s = spotify.Spotify(user.current_user)

	return str(s.get_me())
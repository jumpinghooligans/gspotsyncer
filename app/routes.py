# Flask
from flask import render_template, request, flash, redirect

# Forms
from .forms import CreateForm, LoginForm, UserAccountForm, GoogleCredentialsForm, CreatePlaylistForm

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
		registered = user.register({
			'username' : form.username.data,
			'password' : form.password.data
		})

		if registered:
			return redirect('/account')

	return render_template('account/create.html',
							title='Create User',
							form=form)


@app.route('/account', methods=['GET', 'POST'])
@user.login_required
def account():
	account_form = UserAccountForm()
	google_credentials_form = GoogleCredentialsForm()

	# get some playlists to show
	playlists = playlist.get_user_playlists(user.current_user)[0:3]

	# pretty
	for p in playlists:
		p.attach_random_album_art()

	if account_form.validate_on_submit() and account_form.update_account.data:

		# logged in user
		u = user.current_user
		u.password = user.hash_hex(account_form.password.data)
		u.save()

		flash('Successfully updated your account!')

		return redirect('/account')

	if google_credentials_form.validate_on_submit() and google_credentials_form.update_google.data:

		google_id = google_credentials_form.google_id.data
		google_password =google_credentials_form.google_password.data

		# connect if we have values
		if google_id and google_password:
			g = gmusic.GoogleMusic(user.current_user)
			g.connect(google_id, google_password)

		return redirect('/account')


	return render_template('account/index.html',
							title='Account',
							playlists=playlists,
							account_form=account_form,
							google_credentials_form=google_credentials_form)

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

	for p in playlists:
		p.attach_random_album_art()

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

	if spotify_choices:
		spotify_choices.insert(0, ('', 'Select a Playlist'))
		form.spotify_playlist.choices = spotify_choices
	if google_choices:
		google_choices.insert(0, ('', 'Select a Playlist'))
		form.google_playlist.choices = google_choices

	if form.validate_on_submit():
		p = playlist.Playlist({})

		p.user_id = user.current_user._id

		p.type = form.playlist_type.data

		# Pull form data
		spotify_playlist_id = str(form.spotify_playlist.data)
		spotify_create_name = str(form.spotify_create.data)

		google_playlist_id = str(form.google_playlist.data)
		google_create_name = str(form.google_create.data)

		# Basic validation
		if not (spotify_playlist_id or google_playlist_id):
			flash('You must select at least one existing Google or Spotify playlist')
			return redirect('/playlists/create')

		if not (spotify_playlist_id or spotify_create_name):
			flash('Missing a Spotify playlist or new playlist name')
			return redirect('/playlists/create')

		if not (google_playlist_id or google_create_name):
			flash('Missing a Google playlist or new playlist name')
			return redirect('/playlists/create')

		#
		# Spotify
		#
		# Attach the selected playlists data to our new
		# playlist object - or create a new playlist and
		# attach that data
		#

		if spotify_playlist_id:

			# Find an existing playlist
			p.spotify_playlist_id = spotify_playlist_id
			p.spotify_playlist_data = s.get_allowed_playlist(spotify_playlist_id)

		else:

			# Create a playlist
			new_playlist_result = s.playlist_create(spotify_create_name)

			if new_playlist_result.get('id', None):
				# Get the new ID
				new_playlist_id = new_playlist_result.get('id', None)

				# attach our new playlist data
				p.spotify_playlist_id = new_playlist_id
				p.spotify_playlist_data = s.get_allowed_playlist(new_playlist_id)

			else:
				flash('Unable to create a playlist named \'' + spotify_create_name + '\'')
				return redirect('/playlists/create')

		#
		# Google
		#
		# Attach the selected playlists data to our new
		# playlist object - or create a new playlist and
		# attach that data
		#

		if google_playlist_id:

			# Find an existing playlist
			p.google_playlist_id = google_playlist_id
			p.google_playlist_data = g.get_allowed_playlist(google_playlist_id)

		else:

			# Create a playlist
			new_playlist_result = g.playlist_create(google_create_name)

			if new_playlist_result:
				p.google_playlist_id = new_playlist_result
				p.google_playlist_data = g.get_allowed_playlist(new_playlist_result)

			else:
				flash('Unable to create a playlist named \'' + google_create_name + '\'')
				return redirect('/playlists/create')

		# Make sure we got two valid playlists out of that whole shindig above
		# if not spotify_create_name:
		# 	flash('You must select either an existing Spotify playlist or pick a name to create one')
		# 	return redirect('/playlists/create')

		# master of the master / slave
		p.master = form.master.data

		# shorthand name for the playlist
		p.name = p.spotify_playlist_data.get('name') + ' / ' + p.google_playlist_data.get('name')

		# created timestamp
		p.created = time.strftime("%d/%m/%Y %H:%M:%S")

		# get get track lists
		p.refresh_external_tracks()

		save = p.save()

		return redirect('/playlists/' + str(save.inserted_id) + '/refresh')


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

	# shortcuts for external data
	p.attach_external_track_data()

	return render_template('playlists/modify.html',
							title='Modify Playlist',
							playlist=p)

@app.route('/playlists/<string:playlist_id>/refresh')
@user.login_required
def refresh_playlist(playlist_id):
	p = playlist.Playlist(str(playlist_id))

	if not user.current_user.can_modify_playlist(p):
		return redirect('/account')

	# refresh name - just in case
	p.name = p.spotify_playlist_data.get('name') + ' / ' + p.google_playlist_data.get('name')

	# refresh from the internet
	p.refresh_external_tracks()
	p.generate_track_list()

	if p.save():
		flash('Successfully refreshed playlist data')

	return redirect('/playlists/' + str(playlist_id))

@app.route('/playlists/<string:playlist_id>/process', methods=['GET', 'POST'])
@user.login_required
def process_playlist(playlist_id):
	p = playlist.Playlist(str(playlist_id))

	if not user.current_user.can_modify_playlist(p):
		return redirect('/account')

	# Make sure we have the most up to date
	# track lists from google and spotify
	p.refresh_external_tracks()

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
	if p.save():
		flash('Successfully processed and published tracks to Spotify and Google Play Music')

	return redirect('/playlists/' + playlist_id)

@app.route('/playlists/<string:playlist_id>/delete')
@user.login_required
def delete_playlist(playlist_id):
	p = playlist.Playlist(str(playlist_id))

	if p.delete():
		flash('Successfully deleted playlist')

	return redirect('/playlists')

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

@app.route('/preload/<path:process_url>')
def preload(process_url):
	# prepend a slash
	process_url = '/' + process_url
	return render_template('loader.html',
							title='Processing...',
							process_url=process_url)

@app.route('/test')
@user.login_required
def test_method():
	time.sleep(5)
	return 'a'
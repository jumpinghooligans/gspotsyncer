# Flask
from flask import render_template, request, flash, redirect

# Forms
from .forms import CreateForm, LoginForm, UserAccountForm, CreatePlaylistForm

# Service Manipulation
from app import app, gmusic, spotify, user, playlist

# General imports
import urllib, urllib2, json

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
		user.register({
			'username' : form.username.data,
			'password' : form.password.data
		})
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

		# figure out a better way to do this
		if form.google_password.data == '':
			del(form.google_password)

		# overwrite with the form data
		form.populate_obj(u)

		# save the user
		u.save()

		return redirect('/account')


	return render_template('account/index.html',
							title='Account',
							form=form)

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
	form = CreatePlaylistForm()

	s = spotify.Spotify(user.current_user)
	g = gmusic.GoogleMusic(user.current_user)

	spotify_choices = s.get_playlists_select()
	google_choices = g.get_playlists_select()

	form.spotify_playlist.choices = spotify_choices
	form.google_playlist.choices = google_choices

	if form.validate_on_submit():
		p = playlist.Playlist({})

		p.spotify_playlist_name = dict(spotify_choices).get(form.spotify_playlist.data)
		p.spotify_playlist_id = form.spotify_playlist.data

		p.google_playlist_name = dict(google_choices).get(form.google_playlist.data)
		p.google_playlist_id = form.google_playlist.data

		p.master = form.master.data

		r = p.save()

		return redirect('/playlists/modify/' + str(r.inserted_id))


	return render_template('playlists/create.html',
							title='Create a Playlist',
							form=form)

@app.route('/playlists/<string:playlist_id>', methods=['GET', 'POST'])
@user.login_required
def view_playlist(playlist_id):
	p = playlist.get_playlist(playlist_id)
	return render_template('playlists/playlist.html',
							title='View Playlist',
							playlist=p)

@app.route('/playlists/modify/<string:playlist_id>', methods=['GET', 'POST'])
@user.login_required
def modify_playlist(playlist_id):
	p = playlist.get_playlist(playlist_id)
	return render_template('playlists/modify.html',
							title='Modify Playlist',
							playlist=p)


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
	if request.args.get('code'):
		s = spotify.Spotify(user.current_user)
		s.connect()
	else:
		flash(request.args.get('error'))

	return redirect('/account')

@app.route('/test')
@user.login_required
def test_method():
	s = spotify.Spotify(user.current_user)
	r = s.get_user_playlists()

	return str(r)
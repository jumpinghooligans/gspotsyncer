# Flask
from flask import render_template, request, flash, redirect

# Forms
from .forms import CreateForm, LoginForm, UserAccountForm

# Service Manipulation
from app import app, gmusic, spotify, user, playlist

# General imports
import urllib, urllib2, base64, json

spotify_config = {
	'client_id' : 'cf030653cc244fcdac4d7e91bcb634e7',
	'client_secret' : '456a5944f54d43a59d178e1a80210bdf',
	'redirect_uri' : 'http://localhost:5000/spotify/return'
}

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
		new_user = {
			'username' : form.username.data,
			'password' : form.password.data
		}
		user.register(new_user)
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

@app.route('/account/playlists', methods=['GET', 'POST'])
@user.login_required
def playlists():
	playlists = []

	p = playlist.Playlist({})
	p.save()

	return render_template('account/playlists.html',
							title='Playlists',
							playlists=playlists)

@app.route('/google')
@user.login_required
def google_playlists():
	g = gmusic.GoogleMusic(user.current_user)
	playlists = g.get_full_playlists()

	return render_template('google/index.html',
							title='Google Playlists',
							playlists=playlists)


@app.route('/spotify')
@user.login_required
def spotify_playlists():
	s = spotify.Spotify(user.current_user)
	playlists = s.get_playlists()

	app.logger.info(playlists)

	return render_template('spotify/index.html',
							title='Spotify Playlists',
							playlists=playlists)
	

@app.route('/google/search', methods=['GET', 'POST'])
@user.login_required
def google_search():
	results = []

	if request.method == 'POST':
		g = gmusic.GoogleMusic(user.current_user)

		query = request.form.get("query")
		results = g.search_songs(query)

		app.logger.info(results)

	return render_template('google/search.html',
							title='Google Search',
							results=results)

@app.route('/spotify/connect')
def spotify_connect():
	scope = " ".join(['playlist-read-private',
		'playlist-read-collaborative',
		'playlist-modify-public',
		'playlist-modify-private'])

	params = {
		'response_type' : 'code',
		'client_id' : spotify_config['client_id'],
		'scope' : scope,
		'redirect_uri' : spotify_config['redirect_uri']
	}

	spotify = 'https://accounts.spotify.com/authorize?' + urllib.urlencode(params)

	return redirect(spotify)

@app.route('/spotify/return')
def spotify_return():
	if request.args.get('code'):

		# get and store auth codes
		spotify_auth_request = urllib2.Request('https://accounts.spotify.com/api/token')
		spotify_auth_request.add_header('Authorization', 'Basic ' + base64.b64encode(spotify_config['client_id'] + ':' + spotify_config['client_secret']))
		params = {
			'grant_type' : 'authorization_code',
			'code' : request.args.get('code'),
			'redirect_uri' : spotify_config['redirect_uri']
		}

		try:
			spotify_auth_response = urllib2.urlopen(spotify_auth_request, urllib.urlencode(params)).read()
			spotify_credentials = json.loads(spotify_auth_response)

			user.current_user.spotify_credentials = spotify_credentials
			if user.current_user.save():
				flash('Successfully updated Spotify credentials...')
			else:
				flash('Unknown error updating Spotify credentials...')

			return redirect('/account')
		except urllib2.HTTPError as err:
			response = json.loads(err.fp.read())
			flash(response)

		return redirect('/account')

	else:
		flash(request.args.get('error'))
		return redirect('/account')
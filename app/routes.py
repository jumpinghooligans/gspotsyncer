from app import app

# Flask
from flask import render_template, request, flash, redirect
from flask_dynamo import Dynamo

# Forms
from .forms import CreateForm, LoginForm, UserAccountForm

# Service Manipulation
from app import gmusic

# User management
from app import user

dynamo = Dynamo(app)

@app.route('/', methods=['GET', 'POST'])
def index():
	return render_template('index.html',
							title='Home')

@app.route('/login', methods=['GET', 'POST'])
@app.route('/account/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()

	if form.validate_on_submit():
		user.attempt_login(form.username.data, form.password.data)
		
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
		user.create_user(new_user)

	return render_template('account/create.html',
							title='Login',
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
@app.route('/google')
@user.login_required
def google():
	g = gmusic.GoogleMusic(user.current_user)
	playlists = g.get_full_playlists()

	return render_template('google/index.html',
							title='Google Playlists',
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
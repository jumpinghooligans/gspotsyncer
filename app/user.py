from app import app, mongo, gmusic, spotify
import md5

from flask import flash
from flask_login import LoginManager, AnonymousUserMixin, UserMixin, login_user, logout_user, login_required, current_user

# session management
login_manager = LoginManager()
login_manager.init_app(app)

# redirects and flash messages
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(username):
	user = mongo.db.users.find_one({ 'username' : username })

	if user:
		return User(user)

	return None

def register(user_obj):
	try:
		exists = mongo.db.users.find_one({ 'username' : user_obj['username'] })

		if exists:
			flash('Username already exists')
			return

		insert_result = mongo.db.users.insert_one({
			'username' : user_obj['username'],
			'password' : hash_hex(user_obj['password'])
		})

		new_user = mongo.db.users.find_one({ '_id' : insert_result.inserted_id })
		login_user(User(new_user))

	except Exception, e:
		flash(e.message)

def login(username, password):
	# Check the user password combination
	user_data = None
	try:
		user_data = mongo.db.users.find_one({ 'username' : username })
	except Exception, e:
		pass

	# Found the user
	if user_data:
		app.logger.info('Found ' + username + ', checking password')

		attempted_pw = md5.new(password)
		current_pw = user_data.get('password')

		app.logger.info(current_pw)

		if attempted_pw.hexdigest() == current_pw:
			# Password matches, we can return a user
			app.logger.info('Successful login for ' + username)
			user = User(user_data)

			# Set him as 'logged in'
			login_user(user)
			return

	flash('Incorrect username or password.')

def hash_hex(s):
	return md5.new(s).hexdigest()


# User Object
class User(UserMixin):
	def __init__(self, user):
		app.logger.info('Returning user ' + user.get('username'))

		for key, value in user.items():
			setattr(self, key, value)

	def get_id(self):
		return self.username

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def is_authenticated(self):
		return bool(self.username)

	def can_modify_playlist(self):
		if not hasattr(self, 'google_credentials'):
			return False

		if not hasattr(self, 'spotify_credentials'):
			return False

		return True

	def save(self):
		user = {}

		# update the mongo doc
		for obj in vars(self):
			user[obj] = getattr(self, obj)

		# save to db
		return mongo.db.users.save(user)
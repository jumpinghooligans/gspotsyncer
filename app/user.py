from app import app
import md5

from flask import flash
from flask_dynamo import Dynamo
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# db
dynamo = Dynamo(app)

# session management
login_manager = LoginManager()
login_manager.init_app(app)

# redirects and flash messages
login_manager.login_view = "login"

def create_user(user_obj):
	try:
		dynamo.users.put_item(data={
			'username' : user_obj['username'],
			'password' : hash_hex(user_obj['password'])
		})
	except Exception, e:
		flash(e.message)

def hash_hex(s):
	return md5.new(s).hexdigest()

def attempt_login(username, password):
	# Check the user password combination
	user_data = None
	try:
		user_data = dynamo.users.get_item(username=username)
	except Exception, e:
		pass

	# Found the user
	if user_data:
		app.logger.info('Found ' + username + ', checking password')

		attempted_pw = md5.new(password)
		current_pw = user_data.get('password')

		if attempted_pw.hexdigest() == current_pw:
			# Password matches, we can return a user
			app.logger.info('Successful login for ' + username)
			user = User(user_data)

			# Set him as 'logged in'
			login_user(user)
			return

	flash('Incorrect username or password.')


@login_manager.user_loader
def load_user(username):
	user = dynamo.users.get_item(username=username)

	if user:
		return User(user)

	return None


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

	def new_user(self):
		return {
			username : ''
		}

	def save(self):
		user = dynamo.users.get_item(username=self.username)

		# update the dynamo obj
		for obj in vars(self):
			user[obj] = getattr(self, obj)

		# save to db
		return user.save(overwrite=True)
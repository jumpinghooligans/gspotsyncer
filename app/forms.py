from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, RadioField

from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
	username = StringField('username', validators=[DataRequired()])
	password = PasswordField('password', validators=[DataRequired()])
	remember_me = BooleanField('remember_me', default=False)

class CreateForm(FlaskForm):
	username = StringField('username', validators=[DataRequired()])
	password = PasswordField('password', validators=[DataRequired()])
	password_confirm = PasswordField('password_confirm', validators=[DataRequired()])

class UserAccountForm(FlaskForm):
	password = PasswordField('password')
	google_id = StringField('google_id')
	google_password = PasswordField('google_password')

class CreatePlaylistForm(FlaskForm):
	playlist_type = SelectField('playlist_type', choices=[ ( 'masterslave', 'Master / Slave' )])
	spotify_playlist = SelectField('spotify_playlist', choices=[ ( 'n', 'None' )])
	google_playlist = SelectField('google_playlist', choices=[ ( 'n', 'None' )])
	master = RadioField('master', choices=[('spotify','Spotify'),('google','Google')])

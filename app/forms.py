from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, RadioField, SubmitField

from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
	username = StringField(
		label='Username',
		validators=[DataRequired()]
	)

	password = PasswordField(
		label='Password',
		validators=[DataRequired()]
	)


class CreateForm(FlaskForm):
	username = StringField(
		label='Username',
		validators=[DataRequired()]
	)

	password = PasswordField(
		label='Password',
		validators=[DataRequired()]
	)

	password_confirm = PasswordField(
		label='Confirm Password',
		validators=[DataRequired()]
	)


class UserAccountForm(FlaskForm):
	password = PasswordField(label='password')

	update_account = SubmitField("Update Account")


class GoogleCredentialsForm(FlaskForm):
	google_id = StringField(
		label='Google ID',
		validators=[DataRequired()]
	)

	google_password = PasswordField(
		label='Google Password',
		validators=[DataRequired()]
	)

	update_google = SubmitField("Update Google")


class CreatePlaylistForm(FlaskForm):
	playlist_type = SelectField(
		label='Playlist Sync Type',
		choices=[ ( 'masterslave', 'Master / Slave' )]
	)

	master = SelectField(
		label='Master',
		choices=[('spotify','Spotify'),('google','Google')]
	)

	spotify_playlist = SelectField(
		label='Spotify Playlist',
		choices=[ ( '', 'Select a Playlist' )]
	)

	spotify_create = StringField(
		label='New Playlist Name'
	)

	google_playlist = SelectField(
		label='Google Music Playlist',
		choices=[ ( '', 'Select a Playlist' )]
	)

	google_create = StringField(
		label='New Playlist Name'
	)


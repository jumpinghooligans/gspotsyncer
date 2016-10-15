#!flask/bin/python
import os
import unittest

# from config import basedir
from app import app, mongo

from flask import Flask
from flask_login import current_user
from flask_testing import TestCase

class TestCase(TestCase):

	def setUp(self):
		pass

	def create_app(self):
		app.config['TESTING'] = True
		app.config['WTF_CSRF_ENABLED'] = False
		app.config['SESSION_COOKIE_DOMAIN'] = None

		self.app = app
		self.client = self.app.test_client()

		self.test_user = {
			'username' : 'asdf',
			'password' : 'asdf',
			'google_id' : '',
			'google_password' : ''
		}

		return app

	@classmethod
	def setUpClass(cls):
		# drop our whole database erry test
		with app.app_context():
			mongo.cx.drop_database(app.config['TEST_MONGO_DBNAME'])

	def test_connection(self):
		response = self.client.get('/')
		assert response.status_code is 200

	def test_create_user(self):
		response = self.client.post('/account/create', data={
			'username' : self.test_user.get('username'),
			'password' : self.test_user.get('password'),
			'password_confirm' : self.test_user.get('password')
		}, follow_redirects=False)

		self.assertRedirects(response, '/account', 'Failed to create account')

	def test_login_user(self):
		response = self.login()
		self.assertRedirects(response, '/account', 'Failed to log user in')

	def test_get_account(self):
		self.login()

		response = self.client.get('/account', follow_redirects=False)

		# :(
		assert self.test_user.get('username') + "'s account" in response.data

	def test_get_playlists(self):
		self.login()

		response = self.client.get('/playlists', follow_redirects=False)

		# :(
		assert "You don't seem to have any playlists yet..." in response.data

	def login(self):
		return self.client.post('/account/login', data={
			'username' : self.test_user.get('username'),
			'password' : self.test_user.get('password'),
		}, follow_redirects=False)

if __name__ == '__main__':
	unittest.main()
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

		self.app = app
		self.client = self.app.test_client()

		return app

	def tearDown(self):
		# drop our whole database erry test
		mongo.cx.drop_database(app.config['TEST_MONGO_DBNAME'])

	def test_connection(self):
		response = self.client.get('/')
		assert response.status_code is 200

	def test_create(self):
		response = self.client.post('/account/create', data={
			'username' : 'asdf',
			'password' : 'asdf',
			'password_confirm' : 'asdf'
		}, follow_redirects=False)
		# print response.data
		self.assertRedirects(response, '/account', 'Failed to create account')

	def test_logout_login(self):
		response = self.client.post('/account/create', data={
			'username' : 'asdf',
			'password' : 'asdf',
			'password_confirm' : 'asdf'
		}, follow_redirects=False)

		self.assertRedirects(response, '/account', 'Failed to create account')

		response = self.client.get('/account/logout')
		self.assertRedirects(response, '/', 'Failed to log user out')

		response = self.client.post('/account/login', data={
			'username' : 'asdf',
			'password' : 'asdf'
		}, follow_redirects=False)
		self.assertRedirects(response, '/account', 'Failed to log user in')

if __name__ == '__main__':
	unittest.main()
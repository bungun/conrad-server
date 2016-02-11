import os
import conrad_server as cserver
import unittest
import tempfile
from flask import json

class ConradServerTestCase(unittest.TestCase):
	def setUp(self):
		cserver.app.config['TESTING'] = True
		cserver.app.config['USERNAME'] = 'admin'
		cserver.app.config['PASSWORD'] = 'default'

		self.app = cserver.app.test_client()
		self.jheader = {'Content-Type' : 'application/json'}
		# database setup would go here

	def tearDown(self):
		pass
		# database teardown would go here

	def login(self, username, password):
		data = dict(username = username, password = password)
		return json.loads(self.app.get('/login/', 
			data = json.dumps(data), headers = self.jheader).data)

	def logout(self):
		return json.loads(self.app.get('/logout/').data)

	def test_login_logout(self):
	    rv = self.login('admin', 'default')
	    assert rv['success']
	    assert rv['message'] == 'You were logged in'
	    rv = self.logout()
	    assert rv['success']
	    assert rv['message'] == 'You were logged out'
	    rv = self.login('adminx', 'default')
	    assert not rv['success']
	    assert rv['message'] == 'Invalid username'
	    rv = self.login('admin', 'defaultx')
	    assert not rv['success']
	    assert rv['message'] == 'Invalid password'

if __name__ == '__main__':
	unittest.main()

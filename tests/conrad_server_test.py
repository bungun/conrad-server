import os
import conrad_server as cserver
import unittest
import tempfile
from flask import json

UNSESSIONED_MESSAGE = 'unsessioned'
SESSIONED_MESSAGE = 'sessioned'
TESTCASE = 'TEST CASE'
TESTUSER = 'admin'
TESTPASS = 'default'

class ConradServerTestCase(unittest.TestCase):
	def setUp(self):
		cserver.app.config['TESTING'] = True
		cserver.app.config['USERNAME'] = TESTUSER
		cserver.app.config['PASSWORD'] = TESTPASS

		self.app = cserver.app.test_client()
		self.jheader = {'Content-Type' : 'application/json'}
		self.__CASE_MADE__ = False
		self.__STRUCTURES_MADE__ = False
		self.structure_labels = None
		self.structure_info = None
		self.constraintIDs = None
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
		rv = self.login(TESTUSER, TESTPASS)
		self.assertTrue(rv['success'])
		self.assertEqual(rv['message'], 'You were logged in')
		rv = self.logout()
		self.assertTrue(rv['success'])
		self.assertEqual(rv['message'], 'You were logged out')
		rv = self.login(TESTUSER + 'x', TESTPASS)
		self.assertFalse(rv['success'])
		self.assertEqual(rv['message'], 'Invalid username')
		rv = self.login(TESTUSER, TESTPASS + 'x')
		self.assertFalse(rv['success'])
		self.assertEqual(rv['message'], 'Invalid password')
	
	def test_session(self):
		rv = json.loads(self.app.get('/_check_session/').data)
		self.assertFalse(rv['success'])
		self.assertEqual(rv['message'], UNSESSIONED_MESSAGE)
		self.login(TESTUSER, TESTPASS)	
		rv = json.loads(self.app.get('/_check_session/').data)
		self.assertTrue(rv['success'])
		self.assertEqual(rv['message'], SESSIONED_MESSAGE)

	def test_make_testcase(self):
		self.login(TESTUSER, TESTPASS)	
		rv = json.loads(self.app.get('/_make_test_case/').data)
		self.assertTrue(rv['success'])

	def test_caselist(self):
		self.login(TESTUSER, TESTPASS)	

		rv = json.loads(self.app.get('/_cases/').data)
		self.assertTrue(isinstance(rv['cases'], list))
		
		if not TESTCASE is rv['cases']:
			self.app.get('/_make_test_case/')

		rv = json.loads(self.app.get('/_cases/').data)
		print rv['cases']
		self.assertTrue(TESTCASE in rv['cases'])

	def test_setcase(self):
		self.login(TESTUSER, TESTPASS)	
		self.app.get('/_make_test_case/')

		rv = json.loads(self.app.get('/_select_case/', 
			data = json.dumps({'case': None}),
			headers = self.jheader).data)
		rv = json.loads(self.app.get('/_select_case/', 
			data = json.dumps({'case': 'GIBBERISH'}),
			headers = self.jheader).data)
		self.assertFalse(rv['success'])
		rv = json.loads(self.app.get('/_select_case/', 
			data = json.dumps({'case': TESTCASE}),
			headers = self.jheader).data)
		self.assertTrue(rv['success'])

	def set_default_case(self):
		if self.__CASE_MADE__: return
		self.login(TESTUSER, TESTPASS)	
		self.app.get('/_make_test_case/')
		self.app.get('/_select_case/', 
			data = json.dumps({'case': TESTCASE}),
			headers = self.jheader)
		self.__CASE_MADE__ = True

	def test_getstructures(self):
		self.set_default_case()
		rv = json.loads(self.app.get('/_structure_labels/').data)
		self.assertTrue(rv['success'])
		self.assertTrue('labels' in rv)
		self.assertTrue(isinstance(rv['labels'], list))
		self.assertTrue(len(rv['labels']) > 0)
		structure_labels = rv['labels']

		rv = json.loads(self.app.get('/_structure_info/').data)
		self.assertTrue(rv['success'])
		self.assertTrue('structures' in rv)
		self.assertTrue(isinstance(rv['structures'], dict))
		structures = rv['structures']
		for l in structure_labels:
			self.assertTrue(str(l) in structures.keys())

	def set_default_structures(self):
		if self.__STRUCTURES_MADE__: return
		self.set_default_case()
		self.structure_labels = json.loads(
			self.app.get('/_structure_labels/').data)['labels']
		rv = json.loads(self.app.get('/_structure_info/').data)
		self.structure_info = rv['structures']
		self.__STRUCTURES_MADE__ = True


	def test_dose_constraints(self):
		self.set_default_structures()

		rv = json.loads(self.app.get('/_constraint_data/').data)
		self.assertTrue(rv['success'])
		self.assertTrue('constraintData' in rv.keys())
		constraints = rv['constraintData']

		orig_constraint_count = 0

		for l in self.structure_labels:
			self.assertTrue(str(l) in constraints.keys())
			self.assertTrue(isinstance(constraints[str(l)], list))
			for c in constraints[str(l)]:
				orig_constraint_count += 1
				for token in ['constraintID', 'percentile', 'dose', 'symbol']:
					self.assertTrue(token in c.keys())

			# test add
			direction = '>' if self.structure_info[str(l)]['is_target'] else '<'

			constr = {'structureLabel': l, 'dose': 0.5, 'percentile': 50, 
				'direction': direction}
			rv = json.loads(self.app.get('/_add_dvh_constraint/', data = json.dumps(
				constr), headers = self.jheader).data)
			self.assertTrue(rv['success'])
			cid = rv['constraintID']

			# test change
			rv = json.loads(self.app.get('/_change_dvh_constraint/', 
				data = json.dumps({'constraintID': cid,
					'dose': 0.8, 'percentile': 10, 'direction': '<'}), 
				headers = self.jheader).data)
			self.assertTrue(rv['success'])

			rv = json.loads(self.app.get('/_change_dvh_constraint/', 
				data = json.dumps({'constraintID': cid,
					'dose': 0.8, 'fraction': 0.1, 'direction': '<'}), 
				headers = self.jheader).data)
			self.assertTrue(rv['success'])

			# test drop
			rv = json.loads(self.app.get('/_drop_dvh_constraint/', 
				data = json.dumps({'constraintID': cid}), 
				headers = self.jheader).data)
			self.assertTrue(rv['success'])	

		# TODO: test drop all
		# TODO: test drop all but rx
		# TODO: test add all rx


	def change_objective(self, label, dose = None, 
		w_under = None, w_over = None):

		obj = {'structureLabel': label, 'dose': dose, 
			'w_under': w_under, 'w_over': w_over}
		return json.loads(self.app.get('/_change_objective/',
			data = json.dumps(obj), headers = self.jheader).data)

	def get_objective(self, label):
		return json.loads(self.app.get('/_single_objective/',
			data = json.dumps({'structureLabel': label}), headers = self.jheader).data)


	def test_objective(self):
		self.set_default_structures()

		rv = json.loads(self.app.get('/_objectives/').data)
		self.assertTrue(rv['success'])
		self.assertTrue('objectives' in rv.keys())
		objectives = rv['objectives']

		for l in self.structure_labels:
			self.assertTrue(str(l) in objectives.keys())
			o = objectives[str(l)]
			for token in ['dose_rx', 'dose_solver', 'w_under', 'w_over']:
				self.assertTrue(token in o.keys())
			self.assertEqual(o['dose_rx'], o['dose_solver'])

			# change objective, verify
			if o['dose_rx'] > 0:
				# change dose (target only)
				orig_dose = o['dose_solver']
				req_dose = orig_dose * 1.3

				self.change_objective(l, dose = req_dose)
				rv =  self.get_objective(l)
				self.assertTrue(rv['success'])
				new_dose = rv['objectives']['dose_solver']
				self.assertAlmostEqual(req_dose, new_dose, places = 1) 

				# change w_under (target only)
				orig_w = o['w_under']
				req_w = orig_w * 5

				self.change_objective(l, dose = req_w)
				rv = self.get_objective(l)
				self.assertTrue(rv['success'])
				new_w = rv['objectives']['w_under']
				self.assertAlmostEqual(req_w, new_w, places = 1) 

			# change w_over (targ/nontarg)
			orig_w = o['w_over']
			req_w = orig_w / 5.

			self.change_objective(l, dose = req_w)
			rv = self.get_objective(l)
			self.assertTrue(rv['success'])
			new_w = rv['objectives']['w_over']
			self.assertAlmostEqual(req_w, new_w, places = 1) 



	def test_optimization(self):
		self.set_default_structures()

		# TODO: tests for other optimization input parameters (including invalid)
		rv = json.loads(self.app.get('/_run_optimization/',
			data = json.dumps({'dummy': None}), headers = self.jheader).data)
		self.assertTrue(rv['success'])

		if rv['success']:
			rv = json.loads(self.app.get('/_plotting_data/').data)
			self.assertTrue(rv['success'])
			self.assertTrue('plottingData' in rv.keys())
			pd = rv['plottingData']
			for l in self.structure_labels:
				self.assertTrue(str(l) in pd.keys())
				self.assertTrue('curve' in pd[str(l)].keys())
				self.assertTrue('percentile' in pd[str(l)]['curve'].keys())
				self.assertTrue('dose' in pd[str(l)]['curve'].keys())
				dose = pd[str(l)]['curve']['dose']
				percentile = pd[str(l)]['curve']['percentile']
				self.assertTrue(isinstance(dose, list))
				self.assertTrue(isinstance(percentile, list))
				self.assertEqual(len(dose), len(percentile))
				self.assertEqual(dose[0], 0)
				self.assertEqual(percentile[0], 100)
				self.assertTrue('constraints' in pd[str(l)].keys())
				self.assertTrue(isinstance(pd[str(l)]['constraints'], list))
				constraints = pd[str(l)]['constraints']
				for c in constraints:
					for token in ['constraintID', 'percentile', 'dose', 'symbol']:
						self.assertTrue(token in c.keys())



if __name__ == '__main__':
	unittest.main()

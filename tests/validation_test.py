import unittest
from validation import InputValidator
from conrad_server import build_test_case

class ValidatorTestCase(unittest.TestCase):
	def setUp(self):
		self.case = build_test_case()
		self.validator = InputValidator(self.case)

	def tearDown(self):
		pass

	def test_utils(self):
		# float util
		self.assertFalse(self.validator._InputValidator__str_is_float('a2a.s'))
		self.assertTrue(self.validator._InputValidator__str_is_float('112'))
		self.assertTrue(self.validator._InputValidator__str_is_float('11.2'))
		self.assertTrue(self.validator._InputValidator__str_is_float('1e-3'))
		self.assertTrue(self.validator._InputValidator__str_is_float('1.2e+5'))

		# bool util
		self.assertTrue(self.validator._InputValidator__boolable(False))
		self.assertTrue(self.validator._InputValidator__boolable(True))
		self.assertTrue(self.validator._InputValidator__boolable(0))
		self.assertTrue(self.validator._InputValidator__boolable(1))
		self.assertTrue(self.validator._InputValidator__boolable(2))			
		self.assertTrue(self.validator._InputValidator__boolable(-2))		
		self.assertFalse(self.validator._InputValidator__boolable(1.2))
		self.assertFalse(self.validator._InputValidator__boolable(0.00))
		self.assertTrue(self.validator._InputValidator__boolable('1'))
		self.assertTrue(self.validator._InputValidator__boolable('10'))
		self.assertTrue(self.validator._InputValidator__boolable('true'))
		self.assertTrue(self.validator._InputValidator__boolable('True'))
		self.assertTrue(self.validator._InputValidator__boolable('false'))
		self.assertTrue(self.validator._InputValidator__boolable('False'))
		self.assertFalse(self.validator._InputValidator__boolable('1.0'))
		self.assertFalse(self.validator._InputValidator__boolable('1x'))

		# int util
		self.assertTrue(self.validator._InputValidator__intable(112))
		self.assertTrue(self.validator._InputValidator__intable(True))
		self.assertTrue(self.validator._InputValidator__intable(False))
		self.assertTrue(self.validator._InputValidator__intable(True))
		self.assertTrue(self.validator._InputValidator__intable(12.2))
		self.assertTrue(self.validator._InputValidator__intable('11'))
		self.assertFalse(self.validator._InputValidator__intable('11.0'))

	def label_is_valid(self, label):
		return isinstance(self.validator.validate_structure_label(label), int)

	def test_structure_label(self):
		valid_labels = self.case.structures.keys()
		valid_set = set(valid_labels)

		self.assertTrue(len(valid_labels) > 0)

		for l in valid_labels:
			self.assertTrue(self.label_is_valid(l))
			self.assertTrue(self.label_is_valid(str(l)))
			self.assertTrue(self.label_is_valid(float(l)))

			l_perturb = l
			while l_perturb in valid_set: l_perturb += 1

			self.assertFalse(self.label_is_valid(l_perturb))

		self.assertFalse(self.label_is_valid(None))
		self.assertFalse(self.label_is_valid('None'))

	def test_constraint_id(self):
		valid_ids = self.case.active_constraint_IDs

		for cid in valid_ids:
			self.assertTrue(self.validator.validate_constraintID(cid))

		self.assertFalse(self.validator.validate_constraintID('randomID'))


	def constraint_is_valid(self, dose, percentile, fraction, direction):
		return self.validator.validate_dvh_constraint(dose, percentile, 
			fraction, direction)['valid']

	def test_dvh_constraint(self):
		# test no input
		self.assertFalse(self.constraint_is_valid(None, None, None, None))

		# test direction input
		self.assertFalse(self.constraint_is_valid(None, None, None, '='))
		self.assertTrue(self.constraint_is_valid(None, None, None, '<='))
		self.assertTrue(self.constraint_is_valid(None, None, None, '>='))
		self.assertTrue(self.constraint_is_valid(None, None, None, '<'))
		self.assertTrue(self.constraint_is_valid(None, None, None, '>'))

		# test fraction input
		self.assertTrue(self.constraint_is_valid(None, None, 0, None))
		self.assertTrue(self.constraint_is_valid(None, None, 0.5, None))
		self.assertTrue(self.constraint_is_valid(None, None, 1, None))
		self.assertFalse(self.constraint_is_valid(None, None, -0.1, None))
		self.assertFalse(self.constraint_is_valid(None, None, 1.1, None))
		self.assertTrue(self.constraint_is_valid(None, None, '0', None))
		self.assertTrue(self.constraint_is_valid(None, None, '0.5', None))
		self.assertTrue(self.constraint_is_valid(None, None, '1', None))
		self.assertFalse(self.constraint_is_valid(None, None, '-0.1', None))
		self.assertFalse(self.constraint_is_valid(None, None, '1.1', None))
		self.assertFalse(self.constraint_is_valid(None, None, 'gibberish', None))

		# test percentile input
		self.assertTrue(self.constraint_is_valid(None, 0, None, None))
		self.assertTrue(self.constraint_is_valid(None, 50, None, None))
		self.assertTrue(self.constraint_is_valid(None, 98.2, None, None))
		self.assertTrue(self.constraint_is_valid(None, 100,  None,None))
		self.assertFalse(self.constraint_is_valid(None, -10,  None, None))
		self.assertFalse(self.constraint_is_valid(None, 110, None, None))
		self.assertTrue(self.constraint_is_valid(None, '0', None, None))
		self.assertTrue(self.constraint_is_valid(None, '50', None, None))
		self.assertTrue(self.constraint_is_valid(None, '98.2', None, None))
		self.assertTrue(self.constraint_is_valid(None, '100',  None,None))
		self.assertFalse(self.constraint_is_valid(None, '-10',  None, None))
		self.assertFalse(self.constraint_is_valid(None, '110', None, None))
		self.assertFalse(self.constraint_is_valid(None, 'gibberish', None, None))

		# test percentile input superceding fraction input but not vice-versa
		self.assertTrue(self.constraint_is_valid(None, '13.2', 'gibberish', None))
		self.assertFalse(self.constraint_is_valid(None, 'gibberish', '0.132', None))

		# test dose input
		self.assertTrue(self.constraint_is_valid(13, None, None, None))
		self.assertTrue(self.constraint_is_valid(13.7, None, None, None))
		self.assertTrue(self.constraint_is_valid('13', None, None, None))
		self.assertTrue(self.constraint_is_valid('13.7', None, None, None))
		self.assertFalse(self.constraint_is_valid(-0.1, None, None, None))
		self.assertFalse(self.constraint_is_valid('-0.1', None, None, None))
		self.assertFalse(self.constraint_is_valid('gibberish', None, None, None))

		# test combinations (not exhaustive):
		self.assertTrue(self.constraint_is_valid('13.7', None, None, '<'))
		self.assertTrue(self.constraint_is_valid(None, '44', None, '<'))
		self.assertTrue(self.constraint_is_valid(None, None, '0.44', '<'))
		self.assertTrue(self.constraint_is_valid('13.7', '44', None, '<'))
		self.assertTrue(self.constraint_is_valid('13.7', None, '0.44', '<'))

	def objective_is_valid(self, label, dose, w_under, w_over):
		return self.validator.validate_objective(label, 
			dose, w_under, w_over)['valid']

	def test_objective(self):
		valid_labels = self.case.structures.keys()
		valid_set = set(valid_labels)
		invalid_labels = []


		self.assertTrue(len(valid_labels) > 0)

		for l in valid_labels:
			l_perturb = l
			while l_perturb in valid_set: l_perturb += 1
			invalid_labels.append(l_perturb)

		for l in valid_labels:
			if self.case.structures[l].is_target:

				# test no input:
				self.assertFalse(self.objective_is_valid(l, None, None, None))

				# test dose:
				self.assertTrue(self.objective_is_valid(l, 10.2, None, None))
				self.assertTrue(self.objective_is_valid(l, '10.2', None, None))
				self.assertFalse(self.objective_is_valid(l, -10.2, None, None))
				self.assertFalse(self.objective_is_valid(l, '-10.2', None, None))

				# test w_under:
				self.assertTrue(self.objective_is_valid(l, None, 0.2, None))
				self.assertTrue(self.objective_is_valid(l, None, 2e-1, None))
				self.assertTrue(self.objective_is_valid(l, None, '0.2', None))
				self.assertTrue(self.objective_is_valid(l, None, '2e-1', None))
				self.assertFalse(self.objective_is_valid(l, None, -2e-1, None))
				self.assertFalse(self.objective_is_valid(l, None, '-2e-1', None))

				# test w_over:
				self.assertTrue(self.objective_is_valid(l, None, None, 0.2))
				self.assertTrue(self.objective_is_valid(l, None, None, 2e-1))
				self.assertTrue(self.objective_is_valid(l, None, None, '0.2'))
				self.assertTrue(self.objective_is_valid(l, None, None, '2e-1'))
				self.assertFalse(self.objective_is_valid(l, None, None, -2e-1))
				self.assertFalse(self.objective_is_valid(l, None, None, '-2e-1'))

				# test combinations (not exhaustive):
				self.assertTrue(self.objective_is_valid(l, 32, 0.2, 0.1))
				self.assertTrue(self.objective_is_valid(l, '32', '0.2', '0.1'))
				self.assertTrue(self.objective_is_valid(l, None, None, '0.1'))
				self.assertTrue(self.objective_is_valid(l, None, '0.2', '0.1'))
				self.assertTrue(self.objective_is_valid(l, '32', None, '0.1'))
				self.assertTrue(self.objective_is_valid(l, '32', None, None))
				self.assertTrue(self.objective_is_valid(l, '32', '0.2', None))
				self.assertTrue(self.objective_is_valid(l, None, '0.2', None))

				self.assertFalse(self.objective_is_valid(l, 'gibberish', '0.2', '0.1'))
				self.assertFalse(self.objective_is_valid(l, '32', 'gibberish', '0.1'))
				self.assertFalse(self.objective_is_valid(l, '32', '0.2', 'gibberish'))
				self.assertFalse(self.objective_is_valid(l, -32, 0.2, 0.1))
				self.assertFalse(self.objective_is_valid(l, 32, -0.2, 0.1))
				self.assertFalse(self.objective_is_valid(l, 32, 0.2, -0.1))
				self.assertFalse(self.objective_is_valid(l, '-32', 0.2, 0.1))
				self.assertFalse(self.objective_is_valid(l, '32', -0.2, 0.1))
				self.assertFalse(self.objective_is_valid(l, '32', 0.2, -0.1))
				self.assertFalse(self.objective_is_valid(l, -32, '0.2', 0.1))
				self.assertFalse(self.objective_is_valid(l, 32, '-0.2', 0.1))
				self.assertFalse(self.objective_is_valid(l, 32, '0.2', -0.1))
				self.assertFalse(self.objective_is_valid(l, -32, 0.2, '0.1'))
				self.assertFalse(self.objective_is_valid(l, 32, -0.2, '0.1'))
				self.assertFalse(self.objective_is_valid(l, 32, 0.2, '-0.1'))

			else:
				# test no input:
				self.assertFalse(self.objective_is_valid(l, 32.2, None, None))
				self.assertFalse(self.objective_is_valid(l, '32.2', None, None))
				self.assertFalse(self.objective_is_valid(l, None, 0.2, None))
				self.assertFalse(self.objective_is_valid(l, None, '0.2', None))

				self.assertFalse(self.objective_is_valid(l, 32.2, 0.2, None))
				self.assertFalse(self.objective_is_valid(l, '32.2', '0.2', None))

				# test w_over
				self.assertTrue(self.objective_is_valid(l, None, None, 0.2))
				self.assertTrue(self.objective_is_valid(l, None, None, 2e-1))
				self.assertTrue(self.objective_is_valid(l, None, None, '0.2'))
				self.assertTrue(self.objective_is_valid(l, None, None, '2e-1'))
				self.assertFalse(self.objective_is_valid(l, None, None, -2e-1))
				self.assertFalse(self.objective_is_valid(l, None, None, '-2e-1'))

		# test bad label
		for il in invalid_labels:
			self.assertFalse(self.objective_is_valid(il, 37, 0.3, 0.2))
			self.assertFalse(self.objective_is_valid(il, '37', 0.3, 0.2))
			self.assertFalse(self.objective_is_valid(il, '37', '0.3', 0.2))
			self.assertFalse(self.objective_is_valid(il, '37', '0.3', '0.2'))


	def solve_valid(self, use_2pass, use_slack, solver, verbose):
		return self.validator.validate_solve(use_2pass, use_slack, solver, verbose)['valid']

	def test_solve(self):
		MAX_VERBOSITY = self.validator.MAX_VERBOSITY
		SOLVER_OPTIONS = self.validator.SOLVER_OPTIONS

		for solver in SOLVER_OPTIONS:
			for slack in [True, False, 'True', 'False', 'true', 'false']:
				for two_pass in [True, False, 'True', 'False', 'true', 'false']:
					for verbose in [True, False, 'True', 'False', 0, 1, 2, '0', '1', '2']:
						self.assertTrue(self.solve_valid(two_pass, slack, solver, verbose))

						for perturb in ['gibberish', None]:
							self.assertFalse(self.solve_valid(two_pass, slack, solver, perturb))
							self.assertFalse(self.solve_valid(two_pass, slack, perturb, verbose))
							self.assertFalse(self.solve_valid(two_pass, perturb, solver, verbose))
							self.assertFalse(self.solve_valid(perturb, slack, solver, verbose))

			self.assertTrue(self.validator.validate_solve(
				True, True, solver, MAX_VERBOSITY + 1)['verbose'] <= MAX_VERBOSITY)



if __name__ == '__main__':
	unittest.main()
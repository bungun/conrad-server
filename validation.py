from conrad.defs import SOLVER_OPTIONS, MAX_VERBOSITY

class InputValidator(object):
    def __init__(self, case):
        self.case = case
        self.SOLVER_OPTIONS = SOLVER_OPTIONS
        self.MAX_VERBOSITY = MAX_VERBOSITY

    @staticmethod
    def __str_is_float(string):
        return string.replace('.', '').replace(
            'e-', '').replace('e+', '').isdigit()

    @staticmethod
    def __boolable(argument):
        out = isinstance(argument, (int, bool))
        if isinstance(argument, str):
            out |= argument in ('true', 'True', 'false', 'False')
            out |= argument.isdigit()
        return out

    @staticmethod
    def __intable(argument):
        out = isinstance(argument, (int, bool, float))
        if isinstance(argument, str):
            out |= argument.isdigit()
        return out

    def validate_structure_label(self, label):
        out = {'valid': True, 'message': ''}
        try:
            if label is None:
                out['message'] += 'no label provided\n'
            elif isinstance(label, float):
                label = int(label)
            elif isinstance(label, str):
                if not label.isdigit:
                    out['message'] += 'label is not integer\n'
                else:
                    label = int(label)

            if not label in self.case.structures:
                out['message'] += 'label does not match a structure in case\n'

            # no message -> valid
            if out['message'] == '': return int(label)
            else: return out

        except:
            out['valid'] = False
            out['message'] += 'exception occurred while parsing inputs\n'   
            return out

    def validate_constraintID(self, cid):
        return cid in self.case.active_constraint_IDs

    def validate_dvh_constraint(self, dose, percentile, fraction, direction):
        out = {'valid': True, 'message': ''}
        directions = ['<', '<=', '>', '>=']
        try:
            if dose is None and percentile is None and fraction is None and direction is None:
                out['message'] += 'No changes specified'


            if dose is not None:
                if isinstance(dose, (int, float)):
                    dose = float(dose)
                elif self.__str_is_float(dose):
                    dose = float(dose)
                else:
                    dose = None
                    out['message'] += 'argument "dose" must be a float or None/null\n'                
                if dose is not None:
                    if dose < 0:
                        out['message'] += 'argument "dose" must be in range [0, +inf)\n'                


            if percentile is not None:
                if isinstance(percentile, (int, float)):
                    fraction = percentile / 100.
                elif self.__str_is_float(percentile):
                    percentile = float(percentile)
                    fraction = percentile / 100.
                else:
                    fraction = None
                    out['message'] += 'argument "percentile" must be a float or None/null\n'                
                if percentile is not None:
                    if percentile < 0 or percentile > 100:
                        out['message'] += 'argument "percentile" must be in range [0, 100]\n'                


            elif fraction is not None:
                if isinstance(fraction, (int, float)):
                    fraction = float(fraction)
                elif self.__str_is_float(fraction):
                    fraction = float(fraction)
                else:
                    fraction = None
                    out['message'] += 'argument "fraction" must be a float or None/null\n'                
                if fraction is not None:
                    if fraction < 0 or fraction > 1:
                        out['message'] += 'argument "fraction" must be in range [0, 1]\n'                

            if direction is not None:
                if direction not in directions:
                    out['message'] += 'argument "direction must be one of {} or None/null\n'.format(directions)
                else:
                    direction = direction.replace('=', '')

            out['valid'] = out['message'] == ''
            if out['valid']:
                out['dose'] = dose 
                out['fraction'] = fraction
                out['direction'] = direction
            return out

        except:
            out['valid'] = False
            out['message'] += 'exception occurred while parsing inputs\n'   
            return out


    def validate_objective(self, label, dose, w_under, w_over):
        out = {'valid': True, 'message': ''}
        try:
            if not label in self.case.structures:
                out['message'] += 'label does not match a structure in case\n'

            if dose is None and w_under is None and w_over is None:
                out['message'] += 'No changes specified\n'
            elif not self.case.structures[label].is_target and w_over is None:
                out['message'] += str('No changes specified: label corresponds'
                    ' to non-target structure, argument "w_over" is None')

            if dose is not None:
                if isinstance(dose, (int, float)):
                    dose = float(dose)
                elif self.__str_is_float(dose):
                    dose = float(dose)
                else:
                    dose = None
                    out['message'] += 'argument "dose" must be a float or None/null\n'                
                if dose is not None:
                    if dose < 0:
                        out['message'] += 'argument "dose" must be in range [0, +inf)\n'                


            if w_under is not None:
                if isinstance(w_under, (int, float)):
                    w_under = float(w_under)
                elif self.__str_is_float(w_under):
                    w_under = float(w_under)
                else:
                    w_under = None
                    out['message'] += 'argument "w_under" must be a float or None/null\n'                
                if w_under is not None:
                    if w_under < 0:
                        out['message'] += 'argument "w_under" must be in range [0, +inf)\n'                



            if w_over is not None:
                if isinstance(w_over, (int, float)):
                    w_over = float(w_over)
                elif self.__str_is_float(w_over):
                    w_over = float(w_over)
                else:
                    w_over = None
                    out['message'] += 'argument "w_over" must be a float or None/null\n'                
                if w_over is not None:
                    if w_over < 0:
                        out['message'] += 'argument "w_over" must be in range [0, +inf)\n'                



            out['valid'] = out['message'] == ''
            if out['valid']:
                out['dose'] = dose 
                out['w_under'] = w_under
                out['w_over'] = w_over
            return out

        except:
            out['valid'] = False
            out['message'] += 'exception occurred while parsing inputs\n'   
            return out

    def validate_solve(self, use_2pass, use_slack, solver, verbose):
        out = {'valid': True, 'message': ''}
        try: 
            if not self.__boolable(use_2pass):
                out['message'] += 'argument "use_2pass" must be convertable to bool\n'
            else:
                use_2pass = bool(use_2pass)

            if not self.__boolable(use_slack):
                out['message'] += 'argument "use_slack" must be convertable to bool\n'
            else:
                use_slack = bool(use_slack)

            if not solver in self.SOLVER_OPTIONS:
                out['message'] += 'argument "solver" must be one of: {}\n'.format(SOLVER_OPTIONS)

            if verbose in ('true', 'True'): verbose = 1
            elif verbose in ('false', 'False'): verbose = 0
            if not self.__intable(verbose):
                out['message'] += 'argument "verbose" must be convertable to int\n'
            verbose = min(int(float(verbose)), self.MAX_VERBOSITY)


            out['valid'] = out['message'] == ''
            if out['valid']:
                out['use_2pass'] = use_2pass 
                out['use_slack'] = use_slack
                out['solver'] = solver 
                out['verbose'] = verbose
            return out

        except: 
            out['valid'] = False
            out['message'] += 'exception occurred while parsing inputs\n'  
            return out


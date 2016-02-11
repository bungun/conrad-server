import sys
from os import path

# TODO: eventually replace conrad submodule with installed conrad?
sys.path.append(path.join(path.abspath(path.dirname(__file__)),'conrad'))

from flask import Flask
from flask import render_template, jsonify, request, session, redirect, url_for
from conrad import *
import numpy as np
from time import time
from uuid import uuid4
from threading import Lock
import subprocess
from validation import InputValidator

#configuration
DEBUG = True
SESSION_TIMEOUT = 500
SECRET_KEY = 'conrad_dev_key'
USERNAME = 'admin'
PASSWORD = 'default'

#constants
FIRSTCOLOR = '#ef4904'
LASTCOLOR = '#0222ff'


app = Flask(__name__)
app.secret_key = SECRET_KEY
# app.config.from_object(__name__)
# app.config.from_envvar('CONRAD_SERVER_SETTINGS', silent=True)
# (can specify an environment variable that names a config file)


# construct dummy case. TODO: load case
def build_test_case():
    m_targ = 100
    m_oar = 400
    m = m_targ + m_oar
    n = 200

    # Structure labels
    lab_tum = 0
    lab_oar = 1

    # Voxel labels on beam matrix
    label_order = [lab_tum, lab_oar]
    voxel_labels = [lab_tum] * m_targ + [lab_oar] * m_oar


    # Prescription for each structure
    rx = [{'label': lab_tum, 'name': 'tumor', 'is_target': True,  'dose': 1., 'constraints': ['D95 > 0.9Gy']},
          {'label': lab_oar, 'name': 'oar',   'is_target': False, 'dose': 0., 'constraints': ['D50 < 0.4Gy']}]


    # dose matrix
    A_targ = np.random.rand(m_targ, n)
    A_oar = 0.5 * np.random.rand(m_oar, n)
    A = np.vstack((A_targ, A_oar))

    # Construct unconstrained case
    cs = Case(A, voxel_labels, label_order, rx)

    return cs


class User(object):
    def __init__(self, name = None):
        name = name
        loggedin = False
        sessioned = False
        sid = None


class PlanningSession(object):
    def __init__(self,sid=None,uid=None,pid_C=None,pid_JL=None):
        self.sid = sid
        self.uid = uid
        self.last_update = time()
        self.case_name = None
        self.case = None
        self.validator = None

    def set_case(self, case_name, case):
        self.case_name = case_name
        self.case = case
        self.validator = InputValidator(case)

user_names = []
users = {}
passwords = {}

def __add_user(name, password):
    global user_names, users, passwords
    if name in user_names: return False

    user_names.append(name)
    users[name] = User(name)
    passwords[name] = password 
    return True   

__add_user('admin', 'default')



login_sessions = {}
login_sessions_lock = Lock()

#TODO: case checkout?
#TODO: Set up database to store problem info
#TODO: Get (from database) list of cases on startup.
case_names = [];
cases = {}


def __init_planning_session(uid):
    sid = str(time()) + '-' + str(uuid4())
    session['sid']= sid
    login_sessions[sid] = PlanningSession(sid = sid, uid = uid)
    s = login_sessions[sid]
    users[uid].sid = sid
    users[uid].sessioned = True
    s.uid = uid
    s.last_updaate = time()


def __clean_sessions():
    global login_sessions, login_sessions_lock
    bad_sessions = []
    login_sessions_lock.acquire()
    clean_time = time()
    for sid in login_sessions:
        if login_sessions[sid].last_update + SESSION_TIMEOUT < clean_time:
            print 'Kill session', sid
            # TODO: shutdown Case/Solver/etc
            for uid in users:
                if users[uid].sid == sid:
                    users[uid].sid = None
                    users[uid].sessioned = False
            bad_sessions.append(sid)

    for sid in bad_sessions:
        del login_sessions[sid]

    login_sessions_lock.release()

def __verify_session(session):
    global login_sessions, login_sessions_lock, permissions
    login_sessions_lock.acquire()
    if not 'sid' in session: 
        login_sessions_lock.release()
        print 'No sid in session', session
        return False
    if not str(session['sid']) in login_sessions: 
        login_sessions_lock.release()
        print str(session['sid']), 'not in login sessions'
        return False
    session_d = login_sessions[str(session['sid'])]
    session_d.last_update = time()
    login_sessions_lock.release()
    __clean_sessions()
    return True

@app.route('/create_account/')
def create_account():
    success = False
    message = ''
    json_dict = request.get_json()
    uid = json_dict.pop('username', '')
    pw = json_dict.pop('password', '')
    pw2 = json_dict.pop('password2', '')
    if pw1 != pw2:
        message = 'passwords must match'
        success = False
    else:
        success = __add_user(uid, pw)
        message = 'account added' if success else 'username exists'
    return jsonify(success = success, message = message)


@app.route('/login/', methods = ['GET', 'POST'])
def login():
    global users, passwords
    success = False
    json_dict = request.get_json()
    if json_dict is None:
        json_dict = {}
        json_dict['username'] = request.args.get('username', '', type = str)
        json_dict['password'] = request.args.get('password', '', type = str)

    uid = json_dict.pop('username', '')
    if uid not in users:
        message = 'Invalid username'
    elif json_dict.pop('password', '') != passwords[uid]:
        message = 'Invalid password'
    else:
        session['logged_in'] = True
        __init_planning_session(uid)
        message = 'You were logged in'
        success = True
    return jsonify(success = success, message = message)

@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    return jsonify(success = True, message = 'You were logged out')


@app.route('/_load_color_bounds/')
def load_color_bounds():
    return jsonify(color1 = FIRSTCOLOR, color2 = LASTCOLOR)


@app.route('/_check_session/')
def check_session():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')
    else:
        return jsonify(success = True, message = 'sessioned')


@app.route('/_make_test_case/')
def make_test_case():
    global case_names
    global cases

    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')
    
    if not 'TEST CASE' in case_names:
        case_names.append('TEST CASE')
        cases['TEST CASE'] = build_test_case()

    return jsonify(success = True)


# API
# ----  
# get cases
# set case
# get structure labels
# get structure names
# get DVH - by structure
# get DVH constraints - by structure
# get plotting data - by structure
# get all plotting data (all structures)
# add DVH constraint - return success, ID
# set DVH constraint - by ID
# remove DVH constraint - by ID, return success
# add DVH constraint - by structure label, return success, ID
# add all clinical DVH constraints - return success, constraint IDs, constraints?
# reset to clinical constraints - return success, constraint IDs, constraints?
# run optimization - return success, solver status, info (iters, timing)
# get plan statistics - return dictionary{structure label, stats}
# get prescription sat - return dictionary{structure label, (constraint, status, margin) tuple}
#




@app.route('/hello/')
def hello(name = None):
    return render_template('hello.html', name = name)

# TODO - provide api upon request
@app.route('/api/')
def send_api():
    api = {'getCases': '_cases/', 'setCase': '_select_case/',
        'getStructureLabels': '_structure_labels/',
        'getStructureInfo': '_structure_info/',
        'plottingData': '_plotting_data/',
        'constraintData': '_constraint_data/',
        'addConstraint': '_add_dvh_constraint/',
        'changeConstraint': '_change_dvh_constraint/',
        'dropConstraint': '_drop_dvh_constraint/',
        'changeObjective': '_change_objective/',
        'getObjectives': '_objectives/',
        'getSingleObjective': '_single_objective/',
        'run': '_run_optimization'}
    return jsonify(api)

# get cases
@app.route('/_cases/')
def send_cases():
    return jsonify(cases = case_names)
    pass

# set case
@app.route('/_select_case/')
def select_case():
    global cases
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    s = login_sessions[session['sid']]
    json_dict = request.get_json()
    if json_dict is None:
        json_dict = {}
        json_dict['case'] = request.args.get('case', '', type = str)

    casename = json_dict.pop('case', 'NOCASE')
    if not casename in cases:
        return jsonify(success = False, message = 'case does not exist')
    else:
        s.set_case(casename, cases[casename])

    return jsonify(success = True)

# get structure labels
@app.route('/_structure_labels/')
def send_structure_labels():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    return jsonify(success = True, labels = cs.structures.keys())

# get structure names, TODO: colors by label?
@app.route('/_structure_info/')
def send_structure_info():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    structures = {}
    for label, s in cs.structures.iteritems():
        structures[label] = {'name': s.name, 'is_target': s.is_target}
    return jsonify(success = True, structures = structures)

# get all plotting data (all structures)
@app.route('/_plotting_data/')
def send_plotting_data():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    return jsonify(success = True, 
        plottingData = cs.plotting_data_json_serializable)


# get constraint plotting data (all structures)
@app.route('/_constraint_data/')
def send_constraint_data():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    return jsonify(success = True, 
        constraintData = cs.plotting_data_constraints_only)

# add DVH constraint - return ID
@app.route('/_add_dvh_constraint/')
def add_dvh_constraint():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    val = login_sessions[session['sid']].validator
    json_dict = request.get_json()

    label = json_dict.pop('structureLabel', None)
    dose = json_dict.pop('dose', None)
    percentile = json_dict.pop('percentile', None)
    fraction = json_dict.pop('fraction', None)
    direction = json_dict.pop('direction', None)

    label = val.validate_structure_label(label)
    if isinstance(label, dict):
        return jsonify(success = False, message = label['message'])

    valinfo = val.validate_dvh_constraint(dose, percentile, fraction, direction)
    if not valinfo['valid']:
        return jsonify(success = False, message = valinfo['message'])
    else:
        cid = cs.add_dvh_constraint(label, valinfo['dose'], 
            valinfo['fraction'], valinfo['direction'])
        return jsonify(success = True, constraintID = cid)

# set DVH constraint - by ID
@app.route('/_change_dvh_constraint/')
def change_dvh_constraint():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    val = login_sessions[session['sid']].validator
    json_dict = request.get_json()
    if json_dict is None:
        json_dict = {}
        json_dict['constraintID'] = request.args.get('constraintID', '', type = str)
        json_dict['dose'] = request.args.get('dose')
        json_dict['percentile'] = request.args.get('percentile')
        json_dict['fraction'] = request.args.get('fraction')
        json_dict['direction'] = request.args.get('direction')


    cid = json_dict.pop('constraintID', None)
    dose = json_dict.pop('dose', None)
    percentile = json_dict.pop('percentile', None)
    fraction = json_dict.pop('fraction', None)
    direction = json_dict.pop('direction', None)
    print direction
    print percentile
    if not val.validate_constraintID(cid):
        return jsonify(success = False, message = "invalid constraintID")

    valinfo = val.validate_dvh_constraint(dose, percentile, fraction, direction)

    print valinfo
    if not valinfo['valid']:
        return jsonify(success = False, message = valinfo['message'])
    else:
        cs.change_dvh_constraint(cid, valinfo['dose'], 
            valinfo['fraction'], valinfo['direction'])
        return jsonify(success = True)


# remove DVH constraint - by ID, return success
@app.route('/_drop_dvh_constraint/')
def drop_dvh_constraint():

    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    val = login_sessions[session['sid']].validator
    json_dict = request.get_json()
    cid = json_dict.pop('constraintID', None)
    if not val.validate_constraintID(cid):
        return jsonify(success = False, message = "invalid constraintID")
    else:
        cs.drop_dvh_constraint(cid)
        return jsonify(success = True)

@app.route('/_drop_all_dvh_constraints/')
def dropall_dvh_constraint():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')
    cs = login_sessions[session['sid']].case
    cs.drop_all_dvh_constraints()
    return jsonify(success = True)

@app.route('/_reset_constraints_to_rx/')
def drop_all_but_rx_constraints():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    cs.drop_all_but_rx_constraints()
    return jsonify(success = True)

@app.route('/_add_all_constraints_from_rx/')
def add_all_rx_constraints():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    cid_list = cs.add_all_rx_constraints()
    return jsonify(success = True, constraintIDList = cid_list)


@app.route('/_change_objective/')
def change_objective():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    val = login_sessions[session['sid']].validator
    json_dict = request.get_json()
    if json_dict is None:
        json_dict = {}
        json_dict['structureLabel'] = request.args.get('structureLabel', '', type = str)
        json_dict['dose'] = request.args.get('dose')
        json_dict['w_under'] = request.args.get('w_under')
        json_dict['w_over'] = request.args.get('w_over')



    label = json_dict.pop('structureLabel', None)
    label = val.validate_structure_label(label)

    if isinstance(label, dict):
        return jsonify(success = False, message = label['message'])

    dose = json_dict.pop('dose', None)
    w_under = json_dict.pop('w_under', None)
    w_over = json_dict.pop('w_over', None)

    print "dose", dose, type(dose)
    print "wover", w_over, type(w_over)
    print "wunder", w_under, type(w_under)

    valinfo = val.validate_objective(label, dose, w_under, w_over)

    print valinfo

    if not valinfo['valid']:
        return jsonify(success = False, message = valinfo['message'])
    else:
        cs.change_objective(label, valinfo['dose'], 
            valinfo['w_under'], valinfo['w_over'])
        return jsonify(success = True)

@app.route('/_objectives/')
def send_objectives():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case    
    return jsonify(success = True, objectives = cs.objective_data)

@app.route('/_single_objective/')
def send_single_objective():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case    
    val = login_sessions[session['sid']].validator
    json_dict = request.get_json()
    if json_dict is None:
        json_dict = {}
        json_dict['structureLabel'] = request.args.get('structureLabel', '', type = str)


    label = json_dict.pop('structureLabel', None)
    label = val.validate_structure_label(label)

    if isinstance(label, dict):
        return jsonify(success = False, message = label['message'])

    return jsonify(success = True, 
        objectives = cs.get_objective_by_label(label))


@app.route('/_run_optimization/')
def run_optimization():
    if not __verify_session(session): 
        return jsonify(success = False, message = 'unsessioned')

    cs = login_sessions[session['sid']].case
    val = login_sessions[session['sid']].validator
    json_dict = request.get_json()
    if json_dict is None:
        json_dict = {}
        json_dict['use_2pass'] = request.args.get('use_2pass', False, type = bool)
        json_dict['use_slack'] = request.args.get('use_2pass', True, type = bool)
        json_dict['solver'] = request.args.get('solver', 'ECOS', type = str)
        json_dict['verbose'] = request.args.get('verbose', 1, type = int)

    use_2pass = json_dict.pop('use_2pass', False)
    use_slack = json_dict.pop('use_slack', True)
    solver = json_dict.pop('solver', 'ECOS')
    verbose = json_dict.pop('verbose', 1)

    valinfo = val.validate_solve(use_2pass, use_slack, solver, verbose)
    if not valinfo['valid']:
        return jsonify(success = False, message = valinfo['message'])
    else:
        cs.plan(solver, verbose = valinfo['verbose'])
        info = cs.solver_info

        return jsonify(success = True, status = info['status'], 
            objective = info['objective'], 
            time = info['time'], iterations = info['iters'], 
            feasible = cs.feasible)

@app.route('/_plan_statistics')
def get_plan_statistics():
    pass

@app.route('/_rx_satisfaction_report')
def get_rx_satisfaction_report():
    pass



if __name__ == '__main__':
    app.run(debug=DEBUG)

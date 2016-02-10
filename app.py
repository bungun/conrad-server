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


DEBUG = True
SESSION_TIMEOUT = 500
SECRET_KEY = 'conrad_dev_key'
FIRSTCOLOR = '#ef4904'
LASTCOLOR = '#0222ff'


class User(object):
    def __init__self():
        name = None
        loggedin = False
        sessioned = False
        sid = None


class PlanningSession(object):
    def __init__(self,sid=None,uid=None,pid_C=None,pid_JL=None):
        self.sid = sid
        self.uid = uid
        self.last_update = time()
        self.plan = None
        self.runKeys = []
        self.runs = {}
        self.case = None
        self.nStructures = 0
        self.all_structure_names = None
        self.all_structure_indices = None
        self.nActive = 0
        self.nTarget = 0
        self.active_structure_names = None
        self.active_structure_indices = None
        self.colors = None


app = Flask(__name__)
app.secret_key = SECRET_KEY

uid = 'User'
user_names = []
users = {}

user_names.append(uid)
users[uid]=User()

login_sessions = {}
login_sessions_lock = Lock()

#TODO: Set up database to store problem info

#TODO: Get (from database) list of cases on startup. Or hardcode
case_names = [];
cases = {}

# case_names.append('Case 1: Head and Neck')
# cases[case_names[0]] = PlanningCase(name=case_names[0])
# cases[case_names[0]].m = 268228
# cases[case_names[0]].n = 360
# cases[case_names[0]].path['A'] = '/home/baris/radonc/dosing/demo/folkerts/A.txt'
# cases[case_names[0]].path['B'] = '/home/baris/radonc/dosing/demo/folkerts/B.txt'
# # cases[case_names[0]].path['l'] = '/home/baris/radonc/dosing/demo/folkerts/structure_info.txt'
# cases[case_names[0]].path['s'] = '/home/baris/radonc/dosing/demo/folkerts/voxel_labels.txt'
# cases[case_names[0]].path['l'] = '/Users/Baris/Documents/Thesis/data/optimization/dosing/demo/folkerts/structure_info.txt'
# case_names.append('Case 2: Prostate')
# case_names.append('Case 3: Pancreas')
# case_names.append('Case 4: Lung')

def clean_sessions():
    global login_sessions, login_sessions_lock
    bad_sessions = []
    login_sessions_lock.acquire()
    clean_time = time()
    for sid in login_sessions:
        if login_sessions[sid].last_update + SESSION_TIMEOUT < clean_time:
            print "Kill session", sid
            login_sessions[sid].pogsIO.send_shutdown_signal()
            for uid in users:
                if users[uid].sid == sid:
                    users[uid].sid = None
                    users[uid].sessioned = False
            bad_sessions.append(sid)

    for sid in bad_sessions:
        del login_sessions[sid]

    login_sessions_lock.release()


def verify_session(session):
    global login_sessions, login_sessions_lock, permissions
    login_sessions_lock.acquire()
    if not "sid" in session: 
        login_sessions_lock.release()
        print "No sid in session", session
        return False
    if not str(session["sid"]) in login_sessions: 
        login_sessions_lock.release()
        print str(session["sid"]), "not in login sessions"
        return False
    session_d = login_sessions[str(session["sid"])]
    session_d.last_update = time()
    login_sessions_lock.release()
    clean_sessions()
    return True


#TODO: Data validation
#TODO: Authentication


# @app.route('/_load_cases/')
# def load_cases():
#     return jsonify(cases=case_names)


# @app.route('/_init_planning_session/')
# def init_planning_session():

#     sid = str(time()) + '-' + str(uuid4())
#     session['sid']= sid
#     login_sessions[sid] = PlanningSession(sid=sid)
#     s = login_sessions[sid]
#     s.case = cases[request.args.get('case_name')]


#     #start julia and C++ subprocesses
#     s.pogsIO.start_julia(s.case)
#     s.pogsIO.start_c(s.case)

#     s.nStructures, s.all_structure_names, s.all_structure_indices = s.caseIO.load_structures(s.case.path['l'])

#     #TODO get current uid
#     users[uid].sid = sid
#     users[uid].sessioned = True
#     s.uid = uid

#     return jsonify(success=True,next_page=url_for('case_setup_1'))


# @app.route('/_load_all_structures/')
# def load_all_structures():
#     #TODO get current uid, check auth, check sessioned, check session alive
#     if not verify_session(session) : return jsonify(success=False, message='Cannot load all structures without active session')

#     s = login_sessions[session["sid"]]

#     return jsonify(nStructures = s.nStructures, names = s.all_structure_names)


@app.route('/_load_color_bounds/')
def load_color_bounds():
    return jsonify(color1 = FIRSTCOLOR, color2 = LASTCOLOR)

# @app.route('/_select_structures/')
# def select_structures():
#     #TODO get current uid, check auth, check sessioned, check session alive    
#     if not verify_session(session) : return jsonify(success=False, message='Cannot send active structures without active session')

#     s = login_sessions[session["sid"]]

#     success = False

#     s.nActive = request.args.get('n_active_structures',type=int)
#     s.plan = TreatmentPlan(nStructures=s.nActive,m=s.case.m,n=s.case.n)

#     s.plan.objectives[-1]=Objective(structureIndex=-1,structureName='All Other')

#     s.active_structure_names = [];
#     s.active_structure_indices = [];
#     s.colors = [];

#     for st in xrange(s.nActive):
#         idx = request.args.get('ranked_structures['+str(st)+']',type=int)
#         print(idx)


#         s.active_structure_names.append(s.all_structure_names[idx])
#         s.active_structure_indices.append(s.all_structure_indices[idx])
    
#         s.plan.objectives[s.all_structure_indices[idx]]=Objective(structureIndex=s.all_structure_indices[idx],structureName=s.all_structure_names[idx])

#     s.active_structure_names.append('All Other')
#     s.active_structure_indices.append(-1)

#     for st in xrange(s.plan.nStructures):
#         s.colors.append (request.args.get('colors['+str(st)+']',type=str))


#     #TODO: make voxel label vector
    
#     return jsonify(success=True,next_page=url_for('case_setup_2'))



# @app.route('/case_setup_2/')
# def case_setup_2():
#     if not verify_session(session) : return redirect(url_for('case_selection'))

#     return render_template('target_specification.html')


# @app.route('/post/<int:post_id>')
# def show_post(post_id):
#     # show the post with the given id, the id is an integer
#     return 'Post %d' % post_id


@app.route('/hello/')
def hello(name=None):
    return render_template('hello.html', name=name)



# @app.route('/_load_plan_basics/')
# def load_plan_basics():
#     # #TODO get current uid, check auth, check sessioned, check session alive    
#     if not verify_session(session) : return jsonify(success=False, message='Cannot load plan basics without active session')

#     s = login_sessions[session["sid"]]

#     nStructures = s.plan.nStructures
#     nTargets = s.plan.nTargets
#     structureNames = s.active_structure_names
#     rxs = []
#     targetIndicators = []
#     for key in s.active_structure_indices:
#       rxs.append(s.plan.objectives[key].rx)
#       targetIndicators.append(s.plan.objectives[key].isTarget)
#     colors = s.colors

#     # print(nStructures)
#     # print(nTargets)
#     # print(structureNames)
#     # print(rxs)
#     # print(colors)
#     # print(targetIndicators)

#     return jsonify(success=True,nStructures=nStructures,nTargets=nTargets,targetIndicators = targetIndicators, rxArray=rxs, structureNames=structureNames, colors=colors)


# /@app.route('/_load_dvh/')
# def load_dvh():
#     # #TODO get current uid, check auth, check sessioned, check session alive    
#     if not verify_session(session) : return jsonify(success=False)

#     s = login_sessions[session["sid"]]

#     idx = request.args.get('index', 0, type=int)


#     if s.y is None:
#         if (ON_GPU):
#             pass
#             # if s.A is None:
#                 # s.A = np.loadtxt('/Users/Baris/Documents/Thesis/data/optimization/dosing/demo/folkerts/A.txt')                
#             # if s.x is None:
#                 # s.x = np.loadtxt('/Users/Baris/Documents/Thesis/data/optimization/dosing/demo/folkerts/x.txt')
#             # s.y = np.dot(s.A,s.x)
#         else:
#             s.y = np.loadtxt('/Users/Baris/Documents/Thesis/data/optimization/dosing/demo/folkerts/y.txt')
#     if s.voxel_labels is None:
#         s.voxel_labels = np.loadtxt('/Users/Baris/Documents/Thesis/data/optimization/dosing/demo/folkerts/voxel_labels_full.txt',dtype=int)

#     dvh = s.plan.get_dvh(s.active_structure_indices[idx],s.y,s.voxel_labels)
#     # print(dvh)

#     return jsonify(success=True,result=dvh.tolist(),color=s.colors[idx],structureName=s.active_structure_names[idx])

# @app.route('/_send_objectives/')
# def run_opt():
#     # #TODO get current uid, check auth, check sessioned, check session alive    
#     if not verify_session(session) : return jsonify(success=False, message='Cannot send objectives without active session')

#     s = login_sessions[session["sid"]]


#     success = False
#     s.plan.tsratio = request.args.get('tsRatio',1.,type=float)
#     st=-1
#     # print(tsratio)
#     for o_key in s.plan.objectives:
#             st+=1
#             isTarget = request.args.get('objectives[obj'+str(st)+'][isTarget]') == 'true'
#             s.plan.objectives[o_key].isTarget=isTarget
#             s.plan.objectives[o_key].weight = request.args.get('objectives[obj'+str(st)+'][weight]',-1.,type=float)
#             if (isTarget):
#                 s.plan.objectives[o_key].rx = request.args.get('objectives[obj'+str(st)+'][rx]',-1.,type=float)
#                 s.plan.objectives[o_key].boost = request.args.get('objectives[obj'+str(st)+'][boost]',-1.,type=float)
#                 s.plan.objectives[o_key].alpha = request.args.get('objectives[obj'+str(st)+'][alpha]',-1.,type=float)
#                 s.plan.objectives[o_key].weight*= tsratio           

#     print(s.pogsIO.gen_pogs_msg(s.plan.objectives))

#     # TODO: Pass objectives to function. Check if already used. Get nearest plan in 2(?)-norm, warm-start from there

#     return jsonify(success=True, message="Message")

# @app.route('/_run_optimization/')
# def opt_results():
#     # #TODO get current uid, check auth, check sessioned, check session alive    
#     if not verify_session(session) : return jsonify(success=False, message='Cannot run optimization without active session')

#     s = login_sessions[session["sid"]]



#     return jsonify(success=True, message="Message")




if __name__ == '__main__':
    app.run(debug=DEBUG)

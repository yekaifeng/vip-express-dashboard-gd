# -*- encoding: utf-8 -*-
"""
Python Aplication Template
Licence: GPLv3
"""

from flask import url_for, redirect, render_template, send_file, flash, g, session
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, lm, socketio, q
from forms import ExampleForm, LoginForm
from models import User
from flask_socketio import send, emit
import threading
import time, json
from threading import Lock
from coordTransform import wgs84_to_gcj02

t = None
channel = None
connection = None
message = None
thread = None
thread_lock = Lock()

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/drone/')
def drone():
	return render_template('drone.html')

@app.route('/drone_icon/')
def drone_icon():
	return send_file('templates/drone-icon1.png', mimetype='image/gif')

@app.route('/list/')
def posts():
	return render_template('list.html')

@app.route('/new/')
@login_required
def new():
	form = ExampleForm()
	return render_template('new.html', form=form)

@app.route('/save/', methods = ['GET','POST'])
@login_required
def save():
	form = ExampleForm()
	if form.validate_on_submit():
		print "salvando os dados:"
		print form.title.data
		print form.content.data
		print form.date.data
		flash('Dados salvos!')
	return render_template('new.html', form=form)

@app.route('/view/<id>/')
def view(id):
	return render_template('view.html')

# === User login methods ===

@app.before_request
def before_request():
    g.user = current_user

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login/', methods = ['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        login_user(g.user)

    return render_template('login.html', 
        title = 'Sign In',
        form = form)

@app.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('index'))

@socketio.on('connect', namespace='/demo')
def ws_conn():
    socketio.emit('msg', {'count': 11111}, namespace='/demo')

@socketio.on('disconnect', namespace='/demo')
def ws_disconn():
    global connection, channel
    if connection is not None:
        channel.close()
        connection.close()
    socketio.emit('msg', {'count': 345}, namespace='/demo')

@socketio.on('connect_event', namespace='/demo')
def connected_msg(msg):
    print "connected msg"
    global thread
    with thread_lock:
        if thread is None:
            thread = threading.Thread(target=update_data).start()
            #thread = socketio.start_background_task(target=update_gps)

#    jsonstr = '{"basic_data":{"flight_status":0,"position_altitude":120.42618560791016,"position_latitude":22.993399,"position_longitude":113.165085,"quaternion_w":0.99570769071578979,"quaternion_x":-0.014414009638130665,"quaternion_y":0.030574096366763115,"quaternion_z":-0.086161427199840546,"rc_pitch":29,"rc_roll":14,"rc_throttle":1982,"rc_yaw":43,"velocity_vx":0.0032146789599210024,"velocity_vy":0.0081168506294488907,"velocity_vz":-0.00059953308664262295},"timestamp":"2018-02-22 14:26:53"}'
#    gps = json.loads(jsonstr)
#    emit('server_response', {'data': gps})
#    time.sleep(2)
#    gps['basic_data']['position_latitude'] += 0.0005
#    emit('server_response', {'data': gps})
#    time.sleep(2)
#    gps['basic_data']['position_longitude'] += 0.0005
#    emit('server_response', {'data': gps})
#    time.sleep(2)
#    gps['basic_data']['position_longitude'] += 0.0005
#    emit('server_response', {'data': gps})


def sendingmsg():
    for i in range(1,10):
        socketio.emit('msg', {'count': i}, namespace='/demo')
        time.sleep(1)


def update_data():
    while True:
        time.sleep(0.1)
        if not q.empty():
            for i in range(q.qsize()):
                msg = q.get()
                data = json.loads(msg)
                print "RX DATA: %s" % data
                #convert from wgs84 to gcj02
                lng = data['basic_data']['position_longitude']
                lat = data['basic_data']['position_latitude']
                wgs84_gps = wgs84_to_gcj02(lng, lat)
                data['basic_data']['position_longitude'] = wgs84_gps[0]
                data['basic_data']['position_latitude'] = wgs84_gps[1]
                socketio.emit('server_response', {'data': data},namespace='/demo')
# ====================

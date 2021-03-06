from flask import render_template, redirect
from app import app
from forms import SubmitForm

import json
import socket

@app.route('/', methods=['GET','POST'])
@app.route('/index', methods=['GET','POST'])
def index():
    form = SubmitForm()

    # if form was submitted, do the following
    if form.validate_on_submit():
        data = {}
        data["callsign"] = form.callsign.data
        data["weight"] = form.weight.data
        data["parachute"] = form.parachute.data
        data["balloon"] = form.balloon.data
        data["helium"] = form.helium.data

        host = "127.0.0.1"
        port = 50001
        
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((host,port))
        sock.send(json.dumps(['start_real_time', data]))
        msg = sock.recv(1028)
        print(msg)
        sock.close()

        return redirect('http://127.0.0.1:5000/map/{0}.html'.format(data["callsign"]))

    return render_template('submit.html',
                           title='Home',
                           form=form)

@app.route('/map/<path>')
def map(path):
    return render_template(path)

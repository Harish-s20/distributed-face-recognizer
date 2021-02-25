import os
import uuid
import smtplib
import json

from dataclasses import dataclass
from datetime import datetime

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   send_from_directory)
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.curdir, 'uploads')
app.config['SECRET_KEY'] = "WGRwwA>L<](]c&z^umkHhC78?^(/ws'7"
app.config['DEBUG'] = 1

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///face_recognizer.db'

CONFIG_FILE = 'settings.conf'

db = SQLAlchemy(app)
sio = SocketIO(app)


def mail_serv(message, location):

    config_file = open(CONFIG_FILE, 'r')
    config = json.loads(config_file.read())
    config_file.close()
    mail_id = config['EMAIL_ID']
    password = config['PASSWORD']
    receiver = config['RECEIVER']
    # location = config['LOCATION']

    s = smtplib.SMTP('smtp.gmail.com', 587)

    s.starttls()
    s.login(mail_id, password)
    message += f'\n\nLocation: {location}'
    try:
        s.sendmail(mail_id, receiver, message)
    except Exception:
        pass

    s.quit()


@dataclass
class Person(db.Model):
    id: int
    name: str
    file: str
    disc: str
    date: str

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    file = db.Column(db.String(100))
    disc = db.Column(db.String(500))
    date = db.Column(db.DateTime)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cam_no = db.Column(db.Integer, primary_key=True)
    place = db.Column(db.String(1000))


class FaceRecognizerIndex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    person_id = db.Column(db.Integer, db.ForeignKey(
        'person.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey(
        'location.id'), nullable=False)


class OnlineSystems(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.String(1000))
    time = db.Column(db.DateTime)
    location_id = db.Column(db.Integer, db.ForeignKey(
        'location.id'), nullable=False)


@app.route('/')
def index():
    persons = Person.query.all()
    return render_template('index.html', photo_list=persons)


@app.route('/get_data')
def photots():
    persons = Person.query.all()
    print(persons)
    return jsonify(persons)


@app.route('/new')
def new_upload():
    return render_template('upload-form.html')


@app.route('/upload', methods=["POST"])
def upload_photo():

    if 'person' not in request.files:
        flash('No file attached')
        return redirect(request.url)

    file = request.files['person']
    name = request.form['name']
    discription = request.form['disc']
    filename = str(uuid.uuid4()) + '.' + \
        secure_filename(file.filename).split('.')[-1]
    print(discription)
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        # filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    person = Person(name=name, disc=discription,
                    file=filename, date=datetime.now())
    db.session.add(person)
    db.session.commit()
    sio.emit("new_persom", broadcast=True)
    return redirect('/')


@app.route('/view/<int:table_id>')
def view_person(table_id):
    person = Person.query.get_or_404(table_id)
    return render_template('detail-view.html', person=person)


@app.route('/uploads/<path:path>')
def get_photo(path):
    return send_from_directory('uploads', path)


@sio.event
def connect():
    print('connection established', request.sid)


@sio.event
def disconnect():
    print('disconnect ', request.sid)


@sio.event
def person_found(data):
    print(f'Message received from {request.sid} with ', data)
    # sio.emit('my response', {'response': 'my response'})
    mail_serv(data["person"], data["location"])


if __name__ == "__main__":
    sio.run(app)

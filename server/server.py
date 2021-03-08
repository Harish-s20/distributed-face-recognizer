import os
import uuid
import smtplib
import json
import functools

from dataclasses import dataclass
from datetime import datetime

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   send_from_directory, abort)
from flask_socketio import SocketIO, emit
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


@dataclass
class Location(db.Model):
    id: int
    uid: str
    cam_no: int
    place: str
    discription: str

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(128))
    cam_no = db.Column(db.Integer)
    place = db.Column(db.String(1000))
    discription = db.Column(db.String(1000))


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


def socket_auth(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        uid = ""
        if uid:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


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
    emit("new_person", broadcast=True, namespace="/")
    return redirect('/')


@app.route('/view/<int:table_id>')
def view_person(table_id):
    person = Person.query.get_or_404(table_id)
    face_index = db.session.query(FaceRecognizerIndex).filter(FaceRecognizerIndex.person_id == table_id).all()

    face_recognition_table = []

    for found in face_index:
        face_dict = {}
        location =  Location.query.get(found.location_id)
        face_dict["id"] = found.id
        face_dict["place"] = location.place
        face_dict["cam_no"] = location.cam_no
        face_dict["time"] = found.time
        face_recognition_table.append(face_dict)

    return render_template('detail-view.html', person=person, face_recognition_table=face_recognition_table)


@app.route('/update_person/<id>')
def update_person(id):
    return render_template("upload-form.html")


@app.route('/delete_person/<id>')
def delete_person(id):
    try:
        person = Person.query.get_or_404(id)
        db.session.delete(person)
        face_index = db.session.query(FaceRecognizerIndex).filter(FaceRecognizerIndex.person_id == id).all()

        for found in face_index:
            db.session.delete(found)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        print(e)
        return abort(404)


@app.route('/new_location', methods=["GET", "POST"])
def new_location():
    if(request.method == "POST"):
        data = request.form
        print(data)
        uid = str(uuid.uuid4())
        cam_no = data["cam_no"]
        place = data["place"]
        discription = data["disc"]
        location = Location(uid=uid, cam_no=cam_no, place=place, discription=discription)
        db.session.add(location)
        db.session.commit()

        return render_template('new_location.html', uid=uid)

    return render_template('new_location.html')


@app.route('/view_location')
def view_location():
    locations = Location.query.all()
    return render_template("view_location.html", location=locations)


@app.route('/view_online')
def view_online():
    online_system = OnlineSystems.query.all()
    online_dict = []
    for online in online_system:
        loc_dict = {}
        locat = Location.query.get(online.location_id)
        loc_dict["id"] = online.id
        loc_dict["place"] = locat.place
        loc_dict["cam_no"] = locat.cam_no
        loc_dict["time"] = online.time
        online_dict.append(loc_dict)

    return render_template("online_system.html", location=loc_dict)


@app.route('/update_location/<id>')
def update_location(id):
    return render_template("new_location.html")


@app.route('/delete_location/<id>')
def delete_location(id):
    try:
        location = Location.query.get_or_404(id)
        db.session.delete(location)
        db.session.commit()
        return redirect('/view_location')

    except Exception as e:

        print(e)
        return abort(404)


# @app.route("/person_found", methods=["POST"])
@sio.event
def person_found(data):
    # data = request.json
    try:
        print(f"request received with ... {data}")
        # mail_serv(data["person"], data["location"])
        location = db.session.query(Location).filter(Location.uid == data["auth_token"]).first()

        face_index = FaceRecognizerIndex(time=datetime.now(), location_id=location.id, person_id=data["id"])
        db.session.add(face_index)
        db.session.commit()
        print(location)
        print(face_index)
        print("success", 200)
    except Exception as e:
        print(e)
        print("failed", 502)


@app.route('/uploads/<path:path>')
def get_photo(path):
    return send_from_directory('uploads', path)


@sio.event
def connect():
    # print(data)
    print('connection established', request.sid)


@sio.event
def auth_event(data):
    print('auth_event', request.sid)
    location = db.session.query(Location).filter(Location.uid == data["auth_token"]).first()

    if location != None:
        online = OnlineSystems(sid=request.sid, time=datetime.now(), location_id=location.id)
        db.session.add(online)
        db.commit()
    else:
        print("invalid auth token")


@sio.event
def disconnect():
    try:
        online = db.session.query(OnlineSystems).filter(OnlineSystems.sid == request.sid).first()
        db.session.delete(online)
        db.session.commit()
        print('disconnect ', request.sid)
    except Exception as e:
        print(e)
        print("failed to delete sid - ", request.sid)


if __name__ == "__main__":
    sio.run(app)

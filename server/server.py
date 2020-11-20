import os
import uuid
from dataclasses import dataclass
from datetime import datetime

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   send_from_directory)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.curdir, 'uploads')
app.config['SECRET_KEY'] = "WGRwwA>L<](]c&z^umkHhC78?^(/ws'7"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///face_recognizer.db'

db = SQLAlchemy(app)

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

@app.route('/new')
def new_upload():

    return render_template('upload-form.html')

@app.route('/')
def index():
    persons = Person.query.all()

    return render_template('index.html', photo_list=persons)


@app.route('/get_data')
def photots():
    persons = Person.query.all()
    print(persons)
    return jsonify(persons)


@app.route('/upload', methods=["POST"])
def upload_photo():

    if 'person' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['person']
    name = request.form['name']
    discription = request.form['disc']
    filename = str(uuid.uuid4()) + '.' + secure_filename(file.filename).split('.')[-1]
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

    return redirect('/')

@app.route('/view/<int:table_id>')
def view_person(table_id):
    person = Person.query.get_or_404(table_id)
    return render_template('detail-view.html',person=person)

@app.route('/uploads/<path:path>')
def get_photo(path):

    return send_from_directory('uploads', path)


if __name__ == "__main__":
    app.run(debug=True)

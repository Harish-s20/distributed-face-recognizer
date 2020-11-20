from flask import Flask, render_template, redirect, request, jsonify, send_from_directory, flash
from werkzeug.utils import secure_filename

import os
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.curdir, 'uploads')


@app.route('/')
def index():
    photo_list = []
    for data in os.listdir('./uploads'):
        photo_list.append({"person":data})
    
    return render_template('index.html',photo_list=photo_list)


@app.route('/photots')
def photots():
    photo_list = []
    for data in os.listdir('./uploads'):
        photo_list.append(data)

    return jsonify(photo_list)


@app.route('/upload', methods=["POST"])
def upload_photo():

    if 'person' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['person']
    discription = request.form['disc']
    print(discription)
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        # filename = secure_filename(file.filename)
        filename = str(uuid.uuid4())+'.'+secure_filename(file.filename).split('.')[-1]
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return redirect('/')


@app.route('/uploads/<path:path>')
def get_photo(path):

    return send_from_directory('uploads', path)


if __name__ == "__main__":
    app.run(debug=True)

import json
import threading
import time
import smtplib

import cv2
import face_recognition
import numpy as np
import requests

SERVER_URL = 'http://127.0.0.1:5000/'
DEBUG = True
SERVER_RUNNING = False
CONFIG_FILE = 'settings.conf'

known_face_encodings = []
known_face_names = []


def mail_serv(message):

    config_file = open(CONFIG_FILE, 'r')
    config = json.loads(config_file.read())
    config_file.close()
    mail_id = config['EMAIL_ID']
    password = config['PASSWORD']
    receiver = config['RECEIVER']
    location = config['LOCATION']

    s = smtplib.SMTP('smtp.gmail.com', 587)

    s.starttls()
    s.login(mail_id, password)
    message += f'\n\nLocation: {location}'
    try:
        s.sendmail(mail_id, receiver, message)
    except Exception:
        pass

    s.quit()


def check_server():
    while True:
        if SERVER_RUNNING:
            url = SERVER_URL+'get_data'
            req = requests.get(url).text
            print('send request to the server')

            with open('data.json', 'w') as json_data:
                json_data.write(req)

            content = json.loads(req)

            for data in content:
                img_url = SERVER_URL + 'uploads/' + data['file']
                img = requests.get(img_url).content
                print(f'downloading {data["file"]}')
                with open(f"images/{data['file']}", 'wb') as img_file:
                    img_file.write(img)

        # Load a sample picture and learn how to recognize it.

        with open('data.json') as json_data:

            content = json.loads(''.join(json_data.readlines()))

            for data in content:
                person_image = face_recognition.load_image_file(
                    f"images/{data['file']}")
                person_face_encoding = face_recognition.face_encodings(person_image)[
                    0]

                known_face_encodings.append(person_face_encoding)
                known_face_names.append(data['name'])

        time.sleep(10)


def face_recognizer():

    video_capture = cv2.VideoCapture(0)

    # Initialize some variables
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding)
                name = "Unknown"

                face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    print(f"Found {name} on the frame")
                    if not DEBUG:
                        print("sending mail ...")
                        th = threading.Thread(target=mail_serv, args=[
                                              f"Found {name} on the frame"])
                        th.start()

                face_names.append(name)

        process_this_frame = not process_this_frame

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35),
                          (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        font, 1.0, (255, 255, 255), 1)

        # Display the resulting image
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    fr_thread = threading.Thread(target=face_recognizer)
    cs_thread = threading.Thread(target=check_server)

    # start the threads
    fr_thread.start()
    cs_thread.start()

    # join the threads
    fr_thread.join()
    cs_thread.join()

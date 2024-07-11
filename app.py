import typing
import uuid
import flask
import flask_socketio
import google.generativeai as genai

import firebase_admin
from firebase_admin import firestore, credentials

import secret
import socratic_model

genai.configure(api_key=secret.SECRET_KEY)
app = flask.Flask(__name__)
socketio = flask_socketio.SocketIO(app)


cred = credentials.Certificate("private_key.json")
firebase = firebase_admin.initialize_app(cred)
db = firestore.client()
seminar_collection = db.collection('seminars')

def get_seminar_contents(uid):
    seminar_dict = seminar_collection.document(uid).get()
    if not seminar_dict.exists:
        return {'content': ""}

    model = socratic_model.Seminar.from_dict(seminar_dict.to_dict())
    return {'content': flask.render_template('dialogue.html', contents=model.contents)}

@app.route("/")
def hello_world():
    return flask.render_template('index.html')

@socketio.on('new_seminar')
def handle_new_seminar(data):
    """
    Generate a new uuid and seminar for each session
    """
    uids = [seminar.id for seminar in seminar_collection.stream()]
    while (new_id := uuid.uuid4().hex) in uids:
        pass
    #seminar_dict[new_id] = socratic_model.Seminar(data['prompt'], socratic_model.GeminiActor(), socratic_model.GeminiActor())
    model = socratic_model.Seminar(data['prompt'], socratic_model.GeminiActor(), socratic_model.GeminiActor())
    seminar_collection.document(new_id).set(model.to_dict())
    flask_socketio.emit('on_connect', {'id': new_id})
    flask_socketio.emit('update_seminar', get_seminar_contents(new_id))

@socketio.on('check_seminar')
def handle_check_seminar(data):
    if data['id'] in [seminar.id for seminar in seminar_collection.stream()]:
        flask_socketio.emit('check_seminar', {'value': True})
        flask_socketio.emit('update_seminar', get_seminar_contents(data['id']))
    else:
        flask_socketio.emit('check_seminar', {'value': False})

@socketio.on('continue_seminar')
def handle_continue_seminar(data):
    """
    Handle a request to advance the state of a seminar
    """
    seminar_dict = seminar_collection.document(data['id']).get()
    if not seminar_dict.exists:
        return "Record not found", 400

    model = socratic_model.Seminar.from_dict(seminar_dict.to_dict())

    if data['prompt'] == '':
        model.next()
    else:
        model.add_statement(data['prompt'])

    seminar_collection.document(data['id']).update(model.last_content_embedded())

    flask_socketio.emit('update_seminar', get_seminar_contents(data['id']))
    
if __name__ == "__main__":
    socketio.run(app)
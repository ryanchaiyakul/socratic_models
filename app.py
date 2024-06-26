import typing
import uuid
import flask
import flask_socketio
import google.generativeai as genai

import secret
import socratic_model

genai.configure(api_key=secret.SECRET_KEY)
app = flask.Flask(__name__)
socketio = flask_socketio.SocketIO(app)

seminar_dict: typing.Dict[socratic_model.Seminar, socratic_model.Seminar] = {}

@app.route("/")
def hello_world():
    return flask.render_template('index.html')

@socketio.on('new_seminar')
def handle_new_seminar(data):
    """
    Generate a new uuid and seminar for each session
    """
    new_id = uuid.uuid4().hex
    seminar_dict[new_id] = socratic_model.Seminar(data['prompt'], socratic_model.GeminiActor(), socratic_model.GeminiActor())
    flask_socketio.emit('on_connect', {'id': new_id})

@socketio.on('continue_seminar')
def handle_message(data):
    try:
        model = seminar_dict[data['id']]
    except KeyError:
        return "Record not found", 400
    
    if data['prompt'] == '':
        model.next()
    else:
        model.add_statement(data['prompt'])

    flask_socketio.emit('update_seminar', {'content': flask.render_template('dialogue.html', contents=model.contents)})


if __name__ == "__main__":
    socketio.run(app)
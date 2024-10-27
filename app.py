import flask
import flask_socketio
import google.generativeai as genai

import secret
import socratic_model

genai.configure(api_key=secret.SECRET_KEY)
app = flask.Flask(__name__)
socketio = flask_socketio.SocketIO(app)

db = socratic_model.DB()


def get_seminar_contents(uid):
    seminar = db.get(uid)
    if seminar is None:
        return {'content': ""}

    return {'content': flask.render_template('dialogue.html', contents=seminar.contents)}


@app.route("/")
def index():
    return flask.render_template('index.html')


@app.route("/seminars")
def seminars():
    return flask.render_template('seminars.html', seminars=db.seminar_collection.stream())


@socketio.on('new_seminar')
def handle_new_seminar(data):
    # TODO: Make this not generic
    model = socratic_model.Seminar(
        data['prompt'], socratic_model.GeminiActor(), socratic_model.GeminiActor())

    new_id = db.add(model)
    flask_socketio.emit('on_connect', {'id': new_id})
    flask_socketio.emit('update_seminar', get_seminar_contents(new_id))


@socketio.on('check_seminar')
def handle_check_seminar(data):
    if db.has(data['id']):
        flask_socketio.emit('check_seminar', {'value': True})
        flask_socketio.emit('update_seminar', get_seminar_contents(data['id']))
    else:
        flask_socketio.emit('check_seminar', {'value': False})


@socketio.on('continue_seminar')
def handle_continue_seminar(data):
    """
    Handle a request to advance the state of a seminar
    """
    seminar = db.get(data['id'])
    if seminar is None:
        return "Record not found", 400

    if data['prompt'] == '':
        seminar.next()
    else:
        seminar.add_statement(data['prompt'])

    db.update(data['id'], seminar)
    flask_socketio.emit('update_seminar', get_seminar_contents(data['id']))


if __name__ == "__main__":
    socketio.run(app)

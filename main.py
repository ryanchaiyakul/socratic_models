import sys
import time
import logging

import firebase_admin
from firebase_admin import firestore, credentials

cred = credentials.Certificate("private_key.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()

import google.generativeai as genai

import secret
import socratic_model


if __name__ == "__main__":
    genai.configure(api_key=secret.SECRET_KEY)

    model_one = socratic_model.GeminiActor()
    model_two = socratic_model.GeminiActor()\
    
    topic = "Debate whether golf is a sport"
    if len(sys.argv) > 2:
         topic = sys.argv[2]

    my_seminar = socratic_model.Seminar(topic, model_one, model_two)

    for i in range(int(sys.argv[1])):
            my_seminar.talk(0)
            my_seminar.talk(1)
            # it is two requests per minute so we gotta wait .-.
            if i > 0:
                time.sleep(61)

    db.collection('seminars').document('test2').set(my_seminar.to_dict())
    print(socratic_model.Seminar.from_dict(db.collection('seminars').document('test2').get().to_dict()))

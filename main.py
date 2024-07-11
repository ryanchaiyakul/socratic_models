import sys
import time

import google.generativeai as genai

import secret
import socratic_model


if __name__ == "__main__":
    genai.configure(api_key=secret.SECRET_KEY)

    model_one = socratic_model.GeminiActor()
    model_two = socratic_model.GeminiActor()
    
    topic = "Debate whether golf is a sport"
    if len(sys.argv) > 2:
         print(sys.argv[2])
         topic = sys.argv[2]

    my_seminar = socratic_model.Seminar(topic, model_one, model_two)

    for i in range(int(sys.argv[1])):
            my_seminar.next()
            # it is two requests per minute so we gotta wait .-.
            if (i+1) % 2 == 0:
                time.sleep(61)

    print(my_seminar)
import sys
import time
import google.generativeai as genai

import secret
import socratic_model


if __name__ == "__main__":
    genai.configure(api_key = secret.SECRET_KEY)

    model_one = socratic_model.GeminiActor()
    model_two = socratic_model.GeminiActor()
    my_seminar = socratic_model.Seminar(model_one, model_two)
    
    for i in range(int(sys.argv[1])):
        my_seminar.talk(0)
        time.sleep(5)
        my_seminar.talk(1)
        time.sleep(5)

    print(my_seminar)
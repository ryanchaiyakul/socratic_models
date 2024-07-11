import typing
import lzma

from . import actor

from firebase_admin import firestore


_example_prompt = "{} \
If a part starts with the characters \"[PROMPT]\", \
this message comes from the user and not your opponent. \
You may not use the characters \"[PROMPT]\" in your response. \
If you recieve one of these messages after your most recent output, \
please acknowledge and respond to it. After the next sentence, all \
responses from the user will be from your opponent. Can you begin the debate?"


DEFAULT_ENCODING = {actor.GeminiActor: "gemini"}


class Seminar:

    def __init__(self, prompt: str, *models: actor.Actor):
        self.__contents: typing.List[typing.Tuple[int, str]] = []
        self.__models = [model for model in models]
        self.__init_contents(prompt)
        self.__index = 0

    def to_dict(self, model_encoding: dict = DEFAULT_ENCODING) -> dict:
        content_encoded = []
        for k, v in self.__contents:
            content_encoded.append(lzma.compress("{}\n{}".format(k,v).encode('utf-8')))
        return {"content" : content_encoded, "models": [model_encoding[type(model)] for model in self.__models], "index": self.__index}

    def last_content_embedded(self)->dict:
        return {"index": self.__index, "content" : firestore.ArrayUnion([lzma.compress("{}\n{}".format(self.__contents[-1][0],self.__contents[-1][1]).encode('utf-8'))])}

    @staticmethod
    def from_dict(config: dict, model_encoding: dict = DEFAULT_ENCODING) -> "Seminar":
        inv_encoding = {v: k for k, v in model_encoding.items()}
        seminar = Seminar("NOT IMPORTANT", *[inv_encoding[encoding]() for encoding in config['models']])
        
        content = []
        for encoded in config['content']:
            content.append(lzma.decompress(encoded).decode('utf-8').split('\n', 1))
        seminar._Seminar__contents = content
        seminar._Seminar__index = config['index']
        return seminar


    def __init_contents(self, prompt: str):
        self.__contents.append((0, _example_prompt.format(prompt)))

    def add_statement(self, statement: str):
        self.__contents.append((0, "[PROMPT] {}".format(statement)))

    @property
    def contents(self):
        """ 
        A list of tuples of the format (participant number, content)
        """
        return self.__contents

    def __str__(self):
        """
        Outputs the dialogue in a human readable format
        """
        ret = ""
        for num, content in self.contents:
            ret += "{}: {}\n\n".format("Prompt" if num ==
                                       0 else "Participant {}".format(num), content)
        return ret

    def talk(self, index: int):
        if index < 0 or index > len(self.__models):
            raise ValueError("Index: {} is out of range".format(index))

        new_content = self.__models[index].generate_content(
            self.contents, index+1)
        self.__contents.append(
            (index+1, new_content))
        
    def next(self):
        """
        Calls talk for the next NPC participant
        """
        self.talk(self.__index)
        self.__index = (self.__index + 1) % len(self.__models)

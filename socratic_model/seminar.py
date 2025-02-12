import typing
import lzma
import datetime
import re

from . import actor

from firebase_admin import firestore


_commandable_prompt = "{} \
If a part starts with the characters \"[PROMPT]\", \
this message comes from the user and not your conversation partner. \
You may not use the characters \"[PROMPT]\" in your response. \
If you receive one of these messages after your most recent output, \
please acknowledge and respond to it. After this sentence, all \
responses from the user will be from your conversation partner."

DEFAULT_ENCODING = {actor.GeminiActor: "gemini", actor.GPTActor: 'gpt'}


class Seminar:
    """
    Handles all the internal API and buisness logic necessary to have a LLM discusion

    Features:
    - Loading and saving to a python dictionary object (with compression)
    - Output as a .cha
    - Simple calls to generate new content
    """

    def __init__(self, prompt: str, template: str, *models: actor.Actor):
        self.__contents: typing.List[typing.Tuple[int, str]] = []
        self.__models = [model for model in models]
        self.__init_contents(prompt, template)
        self.__index = 0

    def __init_contents(self, prompt: str, template):
        self.__contents.append((0, template.format(prompt)))

    @staticmethod
    def from_dict(config: dict, model_encoding: dict = DEFAULT_ENCODING) -> "Seminar":
        inv_encoding = {v: k for k, v in model_encoding.items()}
        seminar = Seminar(
            "NOT IMPORTANT", "NOT_IMPORTANT", *[inv_encoding[encoding]() for encoding in config['models']])

        contents = []
        for encoded in config['content']:
            index, content = lzma.decompress(
                encoded).decode('utf-8').split('\n', 1)
            contents.append((int(index), content))
        seminar._Seminar__contents = contents
        seminar._Seminar__index = int(config['index'])
        return seminar

    def to_dict(self, model_encoding: dict = DEFAULT_ENCODING) -> dict:
        """
        Get self.__contents encoded with lzma
        """
        content_encoded = []
        for k, v in self.__contents:
            content_encoded.append(lzma.compress(
                "{}\n{}".format(k, v).encode('utf-8')))
        return {"content": content_encoded, "models": [model_encoding[type(model)] for model in self.__models], "index": self.__index}

    def last_content_embedded(self) -> dict:
        return {"index": self.__index, "content": firestore.ArrayUnion([lzma.compress("{}\n{}".format(self.__contents[-1][0], self.__contents[-1][1]).encode('utf-8'))])}

    def __repr__(self):
        """
        Outputs the dialogue in a human readable format
        """
        ret = ""
        for num, content in self.contents:
            ret += "{}: {}\n\n".format("Prompt" if num ==
                                       0 else "Participant {}".format(num), content)
        return ret

    def to_cha(self):
        """
        Return the seminar as a cha file
        """
        llms = "".join(["SPE{} LLM{} Speaker, ".format(i, i)
                       for i in range(len(self.__models))])
        IDs = "".join(["@ID:\teng|llm_debate|HST|||||Host|||\n"] +
                      ["@ID:\teng|llm_debate|SPE{}|||||Speaker|||\n".format(i) for i in range(len(self.__models))])
        ret = "@UTF8\n@Begin\n@Languages:\teng\n@Participants:\tHST Prompt Host, {}\n{}@Date:\t{}\n".format(
            llms[:-2], IDs, datetime.datetime.today().strftime('%d-%b-%Y').upper())

        for num, content in self.contents:
            # Split into sentences
            # replace counting indices i.e 1., 2., 3. with a space instead
            content = re.sub(r'\b\d+\.\s*', ' ', content)
            for line in [s.strip() for s in re.findall(r'[^.!?]+[.!?]', content)]:
                line = "*{}:\t{}\n".format("HST" if num == 0 else "SPE{}".format(
                    num-1), line.replace("\"[PROMPT]\"", "&~PROMPT").replace('\n', ' '))
                ret += line
        return ret + "@End"

    def add_statement(self, statement: str):
        self.__contents.append((0, "[PROMPT] {}".format(statement)))

    @property
    def contents(self):
        """ 
        A list of tuples of the format (participant number, content)
        """
        return self.__contents

    def talk(self, index: int):
        if index < 0 or index > len(self.__models):
            raise ValueError("Index: {} is out of range".format(index))

        new_content = self.__models[index].generate_content(
            self.contents, index+1)
        self.__contents.append(
            (index+1, new_content))

    def next(self):
        """
        Calls talk for the next LLM participant
        """
        self.talk(self.__index)
        self.__index = (self.__index + 1) % len(self.__models)

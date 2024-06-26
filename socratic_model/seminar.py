import typing

from . import actor


_example_prompt = "{} \
If a part starts with the characters \"[PROMPT]\", \
this message comes from the user and not your opponent. \
You may not use the characters \"[PROMPT]\" in your response. \
If you recieve one of these messages after your most recent output, \
please acknowledge and respond to it. After the next sentence, all \
responses from the user will be from your opponent. Can you begin the debate?"

class Seminar:

    def __init__(self, prompt: str, *models: actor.Actor):
        self.__contents: typing.List[typing.Tuple[int, str]] = []
        self.__models = [model for model in models]
        self.__init_contents(prompt)

    def __init_contents(self, prompt: str):
        self.__contents.append((0, _example_prompt.format(prompt)))
    
    def add_statement(self, statement:str):
        self.__contents.append((0, "[PROMPT] {}".format(statement)))

    @property
    def contents(self):
        """ 
        A list of tuples of the format (participant number, content)
        """
        return self.__contents
    
    def __str__(self):
        ret = ""
        for num, content in self.contents:
            ret += "{}: {}\n\n".format("Prompt" if num == 0 else "Participant {}".format(num), content)
        return ret
    
    def talk(self, index: int):
        if index < 0 or index > len(self.__models):
            raise ValueError("Index: {} is out of range".format(index))
        
        new_content = self.__models[index].generate_content(self.contents, index+1)
        self.__contents.append(
            (index+1, new_content))

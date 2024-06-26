import typing

from . import actor


class Seminar:

    def __init__(self, *models: actor.Actor):
        self.__contents: typing.List[typing.Tuple[int, str]] = []
        self.__models = [model for model in models]
        self.__init_contents()

    def __init_contents(self):
        self.__contents.append((0, "You are debating against an opponent on whether golf is a sport. After the next sentence, all responses from the user will be from your opponent. Can you begin the debate?"))
    
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

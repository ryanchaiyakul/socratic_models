import abc
import typing
import google.generativeai as genai
import google.generativeai.types.content_types as content_types


class Actor(metaclass=abc.ABCMeta):
    """ Abstract class that hides specific gen ai implementation """

    @abc.abstractmethod
    def generate_content(self, context: typing.List[typing.Tuple[int, str]], num: int) -> str:
        """ Wrapper to generate content with passed dictionary as context """
        pass


class GeminiActor(Actor):

    def __init__(self, model: str = 'gemini-1.5-pro'):
        self.__model: genai.GenerativeModel = genai.GenerativeModel(
            model_name=model)

    def generate_content(self, context: typing.List[typing.Tuple[int, str]], num: int):
        return self.__model.generate_content(contents=self.__tuple_to_content(context, num)).text

    @staticmethod
    def __tuple_to_content(tuples: typing.List[typing.Tuple[int, str]], num: int) -> content_types.ContentsType:
        return content_types.to_contents([{'role': "model" if participant_num == num else "user", 'parts': {content}} for participant_num, content in tuples])

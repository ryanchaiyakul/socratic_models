import abc
import typing
import google.generativeai as genai
import google.generativeai.types.content_types as content_types

import openai

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

class GPTActor(Actor):

    _client: openai.OpenAI = None

    def __init__(self, model: str = 'gpt-4o-mini', key = None):
        if type(self)._client is None:
            if key is None:
                raise ValueError('Missing API Key for intial GPTActor')
            type(self)._client = openai.OpenAI(api_key=key)
        self.__model = model

    def generate_content(self, context: typing.List[typing.Tuple[int, str]], num: int):
        completion = type(self)._client.chat.completions.create(
            model=self.__model,
            store=True,
            messages=self.__tuple_to_content(context, num)
        )
        return completion.choices[0].message.content    # return the most likely completion


    @staticmethod
    def __tuple_to_content(tuples: typing.List[typing.Tuple[int, str]], num: int) -> content_types.ContentsType:
        def role_tag(tag: int, num: int) -> str:
            return {0: 'system', num: 'assistant'}.get(tag, 'user')
        return [{'role': role_tag(participant_num, num),'content': content} for participant_num, content in tuples]
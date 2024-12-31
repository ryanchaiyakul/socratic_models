import os
import typing
import torch
import xlsxwriter

from . import db, seminar

import EVM
import Levenshtein

from tqdm.notebook import tqdm

_wv = EVM.languageModelLayers('roberta-base', layers=[7])


class Utterance:

    def __init__(self, raw: str, wv: EVM.languageModelLayers = _wv):
        tag, content = raw.split('\t')
        self.tag = tag[:-1]
        self.content = content
        self.token_count = len(_wv._tokenize(raw)[0])

    def __repr__(self):
        return "{}: {}".format(self.tag, self.content)


class CHA:

    def __init__(self, path: str):
        with open(path, encoding='utf-8') as f:
            self.raw = f.read()

        self.utterances = [Utterance(raw_line) for raw_line in self.raw[self.raw.find(
            '*'):-5].split('\n')]  # trim \n@End


class Analysis:
    """
    Perform large-scale analysis on a folder of .cha files
    """

    def __init__(self, folder: str):
        self.root = folder
        self.chas: typing.Dict[str, CHA] = {}
        for f_name in os.listdir(self.root):
            #try:
            self.chas[f_name] = CHA(os.path.join(self.root, f_name))
            #except ValueError:
            #    print(f_name)
        self.workbook = xlsxwriter.Workbook('{}_analysis.xlsx'.format(folder))

    @staticmethod
    def convert_to_chas(db: db.DB, folder: str):
        for db_obj in db.seminar_collection.stream():
            sem_obj = seminar.Seminar.from_dict(db_obj.to_dict())
            with open('{}/{}.cha'.format(folder, db_obj.id), 'w') as f:
                f.write(sem_obj.to_cha())

    def evm(self, k: int, wv=_wv, sigma=0.3, dim=None, write_xlsx=True):
        mod = EVM.EVM(wv_model=wv, sigma=sigma, entropy_dim=dim)
        self.entries = []
        with torch.no_grad():
            for f_name, cha in tqdm(self.chas.items(), desc="EVM"):
                for i in range(len(cha.utterances)):
                    for j in range(1, k+1):
                        if (i+j) < len(cha.utterances):
                            u_i = cha.utterances[i]
                            u_j = cha.utterances[i+j]
                            self.entries.append((f_name,
                                                i,
                                                i+j,
                                                u_i.tag,
                                                u_j.tag,
                                                u_i.token_count,
                                                u_j.token_count,
                                                *mod(u_i.content, u_j.content)))
        if write_xlsx:
            self.__write_xlsx('standard_evm', ('fl', 'i', 'j', 'who_i',
                              'who_j', 'n_i', 'n_j', 'h_1', 'h_2'), self.entries)
        return self.entries

    def levenshtein(self, k: int, weights: typing.Tuple[int, int, int] = (1, 1, 1), write_xlsx=True):
        self.entries = []

        for f_name, cha in tqdm(self.chas.items(), desc="Levenshtein"):
            for i in range(len(cha.utterances)):
                for j in range(1, k+1):
                    if (i+j) < len(cha.utterances):
                        u_i = cha.utterances[i]
                        u_j = cha.utterances[i+j]
                        self.entries.append((f_name,
                                            i,
                                            i+j,
                                            u_i.tag,
                                            u_j.tag,
                                            u_i.token_count,
                                            u_j.token_count,
                                            Levenshtein.distance(u_i.content, u_j.content, weights=weights)))
        if write_xlsx:
            self.__write_xlsx('levenshtein', ('fl', 'i', 'j', 'who_i',
                              'who_j', 'n_i', 'n_j', 'd'), self.entries)
        return self.entries

    def __write_xlsx(self, sheet_name: str, titles: typing.Tuple[str], entries: typing.List[typing.Tuple[str]]):
        worksheet = self.workbook.add_worksheet(sheet_name)

        row = 0

        for data in ([titles] + entries):
            for i, field in enumerate(data):
                worksheet.write(row, i, field)
            row += 1

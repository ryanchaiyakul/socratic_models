import os
import typing
import torch
import xlsxwriter
from tqdm.autonotebook import tqdm

from . import db, seminar, custom_ceda
import Levenshtein


class Utterance:

    def __init__(self, raw: str):
        tag, content = raw.split('\t')
        self.tag = tag[:-1]
        self.content = content

    def __repr__(self):
        return "{}: {}".format(self.tag, self.content)


class CHA:

    def __init__(self, path: str):
        with open(path, encoding='utf-8') as f:
            self.raw = f.read()

        self.utterances = [Utterance(raw_line) for raw_line in self.raw[self.raw.find(
            '*'):-5].split('\n')]  # trim \n@End
        self.content = [u.content for u in self.utterances]
        self.tag = [u.tag for u in self.utterances]


class Analysis:
    """
    Perform large-scale analysis on a folder of .cha files
    """

    def __init__(self, folder: str):
        self.root = folder
        self.chas: typing.Dict[str, CHA] = {}
        for f_name in os.listdir(self.root):
            if f_name[-3:] == 'cha':
                self.chas[f_name] = CHA(os.path.join(self.root, f_name))
        self.workbook = xlsxwriter.Workbook('{}_analysis.xlsx'.format(folder))

    @staticmethod
    def convert_to_chas(db: db.DB, folder: str):
        for db_obj in db.seminar_collection.stream():
            sem_obj = seminar.Seminar.from_dict(db_obj.to_dict())
            with open('{}/{}.cha'.format(folder, db_obj.id), 'w') as f:
                f.write(sem_obj.to_cha())

    def evm(self, write_xlsx=True):
        mod = custom_ceda.CustomCEDA()
        self.entries = []
        with torch.no_grad():
            for f_name, cha in tqdm(self.chas.items(), desc="EVM"):
                mod.fit(cha.content)
                who_i = [tag for tag in cha.tag for _ in range(len(cha.tag))]
                who_j = cha.tag * len(cha.tag)
                mod.meta_data = [{'fl': f_name, 'who_i': i, 'who_j': j}
                                 for i, j in zip(who_i, who_j)]
                self.entries.append(mod.graph_df)
        # if write_xlsx:
        #    self.__write_xlsx('standard_evm', ('fl', 'i', 'j', 'who_i',
        #                      'who_j', 'n_i', 'n_j', 'h_1', 'h_2'), self.entries)
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

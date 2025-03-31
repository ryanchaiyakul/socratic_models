import convergence_entropy.CEDA as ceda
import pandas as pd
import numpy as np


class CustomCEDA(ceda.ceda_model):
    """ CustomCEDA for full graph"""

    def __init__(self,
            sigma: float = 1.,
            device: str = 'cpu',
            wv_model: str = 'roberta-base',
            wv_layers: list[int] = [8, -1]):
        super().__init__(sigma, device, wv_model, wv_layers)
        self.GRAPH = ceda.calc.fastGraph.fastGraphWithAnalyzer(analyzer_object=self.H)

    def fit(self, corpus, meta_data: list = [], save_texts: bool=False):
        self.GRAPH.fit(corpus)

        if save_texts:
            self.texts = corpus

        if meta_data:
            self.meta_data = meta_data

    def graph_df(self, residualize: bool = True):
        N = self.GRAPH.N.numpy()  # (n,)
        M = self.GRAPH.residual().numpy() if residualize else self.GRAPH.M.numpy()  # (n, n)

        Nx, Ny = np.meshgrid(N, N, indexing='ij')  # (n, n) grids
        n = np.arange(N.shape[0])

        # Flatten for DataFrame construction
        df = pd.DataFrame({
            'x': np.repeat(n, N.shape[0]),
            'y': np.tile(n, N.shape[0]),
            'Nx': Nx.flatten(),
            'Ny': Ny.flatten(),
            'Hxy': M.flatten(),
            'Myx':M.T.flatten()
        })

        if self.meta_data and (len(self.meta_data) == Nx.size):
            # If metadata exists and matches N's length, merge it based on Nx
            meta_df = pd.DataFrame(self.meta_data)
            df = meta_df.merge(df, left_index=True, right_on="Nx", how="right")

        return df

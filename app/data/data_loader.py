# app/data/data_loader.py

import pandas as pd
import os


class DataLoader:
    def __init__(self, data_path='app/data/'):
        self.data_path = data_path

    def load_csv(self, filename):
        filepath = os.path.join(self.data_path, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filepath} does not exist.")
        df = pd.read_csv(filepath)
        return df

    def load_excel(self, filename):
        filepath = os.path.join(self.data_path, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filepath} does not exist.")
        df = pd.read_excel(filepath)
        return df

    def load_json(self, filename):
        filepath = os.path.join(self.data_path, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filepath} does not exist.")
        df = pd.read_json(filepath)
        return df

# app/utils/geojson_handler.py

import json
import os


class GeoJSONHandler:
    def __init__(self, geojson_path='app/data/geojson/'):
        self.geojson_path = geojson_path

    def load_geojson(self, filename):
        filepath = os.path.join(self.geojson_path, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filepath} does not exist.")
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data

    def save_geojson(self, data, filename):
        filepath = os.path.join(self.geojson_path, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"GeoJSON data saved to {filepath}.")

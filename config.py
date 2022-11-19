import json

CONFIG_PATH = 'config.json'

def get_config(path):
    with open(path) as f:
        config = json.load(f)
        return config
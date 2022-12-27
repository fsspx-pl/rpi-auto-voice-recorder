import json

CONFIG_PATH = 'config.json'

def get_config():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
        return config
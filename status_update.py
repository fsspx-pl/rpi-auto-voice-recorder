import requests
import json
import threading

with open('status_update_config.json') as f:
    config = json.load(f)

def threadPost(url, data):
    try:
        x = requests.post(url, json=data, timeout=1.0)
    except:
        pass

def asyncPost(url, data):
    t = threading.Thread(target=threadPost, args=(url, data))
    t.start()
    return t

def updateChunkStatus(chunks_read, chunks_total, previous_update = None):
    # don't post if previous update didn't complete
    if previous_update is not None and previous_update.is_alive():
        return previous_update

    url = config["api_url"] + "chunks"
    data = {
        "id": config["id"],
        "password": config["password"],
        "chunks_read": chunks_read,
        "chunks_total": chunks_total
    }
    return asyncPost(url, data)
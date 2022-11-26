import requests
import threading
from config import CONFIG_PATH, get_config

def threadPost(url, data, timeout):
    try:
        requests.post(url, json=data, timeout=timeout)
    except:
        pass

def asyncPost(url, data, timeout):
    t = threading.Thread(target=threadPost, args=(url, data, timeout))
    t.start()
    return t

def updateChunkStatus(chunks_read, chunks_total, previous_update = None, timeout=1.0):
    # don't post if previous update didn't complete
    if previous_update is not None and previous_update.is_alive():
        return previous_update

    config = get_config(CONFIG_PATH)
    status_update = config['status_update']
    url = status_update['api_url'] + "chunks"
    data = {
        "id": status_update['id'],
        "password": status_update['password'],
        "chunks_read": chunks_read,
        "chunks_total": chunks_total
    }
    return asyncPost(url, data, timeout)
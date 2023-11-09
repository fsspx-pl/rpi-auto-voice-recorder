import time
from tusclient import client
from tusclient.storage import filestorage
from tusclient import exceptions
from dotenv import load_dotenv
import os
import queue
import threading
from log import log_message

def upload(filepath, target_name, logging_queue, retry_interval=30):
    load_dotenv()
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    bucket: str = os.environ.get("SUPABASE_BUCKET_NAME")

    headers = {
        'Authorization': 'Bearer %s' % key,
        'x-upsert': 'true'
    }
    supa_client = supa_client = client.TusClient(url + '/storage/v1/upload/resumable',
                                headers=headers)
    
    metadata = {
        'bucketName': bucket,
        'objectName': target_name,
        'contentType': 'audio/mp4'
    }

    tus_uploader = supa_client.uploader(
        filepath,
        chunk_size=6 * 1024 * 1024,
        client=supa_client,
        metadata=metadata,
        retries=2,
        retry_delay=5,
        store_url=True,
        url_storage=filestorage.FileStorage('storage.json')
    )

    remaining_chunks = True

    while remaining_chunks:
        try:
            # Attempt to upload
            tus_uploader.upload()
            # If successful, exit the loop
            remaining_chunks = False
        except exceptions.TusCommunicationError as e:
            logging_queue.put(f"Upload failed for {filepath}: {e}")
            
            time.sleep(retry_interval)
            
    logging_queue.put(f"Upload complete for {filepath}. URL: {tus_uploader.url}")

def custom_log(message):
    print(f"Custom Log: {message}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='File to upload to Supabase bucket')
    parser.add_argument('-f', '--file', help='path to a file to be uploaded', required=True)
    args = parser.parse_args()

    logging_queue = queue.Queue()
    logging_listener = threading.Thread(target=log_message, args=(logging_queue,))
    logging_listener.start()

    upload(args.file, 'test.wav', logging_queue)
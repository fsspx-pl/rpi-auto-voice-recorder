#!/usr/bin/env python3
import time
import os
import queue
import threading
from log import log_message
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

def upload(filepath, target_name, logging_queue, retry_interval=30):
    """
    Upload a file to MinIO with retry functionality.
    
    Args:
        filepath: Path to the file to upload
        target_name: Name of the file in the MinIO bucket
        logging_queue: Queue for logging messages
        retry_interval: Time to wait between retries in seconds
    """
    load_dotenv()
    minio_url = os.environ.get("MINIO_URL")
    access_key = os.environ.get("MINIO_ACCESSKEY")
    secret_key = os.environ.get("MINIO_SECRETKEY")
    bucket_name = os.environ.get("MINIO_BUCKET_NAME")
    
    # Determine content type based on file extension
    content_type = "application/octet-stream"
    if target_name.lower().endswith(('.wav')):
        content_type = "audio/wav"
    
    # Create MinIO client
    try:
        minio_client = Minio(
            minio_url.replace("http://", "").replace("https://", ""),
            access_key=access_key,
            secret_key=secret_key,
            secure=minio_url.startswith("https")
        )
        
        # Check if bucket exists
        found = minio_client.bucket_exists(bucket_name)
        if not found:
            minio_client.make_bucket(bucket_name)
            logging_queue.put(f"Created bucket {bucket_name}")
        else:
            logging_queue.put(f"Bucket {bucket_name} already exists")
    except S3Error as e:
        logging_queue.put(f"Error checking/creating bucket: {e}")
        return
    
    # Upload with retries
    max_attempts = 10
    attempt_count = 0
    upload_success = False
    
    while not upload_success and attempt_count < max_attempts:
        try:
            attempt_count += 1
            logging_queue.put(f"Uploading {filepath} to {bucket_name}/{target_name} (attempt {attempt_count})")
            
            # Perform the upload
            minio_client.fput_object(
                bucket_name, 
                target_name, 
                filepath,
                content_type=content_type
            )
            
            upload_success = True
            logging_queue.put(f"Upload complete for {filepath} to {bucket_name}/{target_name}")
            
        except S3Error as e:
            logging_queue.put(f"Upload failed for {filepath} (attempt {attempt_count}): {e}")
            
            if attempt_count < max_attempts:
                logging_queue.put(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logging_queue.put(f"Maximum retry attempts reached. Upload failed for {filepath}")
                break
                
        except Exception as e:
            logging_queue.put(f"Unexpected error during upload: {e}")
            
            if attempt_count < max_attempts:
                logging_queue.put(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logging_queue.put(f"Maximum retry attempts reached. Upload failed for {filepath}")
                break
    
    return upload_success

def main():
    """
    Main function to demonstrate usage of the upload function.
    """
    # The file to upload, change this path if needed
    source_file = "/tmp/test-file.txt"
    
    # The destination filename on the MinIO server
    destination_file = "my-test-file.txt"
    
    # Set up logging
    logging_queue = queue.Queue()
    logging_listener = threading.Thread(target=log_message, args=(logging_queue,))
    logging_listener.daemon = True
    logging_listener.start()
    
    # Upload the file
    upload(source_file, destination_file, logging_queue)
    
    # Wait for logging to complete
    logging_queue.join()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='File to upload to MinIO bucket')
    parser.add_argument('-f', '--file', help='path to a file to be uploaded', required=True)
    parser.add_argument('-t', '--target', help='target filename in the bucket', default=None)
    args = parser.parse_args()
    
    target_name = args.target if args.target else os.path.basename(args.file)
    
    logging_queue = queue.Queue()
    logging_listener = threading.Thread(target=log_message, args=(logging_queue,))
    logging_listener.daemon = True
    logging_listener.start()

    try:
        success = upload(args.file, target_name, logging_queue)
        if success:
            logging_queue.put(f"Upload process completed successfully")
        else:
            logging_queue.put(f"Upload process failed")
    except Exception as e:
        logging_queue.put(f"Error occurred: {e}")
    
    # Wait for logging to complete
    logging_queue.join()
def log_message(logging_queue):
    while True:
        message = logging_queue.get()
        print(message, flush=True)
        logging_queue.task_done()
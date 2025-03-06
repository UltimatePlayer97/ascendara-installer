import logging
from io import StringIO

log_stream = StringIO()

def setup_logging():
    logging.basicConfig(
        stream=log_stream,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
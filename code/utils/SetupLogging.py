import logging
from datetime import datetime
from datetime import datetime

def setup_logging(file_prefix):
    log_filename = f"{file_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO, # logging level >= INFO (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),  # output log to file
            logging.StreamHandler() # output log to console
        ]
    )
    return logging.getLogger(__name__)

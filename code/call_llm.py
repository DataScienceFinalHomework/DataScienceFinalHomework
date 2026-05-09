# Write a base scipt to call LLM API

import logging
from datetime import datetime

API_FILE = "my_api_key.txt" # the file storing the api key

def setup_logging():
    log_filename = f"Call_llm_file_logging_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO, # logging level >= INFO (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),  # output log to file
            logging.StreamHandler() # output log to console
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def ReadInAPI():
    """
    Read the api key from the API_FILE
    Return:
        a string: the api key
        None: if the API_FILE does not exit
    """
    api_key = None
    try:
        with open(API_FILE, "r") as f:
            api_key = f.read()
    except FileNotFoundError:
        logger.error(f"错误：找不到文件{API_FILE}，请检查路径是否正确。")
    return api_key
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
    try:
        with open("my_dream_data.txt", "r") as f:
            data = f.read()
    except FileNotFoundError:
        print("错误：找不到该文件，请检查路径是否正确。")
    # 这里可以编写后续处理逻辑，比如跳过该文件或记录日志
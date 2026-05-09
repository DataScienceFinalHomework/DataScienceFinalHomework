# Write a base scipt to call LLM API
"""
A useful function wrapped to call LLM api

The function prototype, parameters and return are here

Prototype:
    async def call_llm(prompt_system, prompt_user, session, RETRY_DELAY = 2, RETRY_ATTEMPTS = 3, timeout = 20, model_used = "deepseek-ai/DeepSeek-V3"):
Parameters:
    prompt_system: a string, the prompt needed to be post to LLM
        example: You are a expert in Computer Science
    prompt_user: a string, the prompt needed to be post to LLM
        example: explain what is data science in Chinese
    session: ...
    RETRY_DELAY: The time to delay if happens any error, defalut to 2
    RETRY_ATTEMPTS: The max times to delay if happens any error, defalut to 3
    timeout: The longest time to timeout
    model_used: The model used, defalut to deepseek-ai/DeepSeek-V3
Return:
    a tuple of (explanation, input_tokens, output_tokens)
    explanation: The result of LLM return

"""


import logging
from datetime import datetime
import asyncio
import random

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


async def call_llm(prompt_system, prompt_user, session, RETRY_DELAY = 2, RETRY_ATTEMPTS = 3, timeout = 20, model_used = "deepseek-ai/DeepSeek-V3"):
    """
    Call LLM API
    Parameters:
        prompt_system: a string, the prompt needed to be post to LLM
            example: You are a expert in Computer Science
        prompt_user: a string, the prompt needed to be post to LLM
            example: explain what is data science in Chinese
        session: ...
        RETRY_DELAY: The time to delay if happens any error, defalut to 2
        RETRY_ATTEMPTS: The max times to delay if happens any error, defalut to 3
        timeout: The longest time to timeout
        model_used: The model used, defalut to deepseek-ai/DeepSeek-V3
    Return:
        a tuple of (explanation, input_tokens, output_tokens)
        explanation: The result of LLM return
    """

    BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"
    my_api_key = ReadInAPI()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {my_api_key}"
    }

    payload = {
        "model": model_used,
        "temperature": 0.1,
        "messages": [
            {
                "role": "system", 
                "content": prompt_system
            },
            {
                "role": "user", 
                "content": prompt_user
            }
        ]
    }

    for attempt in range(RETRY_ATTEMPTS):
        try:
            async with session.post(BASE_URL, headers=headers, json=payload, timeout=timeout) as response:
                if response.status == 200:
                    result = await response.json() # .json()是个异步方法，必须await。
                    explanation = result["choices"][0]["message"]["content"]

                    # 获取token使用情况
                    usage = result.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)

                    logger.debug("Successfully called LLM")
                    return explanation, input_tokens, output_tokens

                elif response.status == 429:  # Rate limit
                    logger.warning(f"Rate limit hit, attempt {attempt + 1}")
                    delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 2)
                    await asyncio.sleep(delay)
                else:
                    error_text = response.text()
                    logger.error(f"HTTP {response.status}: {error_text}")
                    if attempt < RETRY_ATTEMPTS - 1:
                        delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Failed due to HTTP error: {error_text}")
                        return f"Error: HTTP {response.status}", 0, 0

        except asyncio.TimeoutError:
            logger.error(f"Timeout, attempt {attempt + 1}")
            if attempt < RETRY_ATTEMPTS - 1:
                delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            else:
                logger.error("Failed due to timeout")
                return "Error: Timeout", 0, 0

        except Exception as e:
            logger.error(f"Exception, attempt {attempt + 1}: {str(e)}")
            if attempt < RETRY_ATTEMPTS - 1:
                delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed due to exception: {str(e)}")
                return f"Exception: {str(e)}", 0, 0

    logger.error(f"Failed after {RETRY_ATTEMPTS} attempts")
    return "Failed after multiple retries", 0, 0

import json
import os
import asyncio
import aiohttp
from tqdm import tqdm
import random
import logging
from datetime import datetime
import csv

with open('my_api_key.txt', mode='r') as f:
    API_KEY = f.readline()

BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"
MAX_CONCURRENCY = 100
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2

OUTPUT_FILE = "term_def.jsonl"

def setup_logging():
    log_filename = f"term_def_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

def is_error_result(explanation):
    return explanation.startswith(("Error:", "Exception:", "Failed"))

async def definition_async(term, session):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": "deepseek-ai/DeepSeek-V3.2",
        "temperature": 0.1,
        "messages": [
            {
                "role": "system", 
                "content": "You are a helpful assistant for providing explanations in English of Chinese biomedical terms."
            },
            {
                "role": "user", 
                "content": f"What is '{term}'? Please explain in 50 words in English as if in an dictionary. Format: '**(term translated in English)** refers to ...'"
            }
        ]
    }

    for attempt in range(RETRY_ATTEMPTS):
        try:
            async with session.post(BASE_URL, headers=headers, json=payload, timeout=60) as response:
                if response.status == 200:
                    result = await response.json() # .json()是个异步方法，必须await。
                    explanation = result["choices"][0]["message"]["content"]

                    # 获取token使用情况
                    usage = result.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)

                    logger.debug(f"Successfully processed term: {term}")
                    return explanation, input_tokens, output_tokens

                elif response.status == 429:  # Rate limit
                    logger.warning(f"Rate limit hit for term '{term}', attempt {attempt + 1}")
                    delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 2)
                    await asyncio.sleep(delay)
                else:
                    error_text = response.text()
                    logger.error(f"HTTP {response.status} for term '{term}': {error_text}")
                    if attempt < RETRY_ATTEMPTS - 1:
                        delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Failed to process term '{term}' due to HTTP error: {error_text}")
                        return f"Error: HTTP {response.status}", 0, 0

        except asyncio.TimeoutError:
            logger.error(f"Timeout for term '{term}', attempt {attempt + 1}")
            if attempt < RETRY_ATTEMPTS - 1:
                delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to process term '{term}' due to timeout")
                return "Error: Timeout", 0, 0

        except Exception as e:
            logger.error(f"Exception for term '{term}', attempt {attempt + 1}: {str(e)}")
            if attempt < RETRY_ATTEMPTS - 1:
                delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to process term '{term}' due to exception: {str(e)}")
                return f"Exception: {str(e)}", 0, 0

    logger.error(f"Failed to process term '{term}' after {RETRY_ATTEMPTS} attempts")
    return "Failed after multiple retries", 0, 0



async def process_single_term(term, tid, session, semaphore):
    # 处理单个术语，使用信号量控制并发
    async with semaphore:
        explanation, input_tokens, output_tokens = await definition_async(term, session)
        return term, tid, explanation, input_tokens, output_tokens


def save_results_batch(results, output_file):
    # 批量保存结果到文件，只保存成功的结果
    successful_results = []
    error_count = 0

    for term, tid, explanation, input_tokens, output_tokens in results:
        if is_error_result(explanation):
            error_count += 1
        else:
            successful_results.append((term, tid, explanation, input_tokens, output_tokens))

    if successful_results:
        with open(output_file, "a", encoding="utf-8") as fout:
            for term, tid, explanation, input_tokens, output_tokens in successful_results:
                data = {
                    "term": term,
                    "termid":  tid,
                    "explanation": explanation,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
                fout.write(json.dumps(data, ensure_ascii=False) + "\n")
            fout.flush()

    return len(successful_results), error_count

async def main():
    logger.info("Starting explanation generation process...")

    word_dict = {}
    with open('xiehe_terms.csv', encoding='utf-8') as f:
        rd = csv.DictReader(f)
        for row in rd:
            word_dict[row['str']] = row['tid']

    # 如果文件已存在，读取已处理的术语
    processed_terms = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as fin:
            for line in fin:
                data = json.loads(line)
                processed_terms.add(data["term"])
        logger.info(f"Found {len(processed_terms)} already processed terms")
    
    # 过滤出未处理的术语
    items_to_process = [(term, tid) for term, tid in word_dict.items() if term not in processed_terms]
    logger.info(f"Total terms to process: {len(items_to_process)}")

    
    if not items_to_process:
        logger.info("No new terms to process. Exiting.")
        return
    
    # 创建信号量控制并发
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    # 分批处理，每批保存一次
    batch_size = 50000
    total_successful = 0
    total_errors = 0

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=MAX_CONCURRENCY),
        timeout=aiohttp.ClientTimeout(total=300)
    ) as session:

        # 创建所有任务
        tasks = [
            process_single_term(term, tid, session, semaphore) 
            for term, tid in items_to_process
        ]

        # 并发运行并用tqdm提供一个进度条
        results_batch = []
        completed_count = 0

        # as_complete()类似于gather()，但是是按完成顺序形成迭代器
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing terms"):
            try:
                result = await task # 从as_complete()出来的task都是已完成的，不需等待。
                term, tid, explanation, input_tokens, output_tokens = result
                results_batch.append((term, tid, explanation, input_tokens, output_tokens))
                completed_count += 1

                # 检查是否需要保存批次
                if len(results_batch) >= batch_size:
                    successful_count, error_count = save_results_batch(results_batch, OUTPUT_FILE)
                    total_successful += successful_count
                    total_errors += error_count
                    logger.info(f"Saved batch: {successful_count} successful, {error_count} errors")
                    results_batch = []
            except Exception as e:
                logger.error(f"Critical error in main loop: {e}") 

        # 保存最后一批结果
        try:
            if results_batch:
                successful_count, error_count = save_results_batch(results_batch, OUTPUT_FILE)
                total_successful += successful_count
                total_errors += error_count
                logger.info(f"Saved final batch: {successful_count} successful, {error_count} errors")
        except Exception as e:
                logger.error(f"Critical error in saving: {e}") 

    # 统计结果
    total_processed = len(items_to_process)
    logger.info("Processing complete!")
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Successful: {total_successful}")
    logger.info(f"Errors: {total_errors}")
    if total_processed > 0:
        logger.info(f"Success rate: {total_successful/total_processed*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())

import pandas as pd
import json
import os
import numpy as np
from collections import Counter
import asyncio
import aiohttp

# 读取 API key
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY_FILE = os.path.join(SCRIPT_DIR, "api_key.txt")

with open(API_KEY_FILE, "r", encoding='utf-8') as f:
    api_key = f.read().strip()

# Silicon Flow API 配置
API_BASE_URL = "https://api.siliconflow.com/v1/chat/completions"

# 读取数据
csv_file = os.path.join(SCRIPT_DIR, "../Datasets/DB.csv")
df = pd.read_csv(csv_file)

print(f"✓ 已加载 {len(df)} 条梦境记录")
print(f"✓ Series 列表: {df['Series'].unique().tolist()}")


def log_log_regression(sorted_entities):
    """
    对 rank 与 frequency 的对数值进行线性回归
    返回斜率、截距、相关系数、R^2 及线性关系判断
    """
    if not sorted_entities or len(sorted_entities) < 2:
        return None

    ranks = np.arange(1, len(sorted_entities) + 1, dtype=float)
    frequencies = np.array([freq for _, freq in sorted_entities], dtype=float)

    # 防御式处理：log 仅对正数定义
    valid_mask = frequencies > 0
    ranks = ranks[valid_mask]
    frequencies = frequencies[valid_mask]
    if len(ranks) < 2:
        return None

    log_ranks = np.log(ranks)
    log_freqs = np.log(frequencies)

    # 线性回归：log(freq) = slope * log(rank) + intercept
    slope, intercept = np.polyfit(log_ranks, log_freqs, 1)
    pred = slope * log_ranks + intercept

    # 相关系数与拟合优度
    corr = float(np.corrcoef(log_ranks, log_freqs)[0, 1])
    ss_res = float(np.sum((log_freqs - pred) ** 2))
    ss_tot = float(np.sum((log_freqs - np.mean(log_freqs)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # 简单规则：|r| >= 0.9 或 R^2 >= 0.8 视为近似线性
    is_linear = bool(abs(corr) >= 0.9 or r_squared >= 0.8)

    return {
        "n_points": int(len(log_ranks)),
        "slope": float(slope),
        "intercept": float(intercept),
        "correlation": corr,
        "r_squared": float(r_squared),
        "is_approximately_linear": is_linear,
    }


def save_series_results_to_json(series_results, json_path):
    """
    将当前已有的 Series 结果写入 JSON 文件
    """
    json_data = {}
    for series_name, data in series_results.items():
        json_data[series_name] = {
            'entities': data['entity_frequencies'],
            'total_unique_entities': len(data['entity_frequencies']),
            'regression_stats': data.get('regression_stats'),
        }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

async def extract_entities_async(dream_text, session):
    """
    使用 DeepSeek-V4-Flash API 从梦境文本中提取实体（异步版本）
    """
    prompt = f"""你是一个专业的自然语言处理专家，请从以下梦境文本中提取所有重要的人类实体（entities）。
实体包括：mother, father, brother, sister, friend 等，注意将同类、同义（如mom、mother）实体归为一类进行统计。
注意：提取到的实体统一用英文表示。

请以 JSON 格式返回结果，格式如下：
{{
    "entities": ["实体1", "实体2", "实体3", ...]
}}

梦境文本：
{dream_text}

请只返回 JSON 格式的结果，不要包含其他文本。"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "deepseek-ai/DeepSeek-V4-Flash",
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的自然语言处理专家。请严格按照 JSON 格式返回结果。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        async with session.post(API_BASE_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                result = await response.json()
                result_text = result["choices"][0]["message"]["content"]
                
                # 尝试解析 JSON
                try:
                    parsed = json.loads(result_text)
                    entities = parsed.get("entities", [])
                except json.JSONDecodeError:
                    # 如果解析失败，尝试从文本中提取
                    print(f"  ⚠ JSON 解析失败")
                    entities = []
                
                return entities
            else:
                print(f"  ✗ API 错误 ({response.status})")
                return []
    
    except Exception as e:
        print(f"  ✗ API 调用出错: {str(e)}")
        return []


async def process_series(series_name, dreams, session):
    """
    处理某个 Series 的所有梦境（异步版本，每次处理100条）
    """
    print(f"\n正在处理 Series: {series_name} (共 {len(dreams)} 条梦境)")
    
    all_entities = []
    batch_size = 100
    
    # 按批次处理（每批100条）
    for batch_start in range(0, len(dreams), batch_size):
        batch_end = min(batch_start + batch_size, len(dreams))
        batch = dreams[batch_start:batch_end]
        
        print(f"  [批次 {batch_start//batch_size + 1}] 处理第 {batch_start+1} 到 {batch_end} 条...", end="", flush=True)
        
        # 创建异步任务
        tasks = [extract_entities_async(dream, session) for dream in batch]
        
        # 并发执行
        results = await asyncio.gather(*tasks)
        
        # 合并结果
        for entities in results:
            all_entities.extend(entities)
        
        print(f" ✓ (提取到 {sum(len(e) for e in results)} 个实体)")
    
    # 统计实体频率
    entity_counter = Counter(all_entities)
    
    if not entity_counter:
        print(f"  ⚠ {series_name} 未提取到任何实体")
        return None
    
    # 按频率排序，创建 rank
    sorted_entities = entity_counter.most_common()
    regression_stats = log_log_regression(sorted_entities)
    
    result_data = {
        'Series': series_name,
        'entities': sorted_entities,
        'entity_frequencies': {entity: freq for entity, freq in sorted_entities},
        'regression_stats': regression_stats,
    }
    
    print(f"  ✓ 统计完成: 共 {len(entity_counter)} 个不同的实体")
    print(f"  ✓ 出现频率前 5 的实体:")
    for i, (entity, freq) in enumerate(sorted_entities[:5], 1):
        print(f"     rank={i}: {entity} ({freq} 次)")

    if regression_stats:
        print("  ✓ log-log 回归统计:")
        print(f"     相关系数 r = {regression_stats['correlation']:.4f}")
        print(f"     决定系数 R^2 = {regression_stats['r_squared']:.4f}")
        print(f"     回归方程: log(freq) = {regression_stats['slope']:.4f} * log(rank) + {regression_stats['intercept']:.4f}")
        print(f"     是否近似直线关系: {'是' if regression_stats['is_approximately_linear'] else '否'}")
    
    return result_data


async def main():
    # 按 Series 分组，处理所有 Series
    grouped = df.groupby('Series')
    
    series_results = {}
    
    # 创建异步会话
    async with aiohttp.ClientSession() as session:
        for idx, (series_name, group) in enumerate(grouped):
            dreams = group['Dream_Text'].tolist()
            result = await process_series(series_name, dreams, session)
            if result:
                series_results[series_name] = result

                # 增量保存：每处理完一个 Series 就写一次 JSON
                output_json = os.path.join(SCRIPT_DIR, "../entity_analysis_results.json")
                save_series_results_to_json(series_results, output_json)
                print(f"✓ 已增量保存 {series_name} 的结果到: {os.path.abspath(output_json)}")
    
    # 最终再保存一次，确保结果完整
    output_json = os.path.join(SCRIPT_DIR, "../entity_analysis_results.json")
    save_series_results_to_json(series_results, output_json)

    print(f"✓ 详细结果已保存: {os.path.abspath(output_json)}")

    if not series_results:
        print("\n⚠ 实体结果为空：仅保存了空 JSON（{}）。")


if __name__ == "__main__":
    asyncio.run(main())

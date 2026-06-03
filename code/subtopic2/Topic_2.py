import pandas as pd
import json
import numpy as np
import os
import json
import ast
from collections import Counter
import matplotlib.pyplot as plt
from plotnine import *

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

jsonl_file = os.path.join(SCRIPT_DIR, "../../Datasets/DB_LLM_processed.jsonl")

with open(jsonl_file, "r") as f:
    data = [json.loads(line) for line in f]

#提取data中的“dream_id"和"character_frequency"，存到新的data文件中
dream_ids = [item["dream_id"] for item in data]
character_frequencies = [item["character_frequency"] for item in data]
df = pd.DataFrame({
    "dream_id": dream_ids,
    "character_frequency": character_frequencies
})

#将df的“dream_id"按照_分割，只保留前半部分
df["dream_id"] = df["dream_id"].apply(lambda x: x.split("_")[0])

#先保存初步清洗后的数据
df.to_csv(os.path.join(SCRIPT_DIR, "../../Datasets/dream_cha_freq.csv"), index=False)

#合并同series梦境
merged = {}
for item in df.to_dict(orient="records"):
    raw_id = item.get("dream_id", "")
    char_freq = item.get("character_frequency", {})

    if raw_id not in merged:
        merged[raw_id] = Counter()

    if isinstance(char_freq, dict):
        merged[raw_id].update(char_freq)

#降序排列
rows = []
for did, counter in merged.items():
    sorted_items = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)
    rows.append({
        "dream_id": did,
        "character_frequency": dict(sorted_items)
    })

df_sorted = pd.DataFrame(rows)
out_file = os.path.join(SCRIPT_DIR, "../../Datasets/dream_sorted.csv")
df_sorted.to_csv(out_file, index=False)

print(f"排序后数据输出至: {os.path.abspath(out_file)}")


#以出现频率为 y，出现次数排名为 x，为每个梦境绘制散点图
#此时发现绘制出散点图显然不符合直线分布
#存储路径
plot_dir = os.path.join(SCRIPT_DIR, "../../Datasets/plots_x_y")
os.makedirs(plot_dir, exist_ok=True)

for _, row in df_sorted.iterrows():
    dream_id = row["dream_id"]
    char_freq = row["character_frequency"]

    sorted_values = list(char_freq.values())
    x_values = list(range(1, len(sorted_values) + 1))

    plt.figure(figsize=(8, 5))
    plt.scatter(x_values, sorted_values, alpha=0.75)
    plt.title(f"Dream {dream_id} Character Frequency Scatter")
    plt.xlabel("Frequency Rank")
    plt.ylabel("Frequency")
    plt.tight_layout()

    plot_path = os.path.join(plot_dir, f"{dream_id}_scatter.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()

print(f"原数据散点图已输出至: {os.path.abspath(plot_dir)}")

#以出现频率和出现次数排名的对数值绘制散点图
#此时发现绘制出散点图明显更接近于直线分布，说明数据符合幂律分布
#存储路径
plot_dir = os.path.join(SCRIPT_DIR, "../../Datasets/plots_logx_logy")
os.makedirs(plot_dir, exist_ok=True)

for _, row in df_sorted.iterrows():
    dream_id = row["dream_id"]
    char_freq = row["character_frequency"]

    sorted_values = list(char_freq.values())
    log_sorted_values = [np.log(v) for v in sorted_values if v > 0]

    x_values = list(range(1, len(sorted_values) + 1))
    log_x_values = [np.log(x) for x in x_values if x > 0]

    plt.figure(figsize=(8, 5))
    plt.scatter(log_x_values, log_sorted_values, alpha=0.75)
    plt.title(f"Dream {dream_id} Character Frequency Scatter")
    plt.xlabel("log Frequency Rank")
    plt.ylabel("log Frequency")
    plt.tight_layout()

    plot_path = os.path.join(plot_dir, f"{dream_id}_scatter.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()

print(f"对数数据散点图已输出至: {os.path.abspath(plot_dir)}")

#数据处理部分

#对每个梦境进行线性回归分析，计算斜率、截距、相关系数、R^2，并判断是否近似线性
regression_results = []
for _, row in df_sorted.iterrows():
    dream_id = row["dream_id"]
    char_freq = row["character_frequency"]

    sorted_values = list(char_freq.values())
    x_values = list(range(1, len(sorted_values) + 1))

    log_x_values = [np.log(x) for x in x_values if x > 0]
    log_sorted_values = [np.log(v) for v in sorted_values if v > 0]

    if len(log_x_values) >= 2 and len(log_sorted_values) >= 2:
        slope, intercept = np.polyfit(log_x_values, log_sorted_values, 1)
        pred = slope * np.array(log_x_values) + intercept

        corr = float(np.corrcoef(log_x_values, log_sorted_values)[0, 1])
        ss_res = float(np.sum((log_sorted_values - pred) ** 2))
        ss_tot = float(np.sum((log_sorted_values - np.mean(log_sorted_values)) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        is_linear = bool(abs(corr) >= 0.9 or r_squared >= 0.8)

        regression_results.append({
            "dream_id": dream_id,
            "slope": slope,
            "intercept": intercept,
            "correlation": corr,
            "r_squared": r_squared,
            "is_approximately_linear": is_linear
        })

#将线性回归结果保存到 JSON 文件
regression_json_path = os.path.join(SCRIPT_DIR, "../../Datasets/regression_results.json")

with open(regression_json_path, "w", encoding="utf-8") as f:    
    json.dump(regression_results, f, ensure_ascii=False, indent=4)
print(f"线性回归结果已保存至: {os.path.abspath(regression_json_path)}")

#除去出现频率为1的实体
data_path = os.path.join(SCRIPT_DIR, "../../Datasets/dream_sorted.csv")

with open(data_path, "r", encoding="utf-8") as f:
    df = pd.read_csv(f)

filtered_rows = []
for _, row in df.iterrows():
    dream_id = row["dream_id"]
    raw_freq = row["character_frequency"]

    char_freq = ast.literal_eval(raw_freq)

    filtered_freq = {k: v for k, v in char_freq.items() if v > 1}

    if filtered_freq:
        filtered_rows.append({
            "dream_id": dream_id,
            "character_frequency": dict(filtered_freq)
        })

filtered_df = pd.DataFrame(filtered_rows)
filtered_csv_path = os.path.join(SCRIPT_DIR, "../../Datasets/dream_filtered.csv")
filtered_df.to_csv(filtered_csv_path, index=False)
print(f"去除频率为1的实体后数据已保存至: {os.path.abspath(filtered_csv_path)}")

#对处理后数据以出现频率和出现次数排名的对数值绘制散点图
#存储路径
plot_dir = os.path.join(SCRIPT_DIR, "../../Datasets/plots_logx_logy_2")
os.makedirs(plot_dir, exist_ok=True)

for _, row in filtered_df.iterrows():
    dream_id = row["dream_id"]
    char_freq = row["character_frequency"]

    sorted_values = list(char_freq.values())
    log_sorted_values = [np.log(v) for v in sorted_values if v > 0]

    x_values = list(range(1, len(sorted_values) + 1))
    log_x_values = [np.log(x) for x in x_values if x > 0]

    plt.figure(figsize=(8, 5))
    plt.scatter(log_x_values, log_sorted_values, alpha=0.75)
    plt.title(f"Dream {dream_id} Character Frequency Scatter")
    plt.xlabel("log Frequency Rank")
    plt.ylabel("log Frequency")
    plt.tight_layout()

    plot_path = os.path.join(plot_dir, f"{dream_id}_scatter.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()

print(f"对数数据散点图已输出至: {os.path.abspath(plot_dir)}")


#再次对处理后的对每个梦境进行线性回归分析，计算斜率、截距、相关系数、R^2，并判断是否近似线性
regression_results = []
for _, row in filtered_df.iterrows():
    dream_id = row["dream_id"]
    char_freq = row["character_frequency"]

    sorted_values = list(char_freq.values())
    x_values = list(range(1, len(sorted_values) + 1))

    log_x_values = [np.log(x) for x in x_values if x > 0]
    log_sorted_values = [np.log(v) for v in sorted_values if v > 0]

    if len(log_x_values) >= 2 and len(log_sorted_values) >= 2:
        slope, intercept = np.polyfit(log_x_values, log_sorted_values, 1)
        pred = slope * np.array(log_x_values) + intercept

        corr = float(np.corrcoef(log_x_values, log_sorted_values)[0, 1])
        ss_res = float(np.sum((log_sorted_values - pred) ** 2))
        ss_tot = float(np.sum((log_sorted_values - np.mean(log_sorted_values)) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        is_linear = bool(abs(corr) >= 0.9 or r_squared >= 0.8)

        regression_results.append({
            "dream_id": dream_id,
            "slope": slope,
            "intercept": intercept,
            "correlation": corr,
            "r_squared": r_squared,
            "is_approximately_linear": is_linear
        })

#将线性回归结果保存到 JSON 文件
regression_json_path_2 = os.path.join(SCRIPT_DIR, "../../Datasets/regression_results_2.json")

with open(regression_json_path_2, "w", encoding="utf-8") as f:    
    json.dump(regression_results, f, ensure_ascii=False, indent=4)
print(f"线性回归结果已保存至: {os.path.abspath(regression_json_path_2)}")

#读取两部分回归的jsonl文件，对R^2进行比较，作箱线图

with open(regression_json_path, "r", encoding="utf-8") as f:
    regression_results_1 = json.load(f)
r_squared_1 = [res["r_squared"] for res in regression_results_1]

df1 = pd.DataFrame({"R2": r_squared_1, "group": "Original"})

p1 = (
    ggplot(df1, aes(x="group", y="R2", fill="group"))
    + geom_boxplot(width=0.3)
    + ggtitle("R^2 Values Before Filtering")
    + xlab("Before")
    + ylab("R^2")
    + ylim(0.5, 1.0)
    + theme_bw()
)
p1.save(os.path.join(SCRIPT_DIR, "../../Datasets/r_squared_before.png"), dpi=150)


with open(regression_json_path_2, "r", encoding="utf-8") as f:
    regression_results_2 = json.load(f)
r_squared_2 = [res["r_squared"] for res in regression_results_2]

df2 = pd.DataFrame({"R2": r_squared_2, "group": "Filtered"})

p2 = (
    ggplot(df2, aes(x="group", y="R2", fill="group"))
    + geom_boxplot(width=0.3)
    + ggtitle("R^2 Values After Filtering")
    + xlab("After")
    + ylab("R^2")
    + ylim(0.5, 1.0)
    + theme_bw()
)
p2.save(os.path.join(SCRIPT_DIR, "../../Datasets/r_squared_after.png"), dpi=150)
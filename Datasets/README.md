# Datasets目录

数据文件目录，存储原始梦境数据及各工具处理结果。

## 数据来源

### DB系列：DreamBank爬虫采集

| 文件 | 说明 |
|------|------|
| DB.csv | 原始数据（Series, Dream_Text, Word_Count），45221条 |
| DB_VADER.csv | VADER情感分析结果 |
| DB_EMPATH.csv | EMPATH主题分类结果 |
| DB_SPACY.csv | SPACY NLP分析结果 |
| DB_wrapped.xml | XML包装格式，用于LLM处理 |

### SDDB系列：Sleep and Dream DataBase下载

| 文件 | 说明 |
|------|------|
| SDDB.csv | 原始数据（Survey Name, Dream Text, Word Count），35511条 |
| SDDB_VADER.csv | VADER情感分析结果 |
| SDDB_EMPATH.csv | EMPATH主题分类结果 |
| SDDB_SPACY.csv | SPACY NLP分析结果 |

---

## 处理工具说明

### VADER
情感分析工具，输出字段：
- `pos`, `neg`, `neu`, `compound` - 情感值
- `difference` = pos - neg
- `log` = log((pos + 1e-5)/(neg + 1e-5))

### EMPATH
主题分类工具，194个预训练词汇类别（值域[0,1]），包括：
family, fear, joy, love, death, violence, school, work, home, travel, medical_emergency, crime, wedding, dance, music...

### SPACY
NLP工具包，输出字段：
- `person_list`, `location_list` - 人物和地点实体
- `noun_chunks`, `action_verbs`, `adjectives` - 语法分析
- `sentence_count` - 句子计数

---

## 其他文件

- `entity_analysis_results.json`: 实体频率分析结果（已处理约5k条数据）
- `wrap_dreams.py`: CSV转XML包装工具
- plot_x_y、plot_logx_logy：课题二出图
- regression_results.json:课题二回归结果

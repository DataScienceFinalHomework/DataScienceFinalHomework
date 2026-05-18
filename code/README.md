# code目录

代码模块目录，包含数据爬取、处理及LLM调用相关代码。

## 目录结构

```
code/
├── utils/                  # 工具函数模块
│   ├── CallLLM.py          # LLM API异步调用封装
│   ├── SetupLogging.py     # 日志配置工具
│   └── my_api_key.txt      # API密钥配置文件
├── process_data/           # LLM数据处理模块
│   ├── process_data.ipynb  # 批量处理Notebook
│   ├── test_process.py     # API测试脚本
│   └── bio_term_explain_LLM.py  # 参考实现
├── test_code/              # 测试代码目录
├── crawler_get_DreamBank.py    # DreamBank爬虫脚本
└── wash_SSDB_data.py       # 数据清洗脚本(待完善)
```

## 文件说明

- **crawler_get_DreamBank.py**: 从DreamBank.net爬取梦境数据
- **utils/CallLLM.py**: 封装异步LLM API调用，支持重试和超时控制
- **utils/SetupLogging.py**: 日志配置，同时输出到文件和终端
- **process_data/process_data.ipynb**: 使用LLM批量提取梦境实体信息

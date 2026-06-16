# Utils

This folder contains shared helper modules used by the final project code.

## Modules

| File | Purpose |
| --- | --- |
| `CallLLM.py` | Async wrapper for calling the SiliconFlow chat-completion API. |
| `SetupLogging.py` | Logging setup helper for scripts and notebooks. |

## `CallLLM.py`

`CallLLM.py` provides `call_llm`, an asynchronous helper for sending system and user prompts to an LLM endpoint.

Main behavior:

- Reads the API key from `my_api_key.txt` in the same folder.
- Sends requests to `https://api.siliconflow.com/v1/chat/completions`.
- Uses `aiohttp` for asynchronous HTTP requests.
- Supports configurable retry delay, retry count, request timeout, and model name.
- Retries on rate limits, timeouts, and transient request failures.
- Returns a tuple of `(explanation, input_tokens, output_tokens)`.

Default model:

```text
deepseek-ai/DeepSeek-V3
```

Typical usage pattern:

```python
import aiohttp
from utils.CallLLM import call_llm
from utils.SetupLogging import setup_logging

logger = setup_logging("llm_process")

async with aiohttp.ClientSession() as session:
    explanation, input_tokens, output_tokens = await call_llm(
        prompt_system="You are an expert in data science.",
        prompt_user="Explain what data science is.",
        session=session,
        logger=logger,
    )
```

## `SetupLogging.py`

`SetupLogging.py` provides `setup_logging(file_prefix)`.

The helper creates a timestamped log file and configures logging output to both:

- a local `.log` file
- the terminal

Generated log files are ignored by Git.

## Local secrets

`my_api_key.txt` is a local-only secret file and must not be committed. It is already covered by the project `.gitignore`.

Expected local layout:

```text
utils/
├── CallLLM.py
├── SetupLogging.py
└── my_api_key.txt    # local only, ignored by Git
```

Do not hard-code API keys in Python files or notebooks. Keep credentials in local ignored files or environment-specific secret management.

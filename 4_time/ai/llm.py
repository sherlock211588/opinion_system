"""
LLM 调用层
=========
通过 OpenAI 兼容接口调用硅基流动 (SiliconFlow) API。
也兼容 DeepSeek / 通义千问 / Ollama / vLLM 等任何 OpenAI 兼容服务。
"""

import os
from openai import OpenAI

# ---- 配置（从环境变量读取，无则用默认值） ----
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
API_KEY = os.getenv("LLM_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")
TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """懒加载 OpenAI 客户端（避免导入时就校验 API Key）"""
    global _client
    if _client is None:
        _client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    return _client


def chat(messages: list[dict[str, str]], timeout: int | None = None) -> str:
    """
    发送消息到 LLM，返回纯文本回答。

    参数：
      messages: [{"role":"system","content":"..."}, {"role":"user","content":"..."}]
      timeout:  超时秒数，默认用环境变量 LLM_TIMEOUT

    异常：
      openai.AuthenticationError — API Key 无效
      openai.RateLimitError      — 额度耗尽/限流
      openai.APIConnectionError  — 网络不通
      openai.APITimeoutError     — 请求超时
      openai.APIError            — 其他 API 错误
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=MAX_TOKENS,
        stream=False,
        timeout=timeout or TIMEOUT,
    )
    return response.choices[0].message.content

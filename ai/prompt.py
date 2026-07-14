"""
Prompt 模板
==========
系统 prompt + message 拼接。
可根据 page_type 切换不同 prompt 风格。
"""

SYSTEM_PROMPT_EVENT = """你是“舆见”舆情智能分析系统的 AI 助手。

你的职责是基于下方提供的事件数据，回答用户的舆情分析问题。

规则：
1. 只使用下面提供的数据回答，不要编造信息。
2. 如果数据不足以回答，明确说“当前数据不足以判断该问题”。
3. 回答简洁专业，控制在 300 字以内。
4. 如果用户问风险或应对建议，结合阶段数据、情感数据和预警等级给出分析。
5. 不要输出你的思考过程，直接给出结论。"""

SYSTEM_PROMPT_ARTICLE = """你是“舆见”舆情智能分析系统的 AI 助手。

你的职责是基于下方提供的文章数据，回答用户的问题。

规则：
1. 只使用下面提供的数据回答，不要编造信息。
2. 回答简洁专业，控制在 200 字以内。
3. 不要输出你的思考过程，直接给出结论。"""

SYSTEM_PROMPT_DEFAULT = """你是“舆见”舆情智能分析系统的 AI 助手。
请基于当前系统数据，简洁专业地回答用户的问题。控制在 200 字以内。"""


def build_messages(
    context: str,
    question: str,
    page_type: str = "event_detail",
) -> list[dict[str, str]]:
    """
    拼装发送给 LLM 的 messages 列表。

    参数：
      context:    build_event_context() / build_article_context() 的输出
      question:   用户问题
      page_type:  "event_detail" | "article_detail" | "home" | "community"
    """
    system_map = {
        "event_detail": SYSTEM_PROMPT_EVENT,
        "article_detail": SYSTEM_PROMPT_ARTICLE,
    }
    system_prompt = system_map.get(page_type, SYSTEM_PROMPT_DEFAULT)

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{context}\n\n用户问题：{question}"},
    ]

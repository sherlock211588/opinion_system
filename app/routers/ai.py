"""
AI 问答路由
==========
POST /api/ai/chat — 舆情 AI 问答

路由通过工厂函数 create_ai_router() 创建，
避免直接导入 server.py 的数据全局变量。
"""

from __future__ import annotations
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from ai.context import build_event_context, build_article_context
from ai.prompt import build_messages
from ai.llm import chat as llm_chat


# ============================================================
#  请求 Schema
# ============================================================

class ChatRequest(BaseModel):
    page_type: str = "event_detail"      # event_detail | article_detail | home | community
    event_id: str | None = None
    article_id: str | None = None
    question: str = ""

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("问题不能为空")
        return v

    @field_validator("page_type")
    @classmethod
    def valid_page_type(cls, v: str) -> str:
        allowed = {"event_detail", "article_detail", "home", "community"}
        if v not in allowed:
            raise ValueError(f"page_type 必须是 {' / '.join(sorted(allowed))}")
        return v


# ============================================================
#  工厂函数：注入数据依赖
# ============================================================

def create_ai_router(
    all_events: dict[str, dict[str, Any]],
    articles_by_event: dict[str, list[dict[str, Any]]],
    prop_nodes_by_event: dict[str, list[dict[str, Any]]],
    prop_event_keywords: dict[str, dict[str, Any]],
    pipe: Any,
) -> APIRouter:
    """
    创建 AI 问答路由。

    参数全部由 server.py 在启动时注入，
    避免 router 层直接 import 全局变量。
    """
    router = APIRouter()

    @router.post("/chat", summary="舆情 AI 问答")
    def ai_chat(req: ChatRequest) -> dict[str, Any]:
        # ---- 1. 参数校验 ----
        if req.page_type == "event_detail" and req.event_id:
            if req.event_id not in all_events:
                return {
                    "code": 404,
                    "message": f"事件 {req.event_id} 不存在",
                    "data": None,
                }

        if req.page_type == "article_detail" and req.article_id:
            found = False
            for arts in articles_by_event.values():
                for a in arts:
                    nid = a.get("news_id", a.get("article_id", ""))
                    if str(nid) == str(req.article_id):
                        found = True
                        break
                if found:
                    break
            if not found:
                return {
                    "code": 404,
                    "message": f"文章 {req.article_id} 不存在",
                    "data": None,
                }

        # ---- 2. 收集上下文 ----
        try:
            if req.page_type == "article_detail" and req.article_id:
                context = build_article_context(
                    req.article_id, all_events, articles_by_event,
                )
            elif req.event_id:
                context = build_event_context(
                    req.event_id, all_events, articles_by_event,
                    prop_nodes_by_event, prop_event_keywords, pipe,
                )
            else:
                context = "当前页面无特定事件或文章数据。请基于知识回答用户问题。"
        except Exception as exc:
            return {
                "code": 500,
                "message": f"上下文收集失败：{exc}",
                "data": None,
            }

        # ---- 3. 拼装 messages ----
        messages = build_messages(context, req.question, req.page_type)

        # ---- 4. 调用 LLM ----
        try:
            answer = llm_chat(messages)
        except Exception as exc:
            error_type = type(exc).__name__
            error_msg = str(exc)

            # 用 openai 库的异常类型判断，同时也兼容 httpx/requests 异常
            if "AuthenticationError" in error_type or "401" in error_msg:
                return {
                    "code": 503,
                    "message": "大模型 API Key 无效，请联系管理员",
                    "data": None,
                }
            if "RateLimitError" in error_type or "429" in error_msg:
                return {
                    "code": 503,
                    "message": "大模型 API 额度不足或请求过于频繁",
                    "data": None,
                }
            if "APIConnectionError" in error_type or "ConnectError" in error_type or "Connection" in error_type:
                return {
                    "code": 503,
                    "message": "无法连接大模型 API，请检查网络或 API 地址配置",
                    "data": None,
                }
            if "Timeout" in error_type or "timeout" in error_msg.lower():
                return {
                    "code": 503,
                    "message": "大模型响应超时，请稍后重试",
                    "data": None,
                }
            # 兜底
            return {
                "code": 503,
                "message": f"大模型服务异常：{error_msg[:100]}",
                "data": None,
            }

        # ---- 5. 返回 ----
        return {
            "code": 200,
            "message": "success",
            "data": {
                "answer": answer,
                "sources": [],
            },
        }

    return router

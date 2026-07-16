"""
上下文收集层
===========
根据 event_id / article_id 从内存数据中提取结构化上下文，
拼接成 LLM 可直接理解的纯文本。
"""

from __future__ import annotations
from typing import Any


def _safe_get(d: dict, *keys: str, default: Any = "暂无") -> Any:
    """多级安全取值，任一环节为 None/falsy 返回 default"""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, None)
        else:
            return default
        if d is None:
            return default
    return d if d not in (None, "") else default


def _truncate(text: str, max_chars: int = 300) -> str:
    """截断过长文本"""
    if not text:
        return ""
    return text[:max_chars] + ("..." if len(text) > max_chars else "")


def _format_sentiment(dist: dict) -> str:
    """格式化情感分布"""
    if not dist:
        return "无数据"
    pos = dist.get("positive", 0)
    neg = dist.get("negative", 0)
    neu = dist.get("neutral", 0)
    return f"正面{pos:.0%} 负面{neg:.0%} 中性{neu:.0%}"


def _format_composite(breakdown: dict | None) -> str:
    """格式化四维热度拆解"""
    if not breakdown:
        return "无数据"
    return (
        f"报道量{breakdown.get('volume', 0):.0f} "
        f"情感分歧{breakdown.get('sentiment_volatility', 0):.0f} "
        f"平台扩散{breakdown.get('platform_spread', 0):.0f} "
        f"互动热度{breakdown.get('engagement', 0):.0f}"
    )


def build_event_context(
    event_id: str,
    all_events: dict[str, dict],
    articles_by_event: dict[str, list],
    prop_nodes_by_event: dict[str, list],
    prop_event_keywords: dict[str, dict],
    pipe: Any,
) -> str:
    """
    根据 event_id 组装事件分析上下文。

    返回一段结构化的纯文本，可直接放进 LLM user message。
    """
    event = all_events.get(event_id)
    if not event:
        return f"事件 {event_id} 不存在。"

    # ---- 基础信息 ----
    parts: list[str] = []
    parts.append(f"【事件ID】{event_id}")
    parts.append(f"【事件标题】{_safe_get(event, 'event_title')}")
    parts.append(f"【事件分类】{_safe_get(event, 'category')}")

    # 时间范围
    ts = event.get("timeseries", [])
    if ts:
        parts.append(f"【数据时间范围】{ts[0].get('time', '?')} 至 {ts[-1].get('time', '?')}（共{len(ts)}个时间点）")

    # 情感分布
    parts.append(f"【情感分布】{_format_sentiment(event.get('sentiment_distribution', {}))}")

    # ---- 生命周期（跑 pipeline） ----
    articles = articles_by_event.get(event_id)
    prop_nodes = None
    if event_id in prop_nodes_by_event:
        raw = prop_nodes_by_event[event_id]
        from collections import defaultdict
        prop_nodes = []
        for rn in raw:
            nid = rn.get("node_id", rn.get("id", ""))
            prop_nodes.append({
                "node_id": nid,
                "account_name": rn.get("account_name", rn.get("user_name", "")),
                "follower_count": rn.get("follower_count", 0),
                "is_verified": rn.get("is_verified", False),
                "post_time": rn.get("post_time", rn.get("time", "")),
                "source": rn.get("source", ""),
                "parent_node_id": rn.get("parent_node_id"),
                "forward_count": rn.get("forward_count", rn.get("comment_count", 0)),
                "title": rn.get("title", ""),
            })

    mapped_articles = None
    if articles:
        mapped_articles = []
        for a in articles:
            mapped_articles.append({
                "id": a.get("news_id", ""),
                "article_id": a.get("news_id", ""),
                "title": a.get("title", ""),
                "cleaned_text": a.get("text", ""),
                "source": a.get("source", ""),
                "url": a.get("url", ""),
                "publish_time": a.get("publish_time", ""),
                "sentiment_intensity": (
                    0.3 if a.get("sentiment") == "positive"
                    else 0.7 if a.get("sentiment") == "negative"
                    else 0.5
                ),
                "is_verified": False,
                "follower_count": 0,
                "forward_count": 0,
                "hours_since_event": 24.0,
            })

    try:
        report = pipe.event_report(event, mapped_articles, prop_nodes)
    except Exception:
        report = {}

    lifecycle = report.get("lifecycle", {}) if isinstance(report, dict) else {}
    if lifecycle and "error" not in lifecycle:
        parts.append(f"【当前阶段】{_safe_get(lifecycle, 'current_stage')}")
        probs = lifecycle.get("stage_probabilities", {})
        if probs:
            parts.append(f"【阶段概率】" + " ".join(f"{k}{v:.0%}" for k, v in probs.items()))
        parts.append(f"【趋势方向】{_safe_get(lifecycle, 'trend_direction')}")
        parts.append(f"【热度指数】{_safe_get(lifecycle, 'current_heat_index')}")
        parts.append(f"【四维热度】{_format_composite(lifecycle.get('composite_index_breakdown'))}")
        warning = lifecycle.get("critical_early_warning", {})
        if warning:
            level = warning.get("warning_level", "none")
            parts.append(f"【预警等级】{level} — {_safe_get(warning, 'message')}")

    # ---- 传播分析 ----
    propagation = report.get("propagation", {}) if isinstance(report, dict) else {}
    if propagation and "error" not in propagation:
        parts.append(f"【传播摘要】{_safe_get(report, 'propagation_summary')}")
        parts.append(f"【传播深度】{_safe_get(propagation, 'propagation_depth')}")
        key_nodes = propagation.get("key_nodes", []) or []
        if key_nodes:
            top = key_nodes[:5]
            parts.append("【关键传播节点】")
            for kn in top:
                scores = kn.get("graph_scores", {})
                parts.append(
                    f"  - {kn.get('account_name', '?')} "
                    f"(角色:{kn.get('role', '?')} "
                    f"PageRank:{scores.get('pagerank', 0):.3f})"
                )

    # ---- 文章统计 + 判假 ----
    articles_list = report.get("articles", []) if isinstance(report, dict) else []
    article_stats = report.get("article_stats", {}) if isinstance(report, dict) else {}
    if article_stats:
        parts.append(
            f"【相关文章】{article_stats.get('total', 0)}篇 "
            f"(可信{article_stats.get('real', 0)} 待验证{article_stats.get('uncertain', 0)} "
            f"疑似虚假{article_stats.get('fake', 0)})"
        )
    if articles_list:
        parts.append("【可疑文章举例】")
        fake_articles = [a for a in articles_list if a.get("verdict") == "疑似虚假"][:3]
        for a in fake_articles:
            parts.append(f"  - 《{a.get('title', '?')}》 可信度:{a.get('confidence_score', 0):.0f}%")
        if not fake_articles:
            parts.append("  当前无标记为虚假的文章。")

    return "\n".join(parts)


def build_article_context(
    article_id: str,
    all_events: dict[str, dict],
    articles_by_event: dict[str, list],
) -> str:
    """
    根据 article_id 查找单篇文章的上下文。
    """
    # 遍历所有事件的文章列表找到目标
    target = None
    for eid, arts in articles_by_event.items():
        for a in arts:
            nid = a.get("news_id", a.get("article_id", ""))
            if str(nid) == str(article_id):
                target = a
                break
        if target:
            break

    if not target:
        return f"文章 {article_id} 不存在。"

    parts = [
        f"【文章ID】{article_id}",
        f"【标题】{_safe_get(target, 'title')}",
        f"【来源】{_safe_get(target, 'source')}",
        f"【发布时间】{_safe_get(target, 'publish_time')}",
        f"【正文】{_truncate(target.get('text', target.get('cleaned_text', '')), 500)}",
        f"【情感倾向】{_safe_get(target, 'sentiment')}",
    ]

    return "\n".join(parts)

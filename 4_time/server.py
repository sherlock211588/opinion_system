"""
4号工程师 — API 接口
====================
启动: uvicorn server:app --host 0.0.0.0 --port 8001 --reload
文档: http://localhost:8001/docs
"""

import json
import math
import os
import sys
import csv as _csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 加载 .env（必须在其他模块之前，确保环境变量已就绪）
load_dotenv(Path(__file__).resolve().parent / ".env")

# 确保导入路径
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

from time_series.pipeline import Pipeline
from time_series.cross_event import CrossEventAnalyzer

# --- 用户认证模块 ---
from app.database import engine, Base
import app.models  # noqa: F401  确保 User 表被 SQLAlchemy 发现
from app.routers.auth import router as auth_router

Base.metadata.create_all(bind=engine)  # 首次启动自动建表（已有则跳过）

# ============================================================
# 启动：加载所有数据
# ============================================================
app = FastAPI(
    title="网络舆情智能分析系统 API",
    description="4号工程师 — 生命周期 + 传播溯源 + 虚假检测 + 跨事件因果",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册用户认证路由
app.include_router(auth_router, prefix="/api/auth", tags=["用户认证"])

# AI 问答路由（延迟创建，等 pipe 初始化后再追加）
_ai_router_created = False

ROOT = PROJECT  # 数据在 4_time/ 内部

# --- 加载 3.data ---
with open(ROOT / "3.data" / "event_timeseries_result.json", "r", encoding="utf-8") as f:
    events_list = json.load(f)
ALL_EVENTS: dict[str, dict] = {e["event_id"]: e for e in events_list}

# --- 合并 3号富字段（event_table_llm.csv）---
# 3号时序 JSON 只有 7 个基础字段，summary/keywords/persons/locations/source_distribution
# 存在 CSV 里，这里补入 ALL_EVENTS，后续 pipeline → server → 前端一条链路自动透出。
_llm_csv = ROOT / "3.data" / "event_table_llm.csv"
if not _llm_csv.exists():
    _llm_csv = ROOT.parent / "opinion_system-dev" / "data" / "event_table_llm.csv"
if _llm_csv.exists():
    _missing = 0
    with open(_llm_csv, "r", encoding="utf-8-sig") as _f:
        for _row in _csv.DictReader(_f):
            _eid = _row.get("event_id", "").strip()
            if not _eid or _eid not in ALL_EVENTS:
                _missing += 1
                continue
            _ev = ALL_EVENTS[_eid]

            # 摘要 — LLM 生成的事件描述
            _summary = _row.get("event_summary", "").strip()
            if _summary:
                _ev["summary"] = _summary

            # 关键词 — JSON 字符串
            _kw = _row.get("event_keywords", "").strip()
            if _kw and not _ev.get("keywords"):
                _ev["keywords"] = _kw

            # 涉及人物 — JSON 字符串
            _persons = _row.get("event_persons", "").strip()
            if _persons:
                _ev["persons"] = _persons
                _ev["event_persons"] = _persons

            # 涉及地点 — JSON 字符串
            _locations = _row.get("event_locations", "").strip()
            if _locations:
                _ev["locations"] = _locations
                _ev["event_locations"] = _locations

            # 起止时间 — CSV 字段更精确
            _start = _row.get("start_time", "").strip()
            if _start:
                _ev["start_time"] = _start
            _end = _row.get("end_time", "").strip()
            if _end:
                _ev["end_time"] = _end

            # 平台分布 — JSON 字符串，3号格式 [{source, news_num, ratio}]
            _sd = _row.get("source_distribution_json", "").strip()
            if _sd:
                _ev["source_distribution"] = _sd
    print(f"[server] Merged rich fields from {_llm_csv.name}")
    if _missing:
        print(f"[server]   ({_missing} CSV rows not matched to any loaded event)")
else:
    print("[server] event_table_llm.csv not found — rich fields (summary/keywords/locations) will be empty")

with open(ROOT / "3.data" / "news_output.json", "r", encoding="utf-8") as f:
    articles_all = json.load(f)
articles_valid = [a for a in articles_all if a["event_id"] != "EVT_NOISE"]

ARTICLES_BY_EVENT: dict[str, list[dict]] = defaultdict(list)
for a in articles_valid:
    ARTICLES_BY_EVENT[a["event_id"]].append(a)

# --- 加载 URL 映射（从 cleaned_data_cn.csv） ---
URL_MAP: dict[str, str] = {}
_url_csv = ROOT / "3.data" / "cleaned_data_cn(2).csv"
if _url_csv.exists():
    with open(_url_csv, "r", encoding="utf-8-sig") as _f:
        for _row in _csv.DictReader(_f):
            _nid = _row.get("news_id", "").strip()
            _u = _row.get("url", "").strip()
            if _nid and _u:
                URL_MAP[_nid] = _u
    print(f"[server] URL map: {len(URL_MAP)} articles with links")

# --- 加载 1.data (传播数据) ---
prop_path = ROOT / "1.data" / "backend_propagation_nodes.json"
PROP_NODES_RAW: list[dict] = []
if prop_path.exists():
    with open(prop_path, "r", encoding="utf-8") as f:
        PROP_NODES_RAW = json.load(f)

# 传播数据事件匹配关键词
PROP_EVENT_KEYWORDS = {
    "EVT_000088": {
        "name": "广西洪涝灾害",
        "keywords": [
            "暴雨", "洪水", "洪涝", "灾害", "救援", "消防", "救火", "水灾",
            "淹", "台风", "气象", "塌陷", "塌方", "泥石流", "山体滑坡",
            "自然灾害", "下沉", "消防员", "救灾",
        ],
    },
    "EVT_000058": {
        "name": "中联油致癌物事件",
        "keywords": [
            "食品", "食安", "致癌", "毒性", "有毒", "安全", "超标",
            "抽检", "监检", "油品", "添加剂", "蔬菜", "农药",
            "食品安全", "卫生", "中毒", "假冒", "消费",
        ],
    },
}

# 为传播事件预过滤节点
PROP_NODES_BY_EVENT: dict[str, list[dict]] = {}
for target_eid, cfg in PROP_EVENT_KEYWORDS.items():
    kws = cfg["keywords"]
    matched_video_ids: set[str] = set()
    for rn in PROP_NODES_RAW:
        if rn.get("node_type") != "video":
            continue
        t = rn.get("title", "") + rn.get("text", "")
        if any(kw in t for kw in kws):
            matched_video_ids.add(rn.get("node_id", rn.get("id", "")))

    seen: set[str] = set()
    event_nodes: list[dict] = []
    for rn in PROP_NODES_RAW:
        nid = rn.get("node_id", rn.get("id", ""))
        pid = rn.get("parent_node_id")
        if nid in matched_video_ids or pid in matched_video_ids or pid in seen:
            event_nodes.append(rn)
            seen.add(nid)
    PROP_NODES_BY_EVENT[target_eid] = event_nodes

# --- 初始化 Pipeline（首次启动时训练模型+缓存） ---
print("[server] Initializing Pipeline...")
pipe = Pipeline(data_interval_hours=6)
print(f"[server] Fake detector model: CV={pipe._train_report.get('cv_mean_accuracy', 0):.1%}")
print(f"[server] Loaded {len(ALL_EVENTS)} events, {len(articles_valid)} articles")
print(f"[server] Propagation data: {len(PROP_NODES_BY_EVENT)} events with B站 data")

# --- 同步预热首页缓存（约 4 分钟，启动后 /api/events 秒回） ---
print("[server] Warming up /api/events cache (114 events, ~4 min)...")
_EVENTS_CACHE = pipe.global_report(
    {k: ALL_EVENTS[k] for k in ALL_EVENTS},
    {k: ARTICLES_BY_EVENT.get(k, []) for k in ALL_EVENTS},
    {k: PROP_NODES_BY_EVENT.get(k, []) for k in ALL_EVENTS if k in PROP_NODES_BY_EVENT},
)
print(f"[server] /api/events cache ready ({len(_EVENTS_CACHE.get('events', []))} events)")

# --- 看板聚合缓存 ---
print("[server] Building dashboard cache...")
_DASHBOARD_CACHE: dict[str, Any] = {}

def _extract_domain(source: str) -> str | None:
    """从来源名提取域名，如 'NewsAPI-36kr.com' → '36kr.com'。无法提取返回 None。"""
    import re
    # 模式: NewsAPI-domain, MediaCloud-domain, 或其他包含域名的前缀
    m = re.search(r'(?:NewsAPI|MediaCloud|Currents)-([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z]{2,})+)', source)
    if m:
        return m.group(1)
    # 兜底：如果 source 本身看起来就是域名（如 '36kr.com'）
    if re.match(r'^[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}$', source):
        return source
    return None

def _build_source_urls(sources: set[str]) -> dict[str, str]:
    """构建 source_name → inferred_url 映射"""
    result: dict[str, str] = {}
    for s in sorted(sources):
        domain = _extract_domain(s)
        if domain:
            result[s] = f"https://{domain}"
    return result

def _build_dashboard_cache():
    global _DASHBOARD_CACHE
    events = _EVENTS_CACHE.get("events", [])
    if not events:
        _DASHBOARD_CACHE = {}
        return

    # ---- KPI 卡片 ----
    total = len(events)
    alerts = _EVENTS_CACHE.get("global_stats", {}).get("alerts", {})
    risk_count = alerts.get("red", 0) + alerts.get("orange", 0)
    avg_heat = round(sum(e.get("current_heat_index", 0) for e in events) / max(total, 1), 1)
    heat_values = [e.get("current_heat_index", 0) for e in events if e.get("current_heat_index")]
    avg_heat = round(sum(heat_values) / max(len(heat_values), 1), 1)

    # ---- 全局情感分布（按 news_count 加权） ----
    tp = tn = tneu = tnc = 0.0
    for e in events:
        sd = e.get("sentiment_distribution", {})
        nc = e.get("news_count", 0) or 1
        tp += sd.get("positive", 0) * nc
        tn += sd.get("negative", 0) * nc
        tneu += sd.get("neutral", 0) * nc
        tnc += nc
    sentiment = {
        "positive": round(tp / max(tnc, 1), 2),
        "negative": round(tn / max(tnc, 1), 2),
        "neutral":  round(tneu / max(tnc, 1), 2),
    }
    dominant = "偏正向" if sentiment["positive"] >= sentiment["negative"] else "偏负向"

    # ---- 全局热度趋势（按天聚合所有事件的 hot_score） ----
    daily_heat: dict[str, float] = {}
    for e in events:
        ts = e.get("timeseries", [])
        if not ts:
            continue
        for p in ts:
            day = str(p.get("time", ""))[:10]
            if not day or len(day) < 8:
                continue
            daily_heat[day] = daily_heat.get(day, 0) + p.get("hot_score", p.get("news_count", 0))
    heat_trend = [
        {"date": k, "value": round(v, 1)}
        for k, v in sorted(daily_heat.items())
    ]
    if len(heat_trend) > 7:
        heat_trend = heat_trend[-7:]

    # ---- 全局关键词 TOP10 ----
    kw_counter: dict[str, int] = {}
    for e in events:
        kws = e.get("keywords", [])
        if isinstance(kws, str):
            try:
                kws = json.loads(kws)
            except Exception:
                kws = []
        for kw in (kws or [])[:5]:
            name = kw.get("name", kw) if isinstance(kw, dict) else str(kw)
            if name:
                kw_counter[name] = kw_counter.get(name, 0) + 1
    top_keywords = sorted(kw_counter.items(), key=lambda x: x[1], reverse=True)[:10]

    # ---- 平台来源数（CSV source_distribution + 文章 source 字段合并）----
    sources: set[str] = set()
    for e in events:
        sd = e.get("source_distribution", "")
        if isinstance(sd, str) and sd.strip():
            try:
                parsed = json.loads(sd)
                for item in parsed:
                    sname = item.get("source", item.get("name", "")) if isinstance(item, dict) else str(item)
                    if sname:
                        sources.add(sname)
            except Exception:
                pass

    # 补充：从真实新闻数据中收集 source（含 NewsAPI/MediaCloud 等可提取域名的来源）
    for _arts in ARTICLES_BY_EVENT.values():
        for _a in _arts[:5]:  # 每个事件取5篇足够
            _asrc = str(_a.get("source", "")).strip()
            if _asrc:
                sources.add(_asrc)
    platform_count = len(sources) or 1

    _DASHBOARD_CACHE = {
        "kpi": {
            "total_events": total,
            "avg_heat": avg_heat,
            "risk_events": risk_count,
            "platform_count": platform_count,
            "dominant_sentiment": dominant,
            "sentiment_positive_pct": round(sentiment["positive"] * 100),
        },
        "sentiment": {
            "positive": round(sentiment["positive"] * 100),
            "negative": round(sentiment["negative"] * 100),
            "neutral":  round(sentiment["neutral"] * 100),
        },
        "heat_trend": heat_trend,
        "keywords": top_keywords,
        # 个人中心概览页用
        "categories": sorted(set(
            e.get("category", "") for e in events if e.get("category", "").strip()
        )),
        "top_keywords": [kw[0] for kw in top_keywords[:8]],
        "source_count": {
            "total": platform_count,
            "active": platform_count,
            "inactive": 0,
        },
        "source_names": sorted(sources),
        "source_urls": _build_source_urls(sources),
    }
    print(f"[server] Dashboard cache ready: {total} events, {len(heat_trend)}-day trend")


_build_dashboard_cache()

# --- 注册 AI 问答路由（管道和数据都就绪后才能创建） ---
from app.routers.ai import create_ai_router
ai_router = create_ai_router(
    all_events=ALL_EVENTS,
    articles_by_event=ARTICLES_BY_EVENT,
    prop_nodes_by_event=PROP_NODES_BY_EVENT,
    prop_event_keywords=PROP_EVENT_KEYWORDS,
    pipe=pipe,
)
app.include_router(ai_router, prefix="/api/ai", tags=["AI 问答"])

# --- 因果分析缓存（预计算，避免每次请求 O(n²) 重算） ---
_CAUSAL_CACHE: dict[str, Any] | None = None
_CAUSAL_BY_EVENT: dict[str, dict] = {}

def _init_causal_cache():
    global _CAUSAL_CACHE, _CAUSAL_BY_EVENT
    if _CAUSAL_CACHE is not None:
        return

    events_qualified: dict[str, list] = {}
    for eid, edata in ALL_EVENTS.items():
        ts = edata.get("timeseries", [])
        nonzero_days = len(set(
            r["time"][:10] for r in ts if r.get("news_count", 0) > 0
        )) if ts else 0
        if nonzero_days >= 3 and edata.get("news_count", 0) >= 5:
            events_qualified[eid] = ts

    analyzer = CrossEventAnalyzer(max_lag=6, significance_level=0.05)
    _CAUSAL_CACHE = analyzer.analyze(events_qualified)
    print(f"[server] Causal cache ready: {_CAUSAL_CACHE.get('significant_pairs', 0)} significant pairs")

    _CAUSAL_BY_EVENT = {}
    for p in _CAUSAL_CACHE.get("pairs", []):
        for key in (p["from_event"], p["to_event"]):
            _CAUSAL_BY_EVENT.setdefault(key, {"granger": [], "te": []})
            _CAUSAL_BY_EVENT[key]["granger"].append(p)
    for p in _CAUSAL_CACHE.get("transfer_entropy_pairs", []):
        for key in (p["from_event"], p["to_event"]):
            _CAUSAL_BY_EVENT.setdefault(key, {"granger": [], "te": []})
            _CAUSAL_BY_EVENT[key]["te"].append(p)

# 预解析关键词集合（用于因果对过滤）
_EVENT_KEYWORD_SETS: dict[str, set[str]] = {}
for _eid, _ev in ALL_EVENTS.items():
    _kw_raw = _ev.get("keywords", _ev.get("event_keywords", ""))
    if isinstance(_kw_raw, str) and _kw_raw.strip().startswith("["):
        try:
            _EVENT_KEYWORD_SETS[_eid] = set(json.loads(_kw_raw))
        except Exception:
            _EVENT_KEYWORD_SETS[_eid] = set()
    else:
        _EVENT_KEYWORD_SETS[_eid] = set()

# 因果缓存改为懒加载——首次请求 /api/cross-event 或 /api/event/{id} 时才计算
# 避免启动时 O(n²) 格兰杰检验卡住 5-10 分钟

print("[server] Ready.")


# =============================================================
# API 0: 看板聚合数据
# =============================================================
@app.get("/api/dashboard")
def get_dashboard() -> dict[str, Any]:
    return _DASHBOARD_CACHE


# ============================================================
# API 1: 事件摘要列表（首页看板）—— 支持分类/关键词/时间筛选
# ============================================================
@app.get("/api/events")
def get_events(
    category: str = "",
    keyword: str = "",
    start_time: str = "",
    end_time: str = "",
) -> dict[str, Any]:
    events = _EVENTS_CACHE.get("events", [])
    if not any([category, keyword, start_time, end_time]):
        return _EVENTS_CACHE

    # 在缓存列表上做内存筛选（不修改原缓存）
    filtered = events
    if category:
        filtered = [e for e in filtered if e.get("category", "") == category]
    if keyword:
        kw = keyword.lower()
        filtered = [
            e for e in filtered
            if kw in (e.get("event_title", "") + e.get("summary", "")).lower()
        ]
    if start_time:
        filtered = [e for e in filtered if str(e.get("time", e.get("event_time", ""))) >= start_time]
    if end_time:
        filtered = [e for e in filtered if str(e.get("time", e.get("event_time", ""))) <= end_time]

    return {
        "events": filtered,
        "cross_event": _EVENTS_CACHE.get("cross_event", {}),
        "global_stats": {
            **_EVENTS_CACHE.get("global_stats", {}),
            "total_events": len(filtered),
            "filtered": True,
        },
    }


# ================================================================
# API 2: 单个事件详情（事件详情页）
# ================================================================
@app.get("/api/event/{event_id}")
def get_event(event_id: str) -> dict[str, Any]:
    if event_id not in ALL_EVENTS:
        return {"error": f"事件 {event_id} 不存在", "available_ids": list(ALL_EVENTS.keys())[:20]}

    edata = ALL_EVENTS[event_id]
    articles = ARTICLES_BY_EVENT.get(event_id)

    # 传播节点
    prop_nodes: list[dict] | None = None
    if event_id in PROP_NODES_BY_EVENT:
        raw = PROP_NODES_BY_EVENT[event_id]
        prop_nodes = []
        for rn in raw:
            nid = rn.get("node_id", rn.get("id", ""))
            children = sum(1 for x in raw if x.get("parent_node_id") == nid)
            prop_nodes.append({
                "node_id":        nid,
                "account_name":   rn.get("account_name", rn.get("user_name", "")),
                "follower_count": rn.get("follower_count", 0),
                "is_verified":    rn.get("is_verified", False),
                "post_time":      rn.get("post_time", rn.get("time", "")),
                "source":         rn.get("source", ""),
                "parent_node_id": rn.get("parent_node_id"),
                "forward_count":  rn.get("forward_count", rn.get("comment_count", children)),
                "title":          rn.get("title", ""),
            })

    # 映射 articles 字段名（3号 → Pipeline 内部）
    mapped_articles = None
    if articles:
        mapped_articles = _map_articles_for_pipeline(articles, event_id)
    report = pipe.event_report(edata, mapped_articles, prop_nodes)

    # ===== 透传原始时序数据（前端需要 timeseries + lifecycle.points 画折线图）=====
    ts = edata.get("timeseries", [])
    report["timeseries"] = ts
    if "lifecycle" in report and isinstance(report["lifecycle"], dict):
        report["lifecycle"]["points"] = [
            {"time": p.get("time", ""), "value": p.get("hot_score", p.get("news_count", 0))}
            for p in ts
        ]
        report["lifecycle"]["heat_trend"] = [
            {"time": p.get("time", ""), "value": p.get("hot_score", 0)}
            for p in ts
        ]
        report["lifecycle"]["news_trend"] = [
            {"time": p.get("time", ""), "value": p.get("news_count", 0)}
            for p in ts
        ]
        report["lifecycle"]["current_avg_count"] = report["lifecycle"].get(
            "current_avg_count",
            round(sum(p.get("news_count", 0) for p in ts[-4:]) / max(len(ts[-4:]), 1), 1) if ts else 0
        )

    # 附加传播事件描述
    if event_id in PROP_EVENT_KEYWORDS:
        report["propagation_description"] = PROP_EVENT_KEYWORDS.get(event_id, {}).get("description", "")
    if prop_nodes is not None and len(prop_nodes) > 0:
        nv = sum(1 for n in prop_nodes if n.get("parent_node_id") is None)
        nc = len(prop_nodes) - nv
        report["propagation_summary"] = f"{len(prop_nodes)}个节点（{nv}个信息源，{nc}条扩散评论）"

    # ===== 前端兼容：补充 event / overview 包装对象 =====
    lifecycle = report.get("lifecycle", {})
    cew = lifecycle.get("critical_early_warning", {})

    # 可信度：若有 article_stats 则用 real_ratio*100，否则默认 85
    article_stats = report.get("article_stats") or {}
    credibility = 85
    if article_stats.get("total", 0) > 0:
        credibility = round((article_stats.get("real", 0) / article_stats["total"]) * 100)

    report["source"] = report.get("source") or edata.get("category", "")
    report["time"] = report.get("event_time", report.get("start_time", ""))
    report["credibility"] = credibility

    report["event"] = {
        "title":                   report.get("event_title", ""),
        "source":                  report["source"],
        "time":                    report["time"],
        "category":                report.get("category", ""),
        "heat":                    lifecycle.get("current_heat_index", report.get("hot_score", 0)),
        "stage":                   lifecycle.get("current_stage", ""),
        "riskLevel":               cew.get("warning_level", "none"),
        "credibility":             credibility,
        "sentiment_distribution":  report.get("sentiment_distribution", {}),
        "news_count":              report.get("news_count", 0),
    }

    report["overview"] = {
        "summary":  report.get("summary", report.get("event_title", "")),
        "time":     report.get("start_time", report.get("event_time", "")),
        "location": report.get("locations", ""),
        "cause":    "",
        "people":   [],
    }

    # ===== 前端字段转换：CSV 原始格式 → 前端组件可消费格式 =====

    # --- overview.people：JSON 字符串数组 → Python 数组 ---
    _persons_raw = edata.get("persons", edata.get("event_persons", ""))
    if isinstance(_persons_raw, str) and _persons_raw.strip():
        try:
            report["overview"]["people"] = json.loads(_persons_raw) if _persons_raw.startswith("[") else [p.strip() for p in _persons_raw.split(",")]
        except Exception:
            report["overview"]["people"] = []

    # --- overview.location：JSON 字符串数组 → 取第一个，多个逗号拼接 ---
    _loc_raw = edata.get("locations", edata.get("event_locations", ""))
    if isinstance(_loc_raw, str) and _loc_raw.strip():
        try:
            _loc_parsed = json.loads(_loc_raw) if _loc_raw.startswith("[") else [_loc_raw]
            report["overview"]["location"] = "、".join(_loc_parsed) if _loc_parsed else ""
        except Exception:
            pass

    # --- keywords：JSON 字符串数组 → [{name, count, color, size, x, y, rotate}] ---
    # 3号 CSV 存的是 ["词1","词2"...] 没有词频，这里给默认 size/x/y/color 做词云布局
    _kw_raw = edata.get("keywords", edata.get("event_keywords", ""))
    _kw_list: list[str] = []
    if isinstance(_kw_raw, str) and _kw_raw.strip():
        try:
            _kw_list = json.loads(_kw_raw) if _kw_raw.startswith("[") else [k.strip() for k in _kw_raw.split(",")]
        except Exception:
            _kw_list = []
    _COLORS = ["#8b5cf6","#3b82f6","#22d3ee","#ec4899","#f472b6","#a78bfa","#38bdf8","#f472b6","#60a5fa","#2dd4bf"]
    import random as _random
    _rng = _random.Random(hash(event_id) & 0x7FFFFFFF)  # 确定性随机，同一事件每次布局一致
    _keyword_items = []
    for _i, _w in enumerate(_kw_list[:10]):
        _size = _rng.randint(14, 34)
        _keyword_items.append({
            "name": _w,
            "count": max(10, 100 - _i * 9),  # 降序词频映射
            "size": _size,
            "color": _COLORS[_i % len(_COLORS)],
            "x": _rng.randint(18, 82),
            "y": _rng.randint(15, 85),
            "rotate": _rng.randint(-8, 8),
        })
    report["keywords"] = _keyword_items

    # --- platform_distribution：CSV 存 [{source, news_num, ratio}] → [{name, value}] ---
    _sd_raw = edata.get("source_distribution", "")
    if isinstance(_sd_raw, str) and _sd_raw.strip():
        try:
            _sd_parsed = json.loads(_sd_raw)
            _platforms = []
            for _item in _sd_parsed:
                _pname = _item.get("source", _item.get("name", _item.get("platform", "")))
                _pval = _item.get("ratio", _item.get("news_num", _item.get("value", 0)))
                if _pname:
                    _platforms.append({"name": _pname, "value": round(float(_pval) * 100, 1) if isinstance(_pval, (int, float)) and _pval <= 1 else float(_pval)})
            report["platform_distribution"] = _platforms
        except Exception:
            report["platform_distribution"] = []
    elif not report.get("platform_distribution"):
        report["platform_distribution"] = []

    # 如果是已知传播事件，附加描述
    if event_id in PROP_EVENT_KEYWORDS:
        report["event"]["source"] = "B站 / " + (report["event"]["source"] or "全网")
        report["propagation_description"] = PROP_EVENT_KEYWORDS[event_id].get("name", "")

    # ===== 跨事件因果数据 =====
    _causal = _CAUSAL_BY_EVENT.get(event_id, {})
    _kw_here = _EVENT_KEYWORD_SETS.get(event_id, set())

    # 过滤：is_significant + 关键词重叠 ≥ 1
    _sig_granger = sorted(
        [p for p in _causal.get("granger", [])
         if p.get("is_significant")
         and len(_kw_here & _EVENT_KEYWORD_SETS.get(p.get("from_event", ""), set())) >= 1
         and len(_kw_here & _EVENT_KEYWORD_SETS.get(p.get("to_event", ""), set())) >= 1],
        key=lambda x: x.get("p_value", 1)
    )[:10]
    _sig_te = sorted(
        [p for p in _causal.get("te", [])
         if p.get("is_significant")
         and len(_kw_here & _EVENT_KEYWORD_SETS.get(p.get("from_event", ""), set())) >= 1
         and len(_kw_here & _EVENT_KEYWORD_SETS.get(p.get("to_event", ""), set())) >= 1],
        key=lambda x: x.get("p_value", 1)
    )[:10]

    report["granger_pairs"] = [
        {
            "source_event": ALL_EVENTS.get(p.get("from_event", ""), {}).get("event_title", p.get("from_event", "")),
            "target_event": ALL_EVENTS.get(p.get("to_event", ""), {}).get("event_title", p.get("to_event", "")),
            "p_value": f"{p.get('p_value', 1):.2e}",
            "lag_hours": p.get("best_lag_hours"),
            "algorithm": "Granger",
        }
        for p in _sig_granger
    ]
    report["transfer_entropy_pairs"] = [
        {
            "source_event": ALL_EVENTS.get(p.get("from_event", ""), {}).get("event_title", p.get("from_event", "")),
            "target_event": ALL_EVENTS.get(p.get("to_event", ""), {}).get("event_title", p.get("to_event", "")),
            "p_value": f"{p.get('p_value', 1):.2e}",
            "te_value": p.get("te_effective"),
            "lag_hours": p.get("best_lag_hours", 1),
            "algorithm": "TransferEntropy",
        }
        for p in _sig_te
    ]
    # lag 折线图：用 -log10(p) 替代 p 值，有视觉起伏
    _all_lag = {}
    for p in _sig_granger:
        raw_lag = p.get("all_lag_pvalues", {})
        for k, v in raw_lag.items():
            lag_num = int(k) if str(k).isdigit() else 0
            if lag_num:
                v_safe = max(float(v), 1e-15)
                _transformed = -math.log10(v_safe)
                if lag_num not in _all_lag or _transformed > _all_lag[lag_num]:
                    _all_lag[lag_num] = round(_transformed, 1)
    report["all_lag_pvalues"] = _all_lag

    return report


# ================================================================
#  API 3: 文章接口（含虚假检测）
# ================================================================

def _map_articles_for_pipeline(articles: list[dict], event_id: str = "") -> list[dict]:
    """3号文章格式 → Pipeline 需要的 article 格式

    从可用数据推导元数据字段，让假新闻检测模型有差分信号：
      - is_verified:    来源是否匹配权威信源白名单
      - follower_count: 根据来源类型估算影响力
      - forward_count:  同事件下其他文章的报道数（→ similar_report_count）
      - hours_since_event: 文章发布时间 − 事件起始时间
    """
    # 同事件文章数（作为多源覆盖信号）
    peer_count = len(ARTICLES_BY_EVENT.get(event_id, [])) if event_id else 1

    # 事件起始时间（用于计算 hours_since_event）
    evt_start_str = ""
    if event_id and event_id in ALL_EVENTS:
        evt_start_str = ALL_EVENTS[event_id].get("start_time", "")
    evt_start = _parse_time_loose(evt_start_str) if evt_start_str else None

    mapped = []
    for a in articles:
        src = str(a.get("source", "")).strip()
        pub_time = str(a.get("publish_time", "")).strip()
        sentiment = str(a.get("sentiment", "")).strip().lower()

        # 元数据推导
        is_verified = _source_is_verified(src)
        followers = _estimate_source_followers(src)
        peer_signal = max(peer_count, 1)  # 至少 1 篇

        # 时间差（小时）
        hours = 24.0
        pub_dt = _parse_time_loose(pub_time)
        if pub_dt and evt_start:
            delta = (pub_dt - evt_start).total_seconds() / 3600.0
            hours = max(0.1, delta) if delta >= 0 else max(0.1, 24.0 + delta)

        # 情感强度：正面低强度、负面高强度
        if sentiment == "positive":
            intensity = 0.3
        elif sentiment == "negative":
            intensity = 0.7
        else:
            intensity = 0.5

        mapped.append({
            "id":                a.get("news_id", ""),
            "article_id":        a.get("news_id", ""),
            "title":             a.get("title", ""),
            "cleaned_text":      a.get("text", ""),
            "source":            src,
            "url":               a.get("url", "") or URL_MAP.get(a.get("news_id", ""), ""),
            "publish_time":      pub_time,
            "sentiment_intensity": intensity,
            "is_verified":       is_verified,
            "follower_count":    followers,
            "forward_count":     peer_signal,
            "hours_since_event": hours,
        })
    return mapped


# ── 信源可信度估算 ──

_SOURCE_WHITELIST_KEYWORDS = frozenset({
    "新华社", "中新网", "人民日报", "央视", "环球", "光明", "中国政府",
    "辟谣", "卫健委", "外交部", "交通运输", "银保监", "央行",
    "澎湃", "新京报", "参考消息", "北京日报", "南方都市", "中国青年",
    "腾讯较真", "科普中国", "丁香医生",
    # 英文/域名级
    "81.cn", "gov.cn", "people.com.cn", "xinhuanet", "cctv",
    "qq.com", "163.com",      # 门户（中等可信）
})

def _source_is_verified(source: str) -> bool:
    """检查来源是否匹配权威信源白名单"""
    for kw in _SOURCE_WHITELIST_KEYWORDS:
        if kw in source:
            return True
    # URL 中的 gov.cn 域
    if ".gov." in source or source.endswith(".gov.cn"):
        return True
    return False

def _estimate_source_followers(source: str) -> int:
    """根据来源名称粗略估算影响力"""
    if any(k in source for k in ("新华社", "人民日报", "央视", "CCTV", "xinhua")):
        return 50_000_000
    if any(k in source for k in ("中新网", "环球", "澎湃", "参考消息")):
        return 20_000_000
    if any(k in source for k in ("辟谣", "卫健委", "外交部", "gov.cn", ".gov.")):
        return 5_000_000
    if any(k in source for k in ("qq.com", "163.com", "新浪", "搜狐", "凤凰")):
        return 10_000_000
    if any(k in source for k in ("B站", "Bilibili", "bilibili")):
        return 5_000  # B站个人账号
    if any(k in source for k in ("抖音", "微博", "小红书")):
        return 2_000
    if any(k in source for k in ("NewsAPI", "Currents", "GoogleNews", "MediaCloud")):
        return 100_000  # 聚合器抓取，原始信源不可知
    return 1_000  # 默认小信源

def _parse_time_loose(time_str: str):
    """宽松时间解析，兼容多种格式"""
    if not time_str:
        return None
    from datetime import datetime
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
                "%Y/%m/%-d %H:%M:%S", "%Y/%-m/%-d %H:%M:%S",
                "%Y/%-m/%-d %H:%M", "%Y/%m/%-d %H:%M:%S"):
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    # 尝试 iso format
    try:
        return datetime.fromisoformat(time_str)
    except Exception:
        return None


def _merge_fake_detection(mapped: list[dict], checked: list[dict], event_id: str) -> list[dict]:
    """把虚假检测结果 merge 回文章数据，输出前端 ready 格式"""
    results = []
    for art, fc in zip(mapped, checked):
        results.append({
            "article_id":       str(art.get("article_id", art.get("id", ""))),
            "event_id":         event_id,
            "title":            art.get("title", ""),
            "cleaned_text":     art.get("cleaned_text", ""),
            "source":           art.get("source", ""),
            "url":              art.get("url", ""),
            "publish_time":     str(art.get("publish_time", "")),
            "verdict":          fc.get("verdict", "待验证"),
            "confidence_score": fc.get("confidence_score", 0),
            "fake_probability": fc.get("fake_probability", 0),
            "risk_factors":     fc.get("risk_factors", []),
            "information_sufficiency": fc.get("information_sufficiency", "一般"),
            "score_breakdown":  fc.get("score_breakdown", {}),
        })
    return results


@app.get("/api/articles")
def get_articles_by_event(event_id: str = "") -> list[dict]:
    """获取某事件全部文章（含虚假检测判定）"""
    articles = ARTICLES_BY_EVENT.get(event_id, [])
    if not articles:
        return []
    mapped = _map_articles_for_pipeline(articles, event_id)
    checked = pipe.article_check(mapped)
    return _merge_fake_detection(mapped, checked, event_id)


@app.get("/api/articles/{article_id}")
def get_article(article_id: str) -> dict:
    """单篇文章详情（含虚假检测判定）"""
    # 遍历所有事件找到该文章
    for evt_id, arts in ARTICLES_BY_EVENT.items():
        for a in arts:
            if str(a.get("news_id", "")) == str(article_id):
                mapped = _map_articles_for_pipeline([a], evt_id)
                checked = pipe.article_check(mapped)
                result = _merge_fake_detection(mapped, checked, evt_id)[0]
                result["article_id"] = str(article_id)
                result["event_id"] = evt_id
                result["sentiment"] = a.get("sentiment", "")
                return result
    return {"error": f"文章 {article_id} 不存在"}


@app.get("/api/cross-event")
def get_cross_event() -> dict[str, Any]:
    _init_causal_cache()
    return _CAUSAL_CACHE


# ================================================================
#  API 5: 健康检查
# ================================================================
@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "events_loaded": len(ALL_EVENTS),
        "articles_loaded": len(articles_valid),
        "propagation_events": list(PROP_NODES_BY_EVENT.keys()),
        "fake_detector_cv": pipe._train_report.get("cv_mean_accuracy", 0),
    }


# ====== 直接运行 ======
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8002, reload=False)

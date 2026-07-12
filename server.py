"""
4号工程师 — API 接口
====================
启动: uvicorn server:app --host 0.0.0.0 --port 8000 --reload
文档: http://localhost:8000/docs
"""

import json
import sys
import csv as _csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 确保导入路径
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

from time_series.pipeline import Pipeline
from time_series.cross_event import CrossEventAnalyzer

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

ROOT = PROJECT  # 数据在 4_time/ 内部

# --- 加载 3.data ---
with open(ROOT / "3.data" / "event_timeseries_result.json", "r", encoding="utf-8") as f:
    events_list = json.load(f)
ALL_EVENTS: dict[str, dict] = {e["event_id"]: e for e in events_list}

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
print("[server] Ready.")


# ============================================================
# API 1: 事件摘要列表（首页看板）
# ============================================================
@app.get("/api/events")
def get_events() -> dict[str, Any]:
    all_event_data: dict[str, dict] = {}
    for eid, edata in ALL_EVENTS.items():
        articles = ARTICLES_BY_EVENT.get(eid)
        prop = PROP_NODES_BY_EVENT.get(eid)
        all_event_data[eid] = edata
        # 不在这里跑全量 Pipeline 避免超时，只跑生命周期
    global_r = pipe.global_report(
        all_event_data,
        {k: ARTICLES_BY_EVENT.get(k, []) for k in ALL_EVENTS},
        {k: PROP_NODES_BY_EVENT.get(k, []) for k in ALL_EVENTS if k in PROP_NODES_BY_EVENT},
    )
    return global_r


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
        mapped_articles = []
        for a in articles:
            mapped_articles.append({
                "id":                a.get("news_id", ""),
                "article_id":        a.get("news_id", ""),
                "title":             a.get("title", ""),
                "cleaned_text":      a.get("text", ""),
                "source":            a.get("source", ""),
                "url":               a.get("url", "") or URL_MAP.get(a.get("news_id", ""), ""),
                "publish_time":      a.get("publish_time", ""),
                "sentiment_intensity": 0.3 if a.get("sentiment") == "positive"
                                     else 0.7 if a.get("sentiment") == "negative"
                                     else 0.5,
                "is_verified":       False,
                "follower_count":    0,
                "forward_count":     0,
                "hours_since_event": 24.0,
            })

    report = pipe.event_report(edata, mapped_articles, prop_nodes)

    # 附加传播事件描述
    if event_id in PROP_EVENT_KEYWORDS:
        report["propagation_description"] = PROP_EVENT_KEYWORDS.get(event_id, {}).get("description", "")
    if prop_nodes is not None and len(prop_nodes) > 0:
        nv = sum(1 for n in prop_nodes if n.get("parent_node_id") is None)
        nc = len(prop_nodes) - nv
        report["propagation_summary"] = f"{len(prop_nodes)}个节点（{nv}个信息源，{nc}条扩散评论）"

    return report


# ================================================================
# API 3: 批量文章判假
# ================================================================
from pydantic import BaseModel

class ArticleInput(BaseModel):
    id: str = ""
    article_id: str = ""
    title: str = ""
    text: str = ""
    cleaned_text: str = ""
    source: str = ""
    publish_time: str = ""
    sentiment_intensity: float = 0.5
    is_verified: bool = False
    follower_count: int = 0
    forward_count: int = 0
    hours_since_event: float = 24.0

class ArticleCheckRequest(BaseModel):
    articles: list[dict[str, Any]] = []

@app.post("/api/articles/check")
def check_articles(req: ArticleCheckRequest) -> list[dict[str, Any]]:
    if not req.articles:
        return []
    return pipe.article_check(req.articles)


# ================================================================
# API 4: 跨事件因果
# ================================================================
@app.get("/api/cross-event")
def get_cross_event() -> dict[str, Any]:
    events_qualified: dict[str, list] = {}
    for eid, edata in ALL_EVENTS.items():
        ts = edata.get("timeseries", [])
        nonzero_days = len(set(
            r["time"][:10] for r in ts if r.get("news_count", 0) > 0
        )) if ts else 0
        if nonzero_days >= 3 and edata.get("news_count", 0) >= 5:
            events_qualified[eid] = ts

    analyzer = CrossEventAnalyzer(max_lag=4, significance_level=0.05)
    return analyzer.analyze(events_qualified)


# ================================================================
# API 5: 健康检查
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
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

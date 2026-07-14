"""
统一报表接口
===========
5号只需调一个函数，拿到一份完整报表 JSON。

使用方式：
    from time_series.pipeline import Pipeline
    pipe = Pipeline()

    # 单事件报表（事件看板 + 趋势图 + 文章可信度）
    report = pipe.event_report(event_data, articles, propagation_nodes)

    # 全局报表（所有事件 + 跨事件因果）
    report = pipe.global_report(all_events, all_articles, all_propagation)

    # 文章列表（逐条判假）
    results = pipe.article_check(articles)
"""

from __future__ import annotations
from typing import Any

from .lifecycle import LifecycleDetector
from .propagation import PropagationTracer
from .fake_detection import get_or_train_model, FakeDetector
from .cross_event import CrossEventAnalyzer


class Pipeline:
    """
    统一报表接口

    初始化时做一次性的模型加载，
    之后每个方法都只返回报表 JSON。
    """

    def __init__(self, data_interval_hours: int = 6):
        """
        data_interval_hours: 数据时间间隔（小时），传给 LifecycleDetector。
                             1=每小时, 6=每6小时, 12=每半天, 24=每天
        """
        self.data_interval_hours = data_interval_hours
        self.lifecycle = LifecycleDetector(data_interval_hours=data_interval_hours)
        self.propagation = PropagationTracer()
        self.cross_event = CrossEventAnalyzer()

        # 虚假检测模型（首次训练 + 缓存）
        model, self._train_report = get_or_train_model()
        self.fake_detector = FakeDetector(model=model)

    @staticmethod
    def _get_latest_time(event_data: dict[str, Any]) -> str:
        """取事件 timeseries 最后一条的时间"""
        ts = event_data.get("timeseries", [])
        if not ts:
            return ""
        return str(ts[-1].get("time", ""))

    # ================================================================
    #  单事件报表
    # ================================================================

    def event_report(
        self,
        event_data: dict[str, Any],
        articles: list[dict[str, Any]] | None = None,
        propagation_nodes: list[dict[str, Any]] | None = None,
        include_fake_check: bool = True,
        include_propagation: bool = True,
    ) -> dict[str, Any]:
        """
        单事件完整报表

        参数：
          event_data: 3号给的事件数据
            {
              "event_id": "EVT_1002",
              "event_title": "南方暴雨事件",
              "category": "社会民生",
              "timeseries": [{"time":"...", "news_count":10, "hot_score":30.5, ...}, ...]
            }
          articles: 该事件的所有文章（2号+3号合并后的格式），每条含 cleaned_text + metadata
          propagation_nodes: 1号给的转发节点列表（可选，没有则跳过传播分析）
          include_fake_check: 是否对文章列表逐条判假
          include_propagation: 是否做传播溯源分析

        返回：
          {
            "event_id": "...",
            "lifecycle":   {阶段+预测+预警+转折点},   // 来自模块1
            "propagation": {传播图+关键节点+反事实},   // 来自模块2 (可选)
            "articles":    [每条的虚假检测结果],        // 来自模块3 (可选)
          }
        """
        report = {
            "event_id": event_data.get("event_id", ""),
            "event_title": event_data.get("event_title", ""),
            "category": event_data.get("category", ""),
            "hot_score": event_data.get("hot_score"),
            "news_count": event_data.get("news_count"),
            "sentiment_distribution": event_data.get("sentiment_distribution", {}),
        }

        # ---- 模块1: 生命周期 ----
        try:
            lifecycle_result = self.lifecycle.detect(event_data)
            report["lifecycle"] = {
                "current_stage": lifecycle_result["current_stage"],
                "stage_probabilities": lifecycle_result["stage_probabilities"],
                "trend_direction": lifecycle_result["trend_direction"],
                "trend_slope": lifecycle_result["trend_slope"],
                "current_heat_index": lifecycle_result["current_heat_index"],
                "composite_index_breakdown": lifecycle_result["composite_index_breakdown"],
                "peak_count": lifecycle_result["peak_count"],
                "peak_time": lifecycle_result["peak_time"],
                "total_duration_hours": lifecycle_result["total_duration_hours"],
                "forecast": lifecycle_result["predicted_next_24h"],
                "turning_points": lifecycle_result["turning_points"],
                "resurgence": lifecycle_result["resurgence"],
                "critical_early_warning": lifecycle_result["critical_early_warning"],
                "diurnal_cycle": lifecycle_result["diurnal_cycle"],
            }
        except Exception as e:
            report["lifecycle"] = {"error": str(e)}

        # ---- 模块2: 传播溯源 ----
        if include_propagation and propagation_nodes:
            try:
                prop_result = self.propagation.analyze(propagation_nodes)
                report["propagation"] = {
                    "source_nodes": prop_result["source_nodes"],
                    "key_nodes": prop_result["key_nodes"],
                    "propagation_depth": prop_result["propagation_depth"],
                    "total_reach": prop_result["total_reach"],
                    "counterfactual": prop_result["counterfactual_analysis"],
                    "graph": prop_result["graph_for_visualization"],
                    "timeline": prop_result["timeline"],
                    "data_quality": prop_result["data_quality"],
                }
            except Exception as e:
                report["propagation"] = {"error": str(e)}
        else:
            report["propagation"] = None

        # ---- 模块3: 虚假检测 ----
        if include_fake_check and articles:
            checked = []
            errors = 0
            for art in articles:
                try:
                    text = art.get("cleaned_text", art.get("text", ""))
                    meta = {
                        "source_verified": art.get("is_verified", False),
                        "source_followers": art.get("follower_count", 0),
                        "similar_report_count": art.get("forward_count", 0),
                        "hours_since_event_start": art.get("hours_since_event", 24.0),
                        "sentiment_intensity": art.get("sentiment_intensity", 0.5),
                    }
                    fc = self.fake_detector.evaluate(text, meta)
                    checked.append({
                        "article_id": art.get("id", art.get("article_id", "")),
                        "event_id": event_data.get("event_id", ""),
                        "title": art.get("title", ""),
                        "cleaned_text": art.get("cleaned_text", art.get("text", "")),
                        "source": art.get("source", ""),
                        "url": art.get("url", ""),
                        "publish_time": str(art.get("publish_time", "")),
                        "verdict": fc["verdict"],
                        "confidence_score": fc["confidence_score"],
                        "fake_probability": fc["fake_probability"],
                        "risk_factors": fc["risk_factors"],
                        "shap_explanation": fc.get("shap_explanation"),
                        "information_sufficiency": fc["information_sufficiency"],
                        "score_breakdown": fc.get("score_breakdown", {}),
                    })
                except Exception:
                    errors += 1
                    checked.append({
                        "article_id": art.get("id", art.get("article_id", "")),
                        "event_id": event_data.get("event_id", ""),
                        "title": art.get("title", ""),
                        "cleaned_text": art.get("cleaned_text", art.get("text", "")),
                        "verdict": "error",
                        "confidence_score": 0,
                        "risk_factors": ["处理失败，跳过了该文章"],
                        "score_breakdown": {},
                    })
            report["articles"] = checked

            fake_count = sum(1 for a in checked if a["verdict"] == "疑似虚假")
            uncertain_count = sum(1 for a in checked if a["verdict"] == "待验证")
            real_count = sum(1 for a in checked if a["verdict"] == "可信")
            report["article_stats"] = {
                "total": len(checked),
                "fake": fake_count,
                "uncertain": uncertain_count,
                "real": real_count,
                "errors": errors,
                "fake_ratio": round(fake_count / max(len(checked), 1), 3),
            }
        else:
            report["articles"] = None
            report["article_stats"] = None

        return report

    # ================================================================
    #  全局报表
    # ================================================================

    def global_report(
        self,
        all_events: dict[str, dict[str, Any]],
        all_articles: dict[str, list[dict[str, Any]]] | None = None,
        all_propagation: dict[str, list[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """
        全局报表（所有事件 + 跨事件因果）

        参数：
          all_events:      {event_id: event_data} 字典
          all_articles:    {event_id: [articles]} 字典（可选，传入则逐事件统计虚假占比）
          all_propagation: {event_id: [propagation_nodes]} 字典（可选，传入则逐事件附传播概况）

        返回：
          {
            "events":         [{event_id, lifecycle, article_stats, propagation}, ...],
            "cross_event":    {pairs, te_pairs, causal_graph},
            "global_stats":   {total_events, alerts, global_article_stats, ...},
          }
        """
        if all_articles is None:
            all_articles = {}
        if all_propagation is None:
            all_propagation = {}

        event_summaries = []
        alerts = {"red": 0, "orange": 0, "yellow": 0}
        global_fake_total = 0
        global_fake_fake = 0

        for eid, event_data in all_events.items():
            lifecycle = self.lifecycle.detect(event_data)
            warning_level = lifecycle["critical_early_warning"]["warning_level"]
            if warning_level in alerts:
                alerts[warning_level] += 1

            summary = {
                "event_id": eid,
                "event_title": event_data.get("event_title", ""),
                "category": event_data.get("category", ""),
                "event_time": self._get_latest_time(event_data),
                "sentiment_distribution": event_data.get("sentiment_distribution", {}),
                "current_stage": lifecycle["current_stage"],
                "current_heat_index": lifecycle["current_heat_index"],
                "trend_direction": lifecycle["trend_direction"],
                "warning_level": warning_level,
                "is_resurgence": lifecycle["resurgence"]["is_resurgence"],
                "total_hours": lifecycle["total_duration_hours"],
                "peak_count": lifecycle["peak_count"],
            }

            # ---- 逐事件文章数量统计（首页不做判假，判假设由 /api/event/{id} 单独处理） ----
            articles = all_articles.get(eid)
            article_count = len(articles) if articles else 0
            summary["article_stats"] = {
                "total": article_count,
                "fake": 0,
                "uncertain": 0,
                "real": article_count,
                "fake_ratio": 0.0,
            }

            # ---- 逐事件传播概况 ----
            prop_nodes = all_propagation.get(eid)
            if prop_nodes:
                try:
                    prop_result = self.propagation.analyze(prop_nodes)
                    summary["propagation"] = {
                        "depth": prop_result["propagation_depth"],
                        "key_node_count": len(prop_result["key_nodes"]),
                        "source_count": len(prop_result["source_nodes"]),
                        "total_reach": prop_result["total_reach"]["estimated_unique_reach"],
                        "data_quality": prop_result["data_quality"],
                    }
                except Exception:
                    summary["propagation"] = None
            else:
                summary["propagation"] = None

            # ===== 前端兼容别名（不改原有字段，只追加前端取值链能命中名字） =====
            summary["hot_score"] = summary["current_heat_index"]
            summary["heat"] = summary["current_heat_index"]
            summary["heat_index"] = summary["current_heat_index"]
            summary["news_count"] = article_count
            summary["news"] = article_count
            summary["timeseries"] = event_data.get("timeseries", [])
            summary["summary"] = summary["event_title"]
            summary["source"] = ""
            summary["time"] = summary["event_time"]

            event_summaries.append(summary)

        # 按热度排序
        event_summaries.sort(key=lambda e: e["current_heat_index"], reverse=True)

        # 跨事件因果由独立接口 /api/cross-event 提供，global_report 不做 O(n²) 因果计算
        cross_result = {"pairs": [], "transfer_entropy_pairs": [], "causal_graph": {},
                        "significant_pairs": 0, "significant_te_pairs": 0, "summary": "跨事件因果请调用 /api/cross-event"}

        return {
            "events": event_summaries,
            "cross_event": {
                "granger_pairs": cross_result["pairs"],
                "transfer_entropy_pairs": cross_result["transfer_entropy_pairs"],
                "causal_graph": cross_result["causal_graph"],
                "summary": cross_result["summary"],
            },
            "global_stats": {
                "total_events": len(event_summaries),
                "alerts": alerts,
                "top_event": event_summaries[0] if event_summaries else None,
                "global_article_stats": {
                    "total": global_fake_total,
                    "fake": global_fake_fake,
                    "fake_ratio": round(global_fake_fake / max(global_fake_total, 1), 3),
                } if global_fake_total > 0 else None,
                "fake_detector_info": {
                    "data_source": self._train_report.get("data_source", self._train_report.get("source", "")),
                    "cv_accuracy": self._train_report.get("cv_mean_accuracy", 0),
                },
            },
        }

    # ================================================================
    #  批量文章检测
    # ================================================================

    def article_check(
        self, articles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        批量判假

        参数：
          articles: [{cleaned_text/text, is_verified, follower_count, ...}, ...]

        返回：
          [{article_id, title, verdict, confidence, risk_factors, shap}, ...]
        """
        results = []
        for art in articles:
            text = art.get("cleaned_text", art.get("text", ""))
            meta = {
                "source_verified": art.get("is_verified", False),
                "source_followers": art.get("follower_count", 0),
                "similar_report_count": art.get("forward_count", 0),
                "hours_since_event_start": art.get("hours_since_event", 24.0),
                "sentiment_intensity": art.get("sentiment_intensity", 0.5),
            }
            fc = self.fake_detector.evaluate(text, meta)
            results.append({
                "article_id": art.get("id", art.get("article_id", "")),
                "title": art.get("title", ""),
                "verdict": fc["verdict"],
                "confidence_score": fc["confidence_score"],
                "fake_probability": fc["fake_probability"],
                "risk_factors": fc["risk_factors"],
                "shap_explanation": fc.get("shap_explanation"),
                "score_breakdown": fc.get("score_breakdown", {}),
            })
        return results


# ====== 自测 ======
if __name__ == "__main__":
    from .utils.mock_data import generate_mock_events, generate_mock_propagation_data

    print("=" * 60)
    print("统一报表接口 — 自测")
    print("=" * 60)

    pipe = Pipeline()

    # 1. 单事件报表
    events = generate_mock_events(num_events=1)
    event_data = events[0]
    propagation_nodes = generate_mock_propagation_data()

    # 构造假文章
    articles = [
        {"id": "1", "title": "官方通告", "cleaned_text": "卫健委通报:今日新增3例,详情见 http://health.gov.cn",
         "is_verified": True, "follower_count": 2000000, "forward_count": 25, "hours_since_event": 8.0, "sentiment_intensity": 0.2, "source": "央视新闻", "publish_time": "2026-07-06 10:00"},
        {"id": "2", "title": "网友爆料", "cleaned_text": "听说隔壁小区被封了,等通知吧",
         "is_verified": False, "follower_count": 500, "forward_count": 2, "hours_since_event": 2.0, "sentiment_intensity": 0.5, "source": "微博", "publish_time": "2026-07-06 14:00"},
        {"id": "3", "title": "可疑消息", "cleaned_text": "震惊!!绝密内幕!!紧急扩散!!马上删!!",
         "is_verified": False, "follower_count": 20, "forward_count": 0, "hours_since_event": 0.5, "sentiment_intensity": 0.95, "source": "未知", "publish_time": "2026-07-06 15:00"},
    ]

    report = pipe.event_report(event_data, articles, propagation_nodes)

    print(f"\n[事件报表] {report['event_title']}")
    print(f"  阶段: {report['lifecycle']['current_stage']}")
    print(f"  热度: {report['lifecycle']['current_heat_index']}")
    print(f"  预警: {report['lifecycle']['critical_early_warning']['warning_level']}")
    print(f"  预测: {len(report['lifecycle']['forecast'])}小时")
    print(f"  传播: {report['propagation']['data_quality']}")
    print(f"  文章: {report['article_stats']}")
    print(f"  文章判定:")
    for a in report["articles"]:
        icon = {"可信": "[OK]", "待验证": "[?]", "疑似虚假": "[!!]"}
        print(f"    {icon[a['verdict']]} {a['title']} | {a['verdict']} ({a['confidence_score']:.0f}%)")
        if a.get("shap_explanation"):
            print(f"      SHAP: {a['shap_explanation']['summary']}")

    # 2. 全局报表（需要至少 2 个事件）
    from .utils.mock_data import generate_mock_events
    all_evts = generate_mock_events(num_events=3)
    all_events = {}
    for evt in all_evts:
        all_events[evt["event_id"]] = evt
    global_r = pipe.global_report(all_events)

    print(f"\n[全局报表]")
    print(f"  事件数: {global_r['global_stats']['total_events']}")
    print(f"  预警分布: {global_r['global_stats']['alerts']}")
    print(f"  交叉因果: {global_r['cross_event']['summary']}")
    print(f"  虚假检测模型: {global_r['global_stats']['fake_detector_info']}")

    print(f"\n[完成] 5号只需 import Pipeline, 调两个方法即可。")

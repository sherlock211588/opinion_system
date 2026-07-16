# -*- coding: utf-8 -*-
"""
时序算法模块 -- 完整演示
======================
4号工程师（时序算法）的全部功能演示

运行方式：
    python demo.py

这个脚本不需要任何外部依赖，纯 Python 标准库即可运行。
"""

from time_series.utils.mock_data import generate_mock_events, generate_mock_propagation_data
from time_series.lifecycle import LifecycleDetector
from time_series.propagation import PropagationTracer
from time_series.fake_detection import FakeDetector


def demo_lifecycle():
    """演示1：舆情生命周期检测"""
    print("=" * 70)
    print("   [演示1] 舆情生命周期检测")
    print("=" * 70)

    events = generate_mock_events(num_events=3)
    detector = LifecycleDetector()

    event_names = ["事件A (公共卫生)", "事件B (科技争议)", "事件C (明星八卦)"]

    for i, evt in enumerate(events):
        records = evt["timeseries"]

        # 模拟三个时刻的检测：早期(第15小时)、中期(第35小时)、后期(第60小时)
        snapshots = {
            "事件爆发15小时后": records[:15],
            "事件爆发35小时后": records[:35],
            "事件爆发60小时后": records[:60],
        }

        print(f"\n{'─' * 50}")
        print(f"  {event_names[i]}: {evt['event_title']}")
        print(f"{'─' * 50}")

        for label, snapshot in snapshots.items():
            temp_event = {"event_id": evt["event_id"], "timeseries": snapshot}
            r = detector.detect(temp_event)
            print(f"  [{label}]  ->  阶段: {r['current_stage']}  "
                  f"趋势: {r['trend_direction']}  "
                  f"热度: {r['current_avg_count']:.0f}篇/时  "
                  f"斜率: {r['trend_slope']:+.2f}")

    print()


def demo_propagation():
    """演示2：传播路径溯源"""
    print("=" * 70)
    print("   [演示2] 事件传播路径溯源")
    print("=" * 70)

    nodes = generate_mock_propagation_data()
    tracer = PropagationTracer()
    result = tracer.analyze(nodes)

    # 传播图结构
    print("\n  传播图结构 (networkx DiGraph):")
    gs = result['propagation_graph']
    print(f"  节点: {gs['node_count']}, 边: {gs['edge_count']}, DAG: {gs['is_dag']}")
    print(f"  密度: {gs['density']}, 源头数: {gs['source_count']}, 叶子数: {gs['sink_count']}")
    print(f"  最长传播链: {result['propagation_depth']} 层")

    # 源头
    srcs = result['source_nodes']
    for s in srcs:
        print(f"  源头: [{s['node_id']}] {s['account_name']} ({s.get('source', '')})")

    print(f"\n  关键节点 (PageRank+介数+出度):")
    for kn in result['key_nodes'][:5]:
        gs2 = kn['graph_scores']
        print(f"    [{kn['role']}] {kn['account_name']} 粉丝:{kn['follower_count']:,} "
              f"PR={gs2['pagerank']:.2f} BC={gs2['betweenness']:.2f}")

    reach = result['total_reach']
    print(f"\n  触达（去重后）: {reach['estimated_unique_reach']:,} 人次")
    print(f"  （旧方法: {reach['breakdown']['naive_sum']:,}，去重比: {reach['breakdown']['dedup_ratio']}）")
    print(f"  数据质量: {result.get('data_quality', {})}")

    print("\n  给前端的可视化数据预览（JSON格式）：")
    viz = result["graph_for_visualization"]
    print(f"    nodes: [{viz['nodes'][0]['name']}, {viz['nodes'][1]['name']}, ...] 共{len(viz['nodes'])}个")
    print(f"    links: [({viz['links'][0]['source']}->{viz['links'][0]['target']}), ...] 共{len(viz['links'])}条")

    print()


def demo_fake_detection():
    """演示3：虚假文本检测"""
    print("=" * 70)
    print("   [演示3] 虚假文本检测")
    print("=" * 70)

    # v3.0: TF-IDF 文本特征 + 元数据特征联合训练（首次训练后缓存）
    try:
        from time_series.fake_detection import get_or_train_model, FakeDetector

        model, report = get_or_train_model()
        detector = FakeDetector(model=model)

        is_cached = report.get("source") == "缓存加载"
        if is_cached:
            print(f"  [v3.0 模型缓存加载] 从 {report['path']} 加载已训练模型")
            if report.get("cv_mean_accuracy"):
                print(f"  交叉验证准确率: {report['cv_mean_accuracy']:.1%} "
                      f"({report.get('n_samples', '?')}条CED标注微博)")
            if report.get("feature_dimensions"):
                dims = report["feature_dimensions"]
                print(f"  TF-IDF文本特征: {dims['tfidf_text_features']}维  "
                      f"元数据特征: {dims['metadata_features']}维")
            if report.get("top_tfidf_text_features"):
                print(f"  最强虚假文本模式: {list(report['top_tfidf_text_features'].keys())[:5]}")
        else:
            print(f"  [v3.0 TF-IDF+元数据联合训练] CED数据集, "
                  f"CV准确率={report['cv_mean_accuracy']:.1%}")
            print(f"  TF-IDF文本特征: {report['feature_dimensions']['tfidf_text_features']}维")
            print(f"  元数据特征: {report['feature_dimensions']['metadata_features']}维")
            print(f"  最强虚假文本模式: {list(report['top_tfidf_text_features'].keys())[:5]}")
    except Exception:
        detector = FakeDetector(auto_train=True)
        print("  [回退模式] 纯数值特征训练")

    test_cases = [
        {
            "label": "案例1：官方通告",
            "text": "据市卫健委通报，今日新增确诊病例3例，均为境外输入，已闭环转运至定点医院。",
            "metadata": {
                "source_verified": True,
                "source_followers": 2000000,
                "sentiment_intensity": 0.2,
                "similar_report_count": 25,
                "hours_since_event_start": 8,
            },
        },
        {
            "label": "案例2：网友爆料",
            "text": "听说隔壁小区被封了，具体情况不清楚，等官方通知吧。",
            "metadata": {
                "source_verified": False,
                "source_followers": 500,
                "sentiment_intensity": 0.5,
                "similar_report_count": 2,
                "hours_since_event_start": 2,
            },
        },
        {
            "label": "案例3：可疑消息",
            "text": "震惊！！绝密文件泄露！！紧急扩散！！马上删！！速看！！",
            "metadata": {
                "source_verified": False,
                "source_followers": 20,
                "sentiment_intensity": 0.95,
                "similar_report_count": 0,
                "hours_since_event_start": 0.5,
            },
        },
    ]

    for case in test_cases:
        r = detector.evaluate(case["text"], case["metadata"])
        verdict_mark = {"可信": "[可信]", "存疑": "[?存疑]", "疑似虚假": "[!疑似虚假]"}
        print(f"\n  {case['label']}")
        print(f"    结果: {verdict_mark.get(r['verdict'], '?')} {r['verdict']} "
              f"(可信度 {r['confidence_score']:.0f}%)")
        print(f"    各维度: {r['score_breakdown']}")
        if r["risk_factors"]:
            for rf in r["risk_factors"]:
                print(f"      ! {rf}")

    print()


def demo_data_format():
    """演示4：和队友的数据接口约定"""
    print("=" * 70)
    print("   [演示4] 你需要的输入数据 & 你的输出数据")
    print("=" * 70)

    print("""
  +-----------------------------------------------------------+
  |              你需要从队友那里拿到的数据                       |
  +-----------------------------------------------------------+
  |                                                           |
  |  1号爬虫 -> 你:                                            |
  |    * 文章发布时间（精确到秒）        <- 没有这个什么都做不了   |
  |    * 转发关系链（谁转了谁）          <- 传播溯源的核心       |
  |    * 账号粉丝数                      <- 判断"关键节点"      |
  |    * 来源平台（微博/知乎/头条等）     <- 平台分布分析        |
  |    * 文章URL / 唯一ID                                    |
  |                                                           |
  |  2号清洗 -> 你:                                            |
  |    * 标准化时间字段（统一格式）                              |
  |    * 清洗后的纯文本                   <- 虚假检测用         |
  |    * TF-IDF / 词向量                 <- 虚假检测特征       |
  |                                                           |
  |  3号NLP -> 你:                                             |
  |    * 事件聚合结果（哪些文章是同一件事）  <- 按事件建模       |
  |    * 情感标签 + 强度                 <- 虚假检测特征        |
  |    * 事件主题分类                     <- 分类分析           |
  |                                                           |
  +-----------------------------------------------------------+
  |              你输出给 5号（前端可视化）的数据                  |
  +-----------------------------------------------------------+
  |                                                           |
  |  生命周期检测 -> 5号:                                       |
  |    {                                                      |
  |      "event_id": "EVT_001",                                |
  |      "current_stage": "高潮期",                             |
  |      "trend_direction": "下降",                            |
  |      "predicted_next_24h": [{...}, ...],   <- 画折线图     |
  |      "turning_points": [{...}, ...]        <- 标注节点     |
  |    }                                                      |
  |                                                           |
  |  传播溯源 -> 5号:                                           |
  |    {                                                      |
  |      "graph_for_visualization": {                          |
  |        "nodes": [...],                  <- 力导向图节点    |
  |        "links": [...],                  <- 连线            |
  |        "categories": [...]              <- 颜色分类        |
  |      }                                                     |
  |    }                                                       |
  |                                                            |
  |  虚假检测 -> 5号:                                            |
  |    {                                                       |
  |      "confidence_score": 85.0,                              |
  |      "verdict": "可信"                                      |
  |    }                                                       |
  |                                                            |
  +------------------------------------------------------------+
""")


def demo_pipeline():
    """演示5：统一报表接口 — 5号只需调这一个类"""
    from time_series.pipeline import Pipeline
    from time_series.utils.mock_data import generate_mock_events, generate_mock_propagation_data

    print("=" * 70)
    print("   [演示5] 统一报表接口 — 5号只需要 import Pipeline")
    print("=" * 70)

    pipe = Pipeline()

    # ---- 准备数据 ----
    events = generate_mock_events(num_events=3)
    all_events = {e["event_id"]: e for e in events}
    event_data = events[0]

    propagation_nodes = generate_mock_propagation_data()

    articles = [
        {"id": "1", "title": "官方通报", "cleaned_text": "卫健委通报:今日新增3例,详情见 http://health.gov.cn",
         "is_verified": True, "follower_count": 2000000, "forward_count": 25,
         "hours_since_event": 8.0, "sentiment_intensity": 0.2,
         "source": "央视新闻", "publish_time": "2026-07-06 10:00"},
        {"id": "2", "title": "网友爆料", "cleaned_text": "听说隔壁小区被封了,等通知吧",
         "is_verified": False, "follower_count": 500, "forward_count": 2,
         "hours_since_event": 2.0, "sentiment_intensity": 0.5,
         "source": "微博", "publish_time": "2026-07-06 14:00"},
        {"id": "3", "title": "可疑消息", "cleaned_text": "震惊!!绝密内幕!!紧急扩散!!马上删!!",
         "is_verified": False, "follower_count": 20, "forward_count": 0,
         "hours_since_event": 0.5, "sentiment_intensity": 0.95,
         "source": "未知", "publish_time": "2026-07-06 15:00"},
    ]
    all_articles = {event_data["event_id"]: articles}
    all_propagation = {event_data["event_id"]: propagation_nodes}

    # ================================================================
    #  接口1: 单事件报表 → 对应前端「事件详情页」
    # ================================================================
    print("\n" + "─" * 50)
    print("  接口1: pipe.event_report(event_data, articles, propagation_nodes)")
    print("  用途: 前端「事件详情页」全部数据\n")
    report = pipe.event_report(event_data, articles, propagation_nodes)

    print(f"  事件: {report['event_title']}")
    print(f"  情感: {report['sentiment_distribution']}")
    print(f"  阶段: {report['lifecycle']['current_stage']}")
    print(f"  热度: {report['lifecycle']['current_heat_index']}/100")
    print(f"  趋势: {report['lifecycle']['trend_direction']}")
    print(f"  预警: {report['lifecycle']['critical_early_warning']['warning_level']}")
    print(f"  预测: {len(report['lifecycle']['forecast'])}小时 → 前端折线图")
    print(f"  转折点: {len(report['lifecycle']['turning_points'])}个 → 前端标注节点")
    print(f"  二次爆发: {report['lifecycle']['resurgence']['is_resurgence']}")
    print(f"  传播: {report['propagation']['data_quality']}")
    print(f"  传播图: {len(report['propagation']['graph']['nodes'])}节点, "
          f"{len(report['propagation']['graph']['links'])}条边 → 前端力导向图")
    print(f"  文章统计: {report['article_stats']}")

    print("\n  文章逐条判假:")
    for a in report["articles"]:
        icon = {"可信": "[OK]", "待验证": "[?]", "疑似虚假": "[!!]"}
        print(f"    {icon[a['verdict']]} {a['title']} | {a['verdict']} "
              f"(可信度{a['confidence_score']}%)")
        if a.get("shap_explanation"):
            print(f"      SHAP: {a['shap_explanation']['summary']}")

    # ================================================================
    #  接口2: 全局报表 → 对应前端「热点看板首页」
    # ================================================================
    print("\n" + "─" * 50)
    print("  接口2: pipe.global_report(all_events, all_articles, all_propagation)")
    print("  用途: 前端「热点看板首页」全部数据\n")
    global_r = pipe.global_report(all_events, all_articles, all_propagation)

    print(f"  事件数: {global_r['global_stats']['total_events']}")
    print(f"  预警分布: {global_r['global_stats']['alerts']}")
    if global_r['global_stats'].get('global_article_stats'):
        gas = global_r['global_stats']['global_article_stats']
        print(f"  全局文章: {gas['total']}篇, 疑似虚假{gas['fake']}篇 ({gas['fake_ratio']:.1%})")
    print(f"\n  ---- 热点榜单（按热度排序）----")
    for i, evt in enumerate(global_r["events"]):
        print(f"  {i+1}. [{evt['current_stage']}] {evt['event_title']}"
              f"  热度:{evt['current_heat_index']:.0f}"
              f"  趋势:{evt['trend_direction']}"
              f"  预警:{evt['warning_level']}")
        if evt.get("sentiment_distribution"):
            sd = evt["sentiment_distribution"]
            print(f"      正面{sd['positive']:.1%} 负面{sd['negative']:.1%} 中性{sd['neutral']:.1%}")
        if evt.get("article_stats"):
            print(f"      虚假文章: {evt['article_stats']['fake']}/{evt['article_stats']['total']}")
        if evt.get("propagation"):
            print(f"      传播: 深{evt['propagation']['depth']}层, "
                  f"触达{evt['propagation']['total_reach']:,}人次")

    print(f"\n  ---- 跨事件因果 ----")
    print(f"  {global_r['cross_event']['summary']}")
    for p in global_r["cross_event"]["granger_pairs"][:3]:
        sig = " *** 显著 ***" if p["is_significant"] else ""
        print(f"    {p['from_title']} → {p['to_title']}{sig}  "
              f"滞后{p['best_lag_hours']}h p={p['p_value']:.4f}")

    # ================================================================
    #  接口3: 批量文章判假
    # ================================================================
    print("\n" + "─" * 50)
    print("  接口3: pipe.article_check(articles)")
    print("  用途: 前端「文章列表页」逐条判假\n")
    results = pipe.article_check(articles)
    for r in results:
        print(f"  {r['title']} → {r['verdict']} ({r['confidence_score']}%)")

    print("\n  [OK] 5号只需记住三行代码:")
    print("    pipe = Pipeline()")
    print("    pipe.event_report(event_data, articles, propagation_nodes)")
    print("    pipe.global_report(all_events, all_articles, all_propagation)")
    print()


if __name__ == "__main__":
    print()
    print("+" + "=" * 62 + "+")
    print("|    网络舆情事件智能分析系统 -- 时序算法模块演示            |")
    print("|    4号工程师：舆情生命周期 + 传播溯源 + 虚假检测          |")
    print("+" + "=" * 62 + "+")

    demo_lifecycle()
    demo_propagation()
    demo_fake_detection()
    demo_pipeline()
    demo_data_format()

    print("=" * 70)
    print("  [OK] 全部演示完成！")
    print("  [>>] 5号只需 import Pipeline，调 event_report / global_report")
    print("=" * 70)
    print()

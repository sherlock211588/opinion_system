"""
用3号真实数据运行全部模块
========================
读取 3.data/event_timeseries_result.json（114个事件，6小时间隔），
运行模块1（生命周期）和模块4（跨事件因果），输出结果摘要。

使用方式：
    cd 4_time
    python run_real_data.py
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

# 确保项目路径
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

from time_series.pipeline import Pipeline
from time_series.cross_event import CrossEventAnalyzer
from time_series.fake_detection import get_or_train_model, FakeDetector


def load_3data(json_path: str) -> dict[str, dict]:
    """加载3号事件数据"""
    with open(json_path, "r", encoding="utf-8") as f:
        events_list = json.load(f)
    return {e["event_id"]: e for e in events_list}


def print_separator(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def run_lifecycle(events: dict):
    """模块1: 所有事件的生命周期检测"""
    print_separator("模块1: 舆情生命周期预测")

    pipe = Pipeline(data_interval_hours=6)
    results = []
    alerts = {"red": 0, "orange": 0, "yellow": 0, "none": 0}

    for eid, event_data in events.items():
        try:
            r = pipe.lifecycle.detect(event_data)
        except Exception as e:
            results.append({"event_id": eid, "error": str(e)})
            continue

        dq = r.get("data_quality", {})
        stage = r["current_stage"]
        heat = r["current_heat_index"]
        trend = r["trend_direction"]
        warning = r["critical_early_warning"]["warning_level"]
        alerts[warning] = alerts.get(warning, 0) + 1
        resurgence = r["resurgence"]["is_resurgence"]
        n_eff = dq.get("effective_nonzero_points", 0)

        results.append({
            "event_id": eid,
            "title": event_data.get("event_title", "")[:50],
            "category": event_data.get("category", ""),
            "stage": stage,
            "heat": heat,
            "trend": trend,
            "warning": warning,
            "resurgence": resurgence,
            "effective_points": n_eff,
            "total_points": dq.get("trimmed_points", 0),
            "total_news": event_data.get("news_count", 0),
        })

    # 按热度排序
    results.sort(key=lambda x: x["heat"], reverse=True)

    print(f"\n  {'事件ID':<14} {'分类':<10} {'阶段':<6} {'热度':>5} {'趋势':<4} {'预警':<6} {'有效点':>5} {'总报道':>5}  标题")
    print(f"  {'-'*14} {'-'*10} {'-'*6} {'-'*5} {'-'*4} {'-'*6} {'-'*5} {'-'*5}  {'-'*30}")
    for r in results:
        heat_str = f"{r['heat']:.0f}" if r["heat"] else "  -"
        resurgence_mark = " ★" if r["resurgence"] else ""
        print(f"  {r['event_id']:<14} {r['category']:<10} {r['stage']+resurgence_mark:<6} {heat_str:>5} {r['trend']:<4} {r['warning']:<6} {r['effective_points']:>5} {r['total_news']:>5}   {r['title'][:40]}")

    print(f"\n  事件总数: {len(results)}")
    print(f"  预警分布: RED={alerts['red']}  ORANGE={alerts['orange']}  YELLOW={alerts['yellow']}  NONE={alerts['none']}")
    print(f"  有效数据点分布: min={min(r['effective_points'] for r in results)}  max={max(r['effective_points'] for r in results)}  avg={sum(r['effective_points'] for r in results)//max(len(results),1)}")

    return results


def run_cross_event(events: dict):
    """模块4: 跨事件因果分析"""
    print_separator("模块4: 跨事件格兰杰因果 + 符号化传递熵")

    analyzer = CrossEventAnalyzer(max_lag=4, significance_level=0.05)

    # 只取时间跨度>=3天的事件（至少12个非零点才能跑因果）
    events_qualified = {}
    for eid, edata in events.items():
        ts = edata.get("timeseries", [])
        nonzero_days = len(set(r["time"][:10] for r in ts if r.get("news_count", 0) > 0)) if ts else 0
        total_news = edata.get("news_count", 0)
        if nonzero_days >= 3 and total_news >= 5:
            events_qualified[eid] = ts

    print(f"\n  符合条件的事件: {len(events_qualified)}/{len(events)} (时间跨度>=3天, 总报道>=5)")

    if len(events_qualified) < 2:
        print("  事件数不足，跳过跨事件因果分析")
        return

    result = analyzer.analyze(events_qualified)

    print(f"\n  {result['summary']}")
    print(f"  方法: {result['method']}")

    # 格兰杰因果
    if result["pairs"]:
        sig_pairs = [p for p in result["pairs"] if p["is_significant"]]
        print(f"\n  ── 格兰杰因果（线性）── 共{len(result['pairs'])}对，显著{len(sig_pairs)}对")
        for p in sig_pairs[:10]:
            print(f"    {p['from_title'][:30]} → {p['to_title'][:30]}")
            print(f"      滞后 {p['best_lag_hours']}步({p['best_lag_hours'] * 6}h)  p={p['p_value']:.4f}")

    # 传递熵
    if result.get("transfer_entropy_pairs"):
        te_sig = [p for p in result["transfer_entropy_pairs"] if p["is_significant"]]
        print(f"\n  ── 符号化传递熵（非线性）── 共{len(result['transfer_entropy_pairs'])}对，显著{len(te_sig)}对")
        for p in te_sig[:5]:
            print(f"    {p['from_title'][:30]} → {p['to_title'][:30]}")
            print(f"      TE={p['te_effective']:.4f}  p={p['p_value']:.4f}")


def run_fake_detection():
    """模块3: 虚假检测（用2号 advanced_analysis(3).csv）"""
    print_separator("模块3: 虚假文本检测")

    # 尝试加载2号数据
    data_dir = PROJECT.parent / "2.data"
    csv_path = data_dir / "advanced_analysis(3).csv"

    if not csv_path.exists():
        print(f"  [跳过] 未找到 {csv_path}")
        return

    import csv
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  加载 {len(rows)} 条清洗文本")

    # 加载模型
    model, report = get_or_train_model()
    detector = FakeDetector(model=model)
    is_cached = report.get("source") == "缓存加载"
    print(f"  模型: {'缓存加载' if is_cached else '新训练'} | CV准确率: {report.get('cv_mean_accuracy', 0):.1%}")

    # 批量判假
    stats = {"可信": 0, "待验证": 0, "疑似虚假": 0, "error": 0}
    sample_results = []

    for i, row in enumerate(rows):
        text = row.get("cleaned_body", row.get("text", ""))
        if not text or len(text) < 10:
            stats["error"] += 1
            continue

        meta = {
            "source_verified": False,       # 2号数据无此字段
            "source_followers": 0,
            "similar_report_count": 0,
            "hours_since_event_start": 24.0,
            "sentiment_intensity": float(row.get("sentiment_polarity", 0.5)),
        }

        r = detector.evaluate(text, meta)
        verdict = r["verdict"]
        stats[verdict] = stats.get(verdict, 0) + 1

        # 保留一些样例
        if len(sample_results) < 8:
            sample_results.append({
                "idx": i,
                "text_preview": text[:60],
                "verdict": verdict,
                "confidence": r["confidence_score"],
                "fake_prob": r["fake_probability"],
                "sentiment": row.get("sentiment_label", "?"),
                "risk": r.get("risk_factors", [])[:2],
            })

    total = sum(stats.values())
    print(f"\n  判定结果分布 ({total}条):")
    for verdict, count in sorted(stats.items()):
        bar = "█" * (count * 40 // max(total, 1))
        print(f"    {verdict:<8} {count:>5}条 ({count/total*100:5.1f}%) {bar}")

    print(f"\n  样例:")
    for s in sample_results:
        icon = {"可信": "[OK]", "待验证": "[?]", "疑似虚假": "[!!]"}
        print(f"    {icon.get(s['verdict'],'[?]')} [{s['verdict']}] 可信{s['confidence']:.0f}% | 情感:{s['sentiment']} | {s['text_preview'][:50]}...")


def run_one_event_detail(events: dict, event_id: str = "EVT_000001"):
    """单个事件完整报表"""
    print_separator(f"事件详情示例: {event_id}")

    if event_id not in events:
        print(f"  [错误] 事件 {event_id} 不存在")
        return

    edata = events[event_id]
    pipe = Pipeline(data_interval_hours=6)
    r = pipe.lifecycle.detect(edata)

    print(f"\n  标题: {edata['event_title'][:60]}")
    print(f"  分类: {edata['category']}")
    print(f"  总报道: {edata['news_count']} 篇  热点分: {edata['hot_score']}")
    print(f"  情感: 正面{edata['sentiment_distribution']['positive']:.0%} "
          f"负面{edata['sentiment_distribution']['negative']:.0%} "
          f"中性{edata['sentiment_distribution']['neutral']:.0%}")

    dq = r["data_quality"]
    print(f"\n  数据质量: 原始{dq['original_points']}点 → 裁剪后{dq['trimmed_points']}点 "
          f"→ 有效非零{dq['effective_nonzero_points']}点 | 间隔{dq['data_interval_hours']}h")

    print(f"\n  ── 阶段判定 ──")
    print(f"  当前阶段: {r['current_stage']}")
    probs = r["stage_probabilities"]
    print(f"  阶段概率: 潜伏期{probs.get('潜伏期',0):.0%} | 成长期{probs.get('成长期',0):.0%} | 高潮期{probs.get('高潮期',0):.0%} | 衰退期{probs.get('衰退期',0):.0%}")
    print(f"  综合热度: {r['current_heat_index']:.0f}/100  趋势: {r['trend_direction']} (斜率{r['trend_slope']:+.2f})")
    print(f"  四维拆解: 报道量{r['composite_index_breakdown'].get('volume',0):.0f} "
          f"情感分歧{r['composite_index_breakdown'].get('sentiment_volatility',0):.0f} "
          f"平台扩散{r['composite_index_breakdown'].get('platform_spread',0):.0f} "
          f"互动{r['composite_index_breakdown'].get('engagement',0):.0f}")

    print(f"\n  ── 临界减速预警 ──")
    cew = r["critical_early_warning"]
    print(f"  等级: {cew['warning_level']} | 方差比:{cew['variance_ratio']} | AR(1):{cew['ar1_coefficient']}")
    if cew.get("message"):
        print(f"  说明: {cew['message']}")

    print(f"\n  ── 趋势预测（未来 {len(r['predicted_next_24h'])} 步）──")
    for p in r["predicted_next_24h"][:6]:
        print(f"    +{p['steps_from_now']}步(+{p['hours_from_now']}h): "
              f"预测{p['predicted_count']:.0f}  [下界{p['lower_bound']:.0f} ~ 上界{p['upper_bound']:.0f}]")

    print(f"\n  ── 拐点 ──")
    for tp in r["turning_points"]:
        print(f"    {tp['time']}  {tp['type']} ({tp['method']})")

    resurgence = r["resurgence"]
    print(f"\n  ── 二次爆发 ──")
    print(f"  检测结果: {'[YES]' if resurgence['is_resurgence'] else '[NO]'}")
    if resurgence.get("interpretation"):
        print(f"  {resurgence['interpretation']}")


def main():
    json_path = PROJECT.parent / "3.data" / "event_timeseries_result.json"
    if not json_path.exists():
        print(f"[错误] 找不到数据文件: {json_path}")
        sys.exit(1)

    print("=" * 70)
    print("  网络舆情事件智能分析系统 — 真实数据运行")
    print(f"  数据源: {json_path}")
    print("=" * 70)

    events = load_3data(str(json_path))
    print(f"\n加载 {len(events)} 个事件")

    # 模块1: 生命周期
    lifecycle_results = run_lifecycle(events)

    # 模块3: 虚假检测
    run_fake_detection()

    # 模块4: 跨事件因果
    run_cross_event(events)

    # 单个事件详情
    run_one_event_detail(events, "EVT_000001")

    print("\n" + "=" * 70)
    print("  [完成] 全部模块运行完毕")
    print("=" * 70)


if __name__ == "__main__":
    main()

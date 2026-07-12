"""多信号融合 & 日周期剥离"""
from __future__ import annotations
from typing import Any


def remove_diurnal_cycle(records: list[dict[str, Any]], data_interval_hours: int = 6) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """剥离昼夜波动，返回 (decycled_records, diurnal_info)。

    按 data_interval_hours 自动调整分桶数：
      1h  → 24个桶（每个桶=1小时）
      6h  → 4个桶（每个桶=6小时：凌晨0-6, 上午6-12, 下午12-18, 晚上18-24）
      12h → 2个桶
      24h → 跳过（日粒度下无意义）
    """
    n = len(records)
    bins_per_day = max(1, 24 // data_interval_hours)
    min_records_needed = bins_per_day * 2  # 至少2天数据才做周期分析

    if data_interval_hours >= 24:
        return records, {"has_cycle": False, "reason": f"数据间隔{data_interval_hours}h，日周期无意义", "peak_hour": None, "trough_hour": None, "amplitude": 0.0}
    if n < min_records_needed:
        return records, {"has_cycle": False, "reason": f"数据不足{min_records_needed}个点（{data_interval_hours}h间隔）", "peak_hour": None, "trough_hour": None, "amplitude": 0.0}

    bin_sum = [0.0] * bins_per_day
    bin_count = [0] * bins_per_day
    for r in records:
        t = r["time"]
        if isinstance(t, str):
            from datetime import datetime
            t = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        bin_idx = (t.hour % 24) // data_interval_hours
        if bin_idx >= bins_per_day:
            bin_idx = bins_per_day - 1
        bin_sum[bin_idx] += r.get("news_count", 0)
        bin_count[bin_idx] += 1

    bin_avg = [bin_sum[b] / bin_count[b] if bin_count[b] > 0 else 0.0 for b in range(bins_per_day)]
    overall_avg = sum(bin_avg) / bins_per_day if bins_per_day > 0 else 0.0
    if overall_avg < 0.5:
        return records, {"has_cycle": False, "reason": "报道量极低", "peak_hour": None, "trough_hour": None, "amplitude": 0.0}

    bin_factor = [bin_avg[b] / overall_avg if overall_avg > 0 else 1.0 for b in range(bins_per_day)]
    peak_bin = max(range(bins_per_day), key=lambda b: bin_factor[b])
    trough_bin = min(range(bins_per_day), key=lambda b: bin_factor[b])
    amplitude = bin_factor[peak_bin] - bin_factor[trough_bin]

    bin_labels = {1: ["0时", "1时", "2时", "3时", "4时", "5时", "6时", "7时", "8时", "9时", "10时", "11时", "12时", "13时", "14时", "15时", "16时", "17时", "18时", "19时", "20时", "21时", "22时", "23时"], 6: ["凌晨0-6时", "上午6-12时", "下午12-18时", "晚间18-24时"], 12: ["白天0-12时", "夜间12-24时"]}
    labels = bin_labels.get(data_interval_hours, [f"时段{b}" for b in range(bins_per_day)])

    if amplitude < 0.30:
        return records, {"has_cycle": False, "reason": f"日周期振幅仅 {amplitude:.2f}（需≥0.30）", "peak_hour": peak_bin, "trough_hour": trough_bin, "amplitude": round(amplitude, 3), "bin_labels": labels}

    decycled = []
    for r in records:
        t = r["time"]
        if isinstance(t, str):
            from datetime import datetime
            t = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        bin_idx = (t.hour % 24) // data_interval_hours
        if bin_idx >= bins_per_day:
            bin_idx = bins_per_day - 1
        factor = bin_factor[bin_idx] if bin_factor[bin_idx] > 0.1 else 1.0
        rec = dict(r)
        rec["news_count"] = int(round(r.get("news_count", 0) / factor))
        rec["_raw_news_count"] = r.get("news_count", 0)
        rec["_diurnal_factor"] = round(factor, 3)
        decycled.append(rec)

    return decycled, {"has_cycle": True, "peak_hour": peak_bin, "peak_label": labels[peak_bin] if peak_bin < len(labels) else str(peak_bin), "trough_hour": trough_bin, "trough_label": labels[trough_bin] if trough_bin < len(labels) else str(trough_bin), "amplitude": round(amplitude, 3), "bin_count": bins_per_day, "bin_labels": labels, "bin_factors": [round(f, 3) for f in bin_factor], "data_interval_hours": data_interval_hours}


def compute_heat_index(records: list[dict[str, Any]], detector: Any) -> list[int]:
    """四维信号融合为综合热度指数 (0~100)，结果存入 detector._last_index_breakdown"""
    n = len(records)
    if n == 0:
        return []

    raw_volume = [r.get("news_count", 0) for r in records]
    raw_sentiment = []
    for r in records:
        pos = r.get("positive_ratio", 0.33)
        neg = r.get("negative_ratio", 0.33)
        raw_sentiment.append(1.0 - abs(pos - neg))
    raw_spread = []
    for r in records:
        pdist = r.get("platform_distribution", {})
        raw_spread.append(sum(1 for v in pdist.values() if v > 0) if isinstance(pdist, dict) else 1)
    raw_engagement = [r.get("hot_score", 0) for r in records]

    def _norm(vals, default_max=1.0):
        vmax = max(max(vals), default_max)
        return [min(v / vmax * 100, 100) for v in vals] if vmax > 0 else [0.0] * len(vals)

    nv = _norm(raw_volume, 15)
    ns = [v * 100 for v in raw_sentiment]
    np_ = _norm(raw_spread, 4)
    ne = [min(v, 100) for v in raw_engagement]

    w = {"volume": 0.40, "sentiment_volatility": 0.25, "platform_spread": 0.20, "engagement": 0.15}
    composite = [int(round(w["volume"] * nv[i] + w["sentiment_volatility"] * ns[i] + w["platform_spread"] * np_[i] + w["engagement"] * ne[i])) for i in range(n)]

    detector._last_index_breakdown = {"volume": round(nv[-1], 1), "sentiment_volatility": round(ns[-1], 1), "platform_spread": round(np_[-1], 1), "engagement": round(ne[-1], 1), "composite": composite[-1]}
    return composite

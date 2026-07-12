"""舆情生命周期检测器 — 主类"""
from __future__ import annotations
import math
from datetime import datetime
from typing import Any

from .stage import STAGE_DECLINING, STAGE_LATENT, STAGE_RESURGENCE, STAGE_UNKNOWN, classify_stage
from .fusion import remove_diurnal_cycle, compute_heat_index
from .forecast import forecast_holt
from .changepoint import find_turning_points
from .resurgence import detect_resurgence
from .critical import detect_critical_slowing_down


class LifecycleDetector:
    def __init__(self, data_interval_hours=6, growth_threshold=0.15,
                 decline_threshold=-0.10, peak_count_threshold=30, latent_count_threshold=5,
                 ema_alpha=0.30):
        """
        data_interval_hours: 每条 timeseries 记录之间的时间间隔（小时）
                             1  = 每小时一条（原默认）
                             6  = 每6小时一条（3号当前数据）
                             12 = 每12小时一条（半天）
                             24 = 每天一条
        其余参数自动按间隔缩放。
        """
        self.data_interval_hours = data_interval_hours
        # 窗口尺寸：始终覆盖最近 ~24 小时
        self.window_size = max(3, 24 // data_interval_hours)
        # 趋势阈值不变
        self.growth_threshold = growth_threshold
        self.decline_threshold = decline_threshold
        self.peak_count_threshold = peak_count_threshold
        self.latent_count_threshold = latent_count_threshold
        self.ema_alpha = ema_alpha
        self._current_event_id = ""
        self._last_index_breakdown = {}

    @staticmethod
    def _parse_time(t):
        """标准化时间：字符串 → datetime；datetime → 不变"""
        if isinstance(t, str):
            from datetime import datetime
            try:
                return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
        return t

    @staticmethod
    def _format_time(t) -> str:
        """标准化时间输出：datetime → 字符串"""
        if isinstance(t, str):
            return t
        return t.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _trim_padding(records: list[dict]) -> list[dict]:
        """剔除头尾连续的零值填充（3号数据会填满所有时间槽）。

        只删两端，保留中间的零值（因为舆情确实可能出现零报道的时段）。
        """
        if not records:
            return records
        start = 0
        while start < len(records) and records[start].get("news_count", 0) == 0:
            start += 1
        end = len(records)
        while end > start and records[end - 1].get("news_count", 0) == 0:
            end -= 1
        trimmed = records[start:end]
        return trimmed if trimmed else records

    @staticmethod
    def _interpolate_zeros(counts: list[int]) -> list[int]:
        """零值线性插值：两个非零点之间的零用均值填充。

        只影响连续零值（3号数据中间的空洞），不影响趋势方向，
        但能让 Holt 预测和 CSD 方差计算更稳定。
        """
        n = len(counts)
        filled = list(counts)
        # 找所有非零位置
        nonzero_positions = [i for i, v in enumerate(counts) if v > 0]
        if len(nonzero_positions) < 2:
            return filled  # 不够做插值
        for gap_start_idx in range(len(nonzero_positions) - 1):
            i = nonzero_positions[gap_start_idx]
            j = nonzero_positions[gap_start_idx + 1]
            if j - i <= 1:
                continue
            v_i = counts[i]
            v_j = counts[j]
            step = (v_j - v_i) / (j - i)
            for k in range(i + 1, j):
                filled[k] = int(round(v_i + step * (k - i)))
        return filled

    def _assess_data_quality(self, records: list[dict]) -> str:
        """数据质量分级，基于裁剪后的时间窗口跨度而非绝对非零点数。

        裁剪后剩余的槽 = 事件真实发生的时间窗口。中间的零值是正常的
        舆情静默期（凌晨没新闻），不是数据质量缺陷。

        返回: "sparse" | "minimal" | "basic" | "full"
        """
        n = len(records)
        nonzero = sum(1 for r in records if r.get("news_count", 0) > 0)

        if n < 4 or nonzero < 2:
            return "sparse"
        if n < 8:
            return "minimal"
        if n < 12:
            return "basic"
        return "full"

    def detect(self, event_data):
        records = event_data["timeseries"]
        if not records:
            return {"event_id": event_data.get("event_id"), "current_stage": STAGE_UNKNOWN, "error": "没有数据"}

        # 裁剪头尾零值填充
        records = self._trim_padding(records)
        n_original = len(event_data["timeseries"])
        n_trimmed = len(records) if records else 0

        # 数据质量分级
        quality_grade = self._assess_data_quality(records)
        n_effective = sum(1 for r in records if r.get("news_count", 0) > 0)

        # 质量提示
        grade_notes = {
            "sparse": f"数据仅{n_trimmed}个时间槽、{n_effective}处报道，仅能做基础阶段研判",
            "minimal": f"事件跨{n_trimmed}个时间段，可做阶段+趋势分析",
            "basic": f"事件跨{n_trimmed}个时间段，可做阶段+趋势+变点分析",
            "full": f"事件跨{n_trimmed}个时间段，全功能可用（含预测+预警）",
        }

        # 设置当前事件 ID，让 classify_stage 的 EMA 按事件分组
        self._current_event_id = event_data.get("event_id", "")

        counts = [r["news_count"] for r in records]
        times = [self._parse_time(r["time"]) for r in records]

        # 日周期剥离（minimal 以上才做）
        if quality_grade in ("basic", "full"):
            decycled_records, diurnal_info = remove_diurnal_cycle(records, self.data_interval_hours)
        else:
            decycled_records, diurnal_info = records, {"has_cycle": False, "reason": "数据不足，跳过日周期分析"}

        composite_index = compute_heat_index(decycled_records, self)

        # 趋势计算（用插值后的序列，避免零值拉低均值）
        filled_index = self._interpolate_zeros(composite_index)
        trend_slope, trend_direction = self._calc_trend(filled_index)
        # 分类用均值（稳定），展示用峰值（更直观）
        current_level = self._calc_current_level(filled_index)

        # 临界减速预警（basic+full 才跑）
        if quality_grade in ("basic", "full"):
            critical_warning = detect_critical_slowing_down(composite_index, self.data_interval_hours)
        else:
            critical_warning = {"warning_level": "none", "reason": "数据不足，跳过CSD预警"}

        # 阶段判定
        stage, probabilities = classify_stage(composite_index, trend_direction, current_level, self, self.data_interval_hours)

        # 二次爆发检测（basic+full 才跑，且非 sparse）
        if quality_grade in ("basic", "full"):
            resurgence_info = detect_resurgence(composite_index, times, stage, self.data_interval_hours)
        else:
            resurgence_info = {"is_resurgence": False, "reason": "数据不足，跳过二次爆发检测"}

        if resurgence_info.get("is_resurgence"):
            stage = STAGE_RESURGENCE
            probs = probabilities.copy()
            probs["二次爆发"] = resurgence_info["confidence"]
            probs["衰退期"] = max(0, probs.get("衰退期", 0) - resurgence_info["confidence"])
            probabilities = probs

        # 拐点（basic+full）
        if quality_grade in ("basic", "full"):
            turning_points = find_turning_points(composite_index, times, self)
        else:
            turning_points = []

        # 趋势预测（full 才跑，用插值序列）
        forecast_steps = max(2, 72 // self.data_interval_hours)
        if quality_grade == "full":
            predicted_raw = forecast_holt(filled_index, forecast_steps, self.data_interval_hours)
        else:
            predicted_raw = []

        # 展示用热度指数：取最近窗口的峰值（比均值更直观）
        display_window = filled_index[-self.window_size:] if len(filled_index) >= self.window_size else filled_index
        display_nonzero = [v for v in display_window if v > 0]
        heat_index = round(max(display_nonzero), 1) if display_nonzero else 0.0

        result = {
            "event_id": event_data.get("event_id", ""), "current_stage": stage,
            "stage_probabilities": probabilities, "trend_direction": trend_direction,
            "trend_slope": round(trend_slope, 2),
            "current_avg_count": round(self._calc_current_level(counts), 1),
            "current_heat_index": heat_index,
            "composite_index_breakdown": self._last_index_breakdown,
            "turning_points": turning_points, "predicted_next_24h": predicted_raw,
            "total_duration_hours": len(records) * self.data_interval_hours,
            "total_data_points": len(records),
            "peak_count": max(counts),
            "peak_time": self._format_time(times[counts.index(max(counts))]) if counts and max(counts) > 0 else "",
            "diurnal_cycle": diurnal_info, "resurgence": resurgence_info,
            "critical_early_warning": critical_warning,
            "data_quality": {
                "original_points": n_original,
                "trimmed_points": n_trimmed,
                "effective_nonzero_points": n_effective,
                "data_interval_hours": self.data_interval_hours,
                "grade": quality_grade,
                "note": grade_notes.get(quality_grade, ""),
            },
        }
        return result

    def _calc_trend(self, counts):
        n = len(counts)
        if n < 2: return 0.0, "平稳"
        if n < self.window_size * 2:
            half = max(2, n // 2)
            recent, early = counts[-half:], counts[:half]
        else:
            recent = counts[-self.window_size:]
            early = counts[-(self.window_size * 2):-self.window_size]
        # 只对非零值取平均；若全为零则退化为零
        recent_nonzero = [v for v in recent if v > 0]
        early_nonzero = [v for v in early if v > 0]
        recent_avg = sum(recent_nonzero) / len(recent_nonzero) if recent_nonzero else 0.0
        early_avg = sum(early_nonzero) / len(early_nonzero) if early_nonzero else 0.0
        denominator = max(early_avg, 0.5)
        denominator = max(denominator, 0.5)
        if early_avg == 0 and recent_avg == 0: slope = 0.0
        elif early_avg == 0 and recent_avg > 0: slope = 2.0
        else: slope = (recent_avg - early_avg) / denominator
        if slope > self.growth_threshold: direction = "上升"
        elif slope < self.decline_threshold: direction = "下降"
        else: direction = "平稳"
        return slope, direction

    def _calc_current_level(self, counts):
        window = counts[-self.window_size:] if len(counts) >= self.window_size else counts
        nonzero = [v for v in window if v > 0]
        return sum(nonzero) / len(nonzero) if nonzero else 0.0

"""临界减速预警 (Critical Slowing Down)"""
from __future__ import annotations
from typing import Any

import numpy as np


def detect_critical_slowing_down(composite_index: list[int], data_interval_hours: int = 6) -> dict[str, Any]:
    """复杂系统相变前兆检测：方差比 + AR(1)自相关 + 恢复速度

    data_interval_hours: 窗口按间隔自动缩放（覆盖~12时间步的物理时长）。
    """
    n = len(composite_index)
    window = max(4, 12 // data_interval_hours)  # 最少4个点，6h间隔下看最近24h
    if n < window * 3:                          # 至少3个窗口才做对比
        return {"warning_level": "none", "reason": f"数据不足{window * 3}个点"}

    recent = composite_index[-window:]
    recent_arr = np.array(recent, dtype=float)

    recent_var = float(np.var(recent_arr))
    if n >= 2 * window:
        baseline_segment = composite_index[-(3 * window):-window]
    else:
        baseline_segment = composite_index[: n - window]
    baseline_var = float(np.var(np.array(baseline_segment, dtype=float))) if baseline_segment else 1.0
    if baseline_var < 0.5:
        baseline_var = 1.0
    variance_ratio = recent_var / baseline_var

    if len(recent_arr) >= 4:
        y_t, y_t1 = recent_arr[1:], recent_arr[:-1]
        y_m = float(np.mean(recent_arr))
        cov = float(np.mean((y_t - y_m) * (y_t1 - y_m)))
        var_y = float(np.var(recent_arr))
        ar1 = cov / var_y if var_y > 0.01 else 0.0
    else:
        ar1 = 0.0

    recovery_lag = 0
    n_full = len(composite_index)
    for i in range(n_full - 2, max(0, n_full - window - 1), -1):
        if recent_arr[-1] > 0 and abs(composite_index[-1] - composite_index[i]) < 0.3 * recent_arr[-1]:
            recovery_lag += 1
        else:
            break

    # 阈值按6小时间隔校准：window=4，方差比2.0即显著波动
    if variance_ratio > 4.0 and ar1 > 0.50:
        level, msg = "red", f"CRITICAL: 方差飙升{variance_ratio:.1f}x + 自相关增强{ar1:.2f}。系统高度不稳定。"
    elif variance_ratio > 2.0 and ar1 > 0.35:
        level, msg = "orange", f"WARNING: 方差比{variance_ratio:.1f}x，自相关{ar1:.2f}。系统逼近临界点。"
    elif variance_ratio > 1.5 or (variance_ratio > 1.2 and ar1 > 0.30):
        level, msg = "yellow", f"注意：方差比{variance_ratio:.1f}x，系统开始不稳定。"
    else:
        level, msg = "none", ""

    return {"warning_level": level, "variance_ratio": round(variance_ratio, 2), "ar1_coefficient": round(ar1, 3), "recovery_lag": recovery_lag, "window_size": window, "message": msg, "conditions": {"variance_ratio": {"value": round(variance_ratio, 2), "threshold_orange": 2.0, "threshold_red": 3.0}, "ar1_coefficient": {"value": round(ar1, 3), "threshold_orange": 0.5, "threshold_red": 0.7}}}

"""
Holt 双指数平滑预测 — 自适应版

基于 Sawalha & Al-Naymat (2025) "An Adaptive Holt–Winters Model":
  双路并行 Holt 线：
    路径1 (Short): 最近 12 小时窗口 → 捕捉即时趋势变化
    路径2 (Long):  更长窗口         → 捕捉宏观模式
  加权融合后输出。

同时在线搜索最优 (alpha, beta)，替代旧版写死 α=0.3, β=0.1。

参考文献：
  [1] Holt, C. C. (1957). "Forecasting seasonals and trends by EWMA."
  [3] Sawalha, S. & Al-Naymat, G. (2025). "An Adaptive Holt–Winters Model
      for Seasonal Forecasting of IoT Data Streams." IoT (MDPI), 6(3), 39.
"""

from __future__ import annotations
import math
from typing import Any


# —— 可调参数 ——
_ALPHA_CANDIDATES = [0.05, 0.10, 0.20, 0.30, 0.50, 0.70]
_BETA_CANDIDATES  = [0.02, 0.05, 0.10, 0.20, 0.35]
_SHORT_WINDOW      = 12     # 路径1: 最近12小时
_LONG_WINDOW_RATIO = 0.60   # 路径2: 用后60%数据（更长的趋势参考）


def _run_holt(
    counts: list[float], alpha: float, beta: float,
) -> tuple[float, float, float, float]:
    """
    跑一条 Holt 线，返回 (final_level, final_trend, mse, residual_std)
    mse 用于自动选参。
    """
    n = len(counts)
    level = counts[0]
    trend = counts[1] - counts[0] if n > 1 else 0.0
    levels = [level]
    sq_errors = 0.0

    for t in range(1, n):
        y = counts[t]
        prev = level
        level = alpha * y + (1 - alpha) * (level + trend)
        trend = beta * (level - prev) + (1 - beta) * trend
        levels.append(level)
        err = y - level
        sq_errors += err * err

    mse = sq_errors / n if n > 0 else 0.0
    residuals = [counts[i] - levels[i] for i in range(n)]
    residual_std = math.sqrt(sum(r * r for r in residuals) / (n - 1)) if n > 1 else 0.0
    return level, trend, mse, residual_std


def _auto_tune(counts: list[float]) -> tuple[float, float]:
    """
    在候选值里搜最优 (alpha, beta)，最小化拟合 MSE。
    纯 CPU，O(n × |A| × |B|)，对于 72 点 × 30 组合 ≈ 0.001s。
    """
    best = (0.30, 0.10, float("inf"))  # (alpha, beta, mse)
    for a in _ALPHA_CANDIDATES:
        for b in _BETA_CANDIDATES:
            _, _, mse, _ = _run_holt(counts, a, b)
            if mse < best[2]:
                best = (a, b, mse)
    return best[0], best[1]


def forecast_holt(
    counts: list[int],
    hours: int = 24,
    alpha: float | None = None,
    beta: float | None = None,
) -> list[dict[str, Any]]:
    """
    自适应 Holt 双指数平滑预测。

    流程：
      1. 自动搜最优 (alpha, beta) — 除非手动指定
      2. 路径1 (Short):  最近 _SHORT_WINDOW 个点跑 Holt
      3. 路径2 (Long):   更长段跑 Holt（捕捉宏观趋势）
      4. 加权融合：权重反比于各路径的 MSE
      5. 输出预测 + 95% 置信区间

    返回格式不变，前端接口完全兼容。
    """
    n = len(counts)
    if n < 2:
        return []

    vals = [float(c) for c in counts]

    # Step 1: 自动选参
    if alpha is None or beta is None:
        alpha, beta = _auto_tune(vals)

    # Step 2: 路径1 (Short) — 最近窗口
    short_n = min(_SHORT_WINDOW, n)
    short_segment = vals[-short_n:]
    s_level, s_trend, s_mse, s_std = _run_holt(short_segment, alpha, beta)

    # Step 3: 路径2 (Long) — 更长的趋势参考
    long_start = max(0, int(n * (1 - _LONG_WINDOW_RATIO)))
    long_segment = vals[long_start:]
    if len(long_segment) < 3:
        # 数据太少，只用 Short 一条线
        long_segment = vals  # 回退到全量
    l_level, l_trend, l_mse, l_std = _run_holt(long_segment, alpha, beta)

    # Step 4: 加权融合（权重反比于 MSE，MSE 越小权重越大）
    eps = 1e-6
    w_s = 1.0 / (s_mse + eps)
    w_l = 1.0 / (l_mse + eps)
    w_total = w_s + w_l
    w_s /= w_total  # 归一化
    w_l /= w_total

    # 特殊处理：短期波动远大于长期波动时，多信长期线
    # 这是 2025 自适应论文的核心思想——"找到历史相似模式来纠偏"
    if short_n >= 6 and len(long_segment) >= 6:
        short_std = math.sqrt(s_mse) if s_mse > 0 else 0.0
        long_std = math.sqrt(l_mse) if l_mse > 0 else 0.0
        if long_std > 0 and short_std / long_std > 2.5:
            # 短期剧烈波动，多信长期（重新分配权重）
            w_s, w_l = 0.35, 0.65

    fused_level = w_s * s_level + w_l * l_level
    fused_trend = w_s * s_trend + w_l * l_trend

    # 残差标准差用加权
    fused_std = w_s * s_std + w_l * l_std

    # Step 5: 生成预测
    predicted = []
    for h in range(1, hours + 1):
        val = max(0, fused_level + h * fused_trend)
        pred_std = fused_std * math.sqrt(1 + h / n)
        predicted.append({
            "hours_from_now": h,
            "predicted_count": round(val, 1),
            "lower_bound": round(max(0, val - 1.96 * pred_std), 1),
            "upper_bound": round(max(0, val + 1.96 * pred_std), 1),
        })

    return predicted


# —— 自测 ——
if __name__ == "__main__":
    from time_series.utils.mock_data import generate_mock_events

    events = generate_mock_events(num_events=1)
    evt = events[0]

    # 取不同阶段的快照对比
    records = evt["timeseries"]
    for n_points in [15, 35, 60, 72]:
        snapshot = [r["news_count"] for r in records[:n_points]]
        alpha_opt, beta_opt = _auto_tune([float(c) for c in snapshot])
        pred = forecast_holt(snapshot, hours=6)

        print(f"\n{n_points}点 | alpha={alpha_opt:.2f} beta={beta_opt:.2f}")
        print(f"  预测未来6h: ", end="")
        for p in pred[::2]:
            print(f"  +{p['hours_from_now']}h={p['predicted_count']:.0f} [{p['lower_bound']:.0f}-{p['upper_bound']:.0f}]", end="")
        print()

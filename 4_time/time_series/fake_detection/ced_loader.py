"""
CED 数据集加载器
===============
将清华大学 THUNLP 的 CED 微博辟谣数据集加载为训练格式。

数据集位置：data/Chinese_Rumor_Dataset/CED_Dataset/

数据结构：
  original-microblog/  — 所有微博原文（1538条谣言 + 1849条非谣言）
  rumor-repost/        — 谣言对应的转发/评论（文件名与原文对应）
  non-rumor-repost/    — 非谣言对应的转发/评论（文件名与原文对应）

标签判定规则：
  文件名在 rumor-repost/ 中 → label=0 (谣言)
  文件名在 non-rumor-repost/ 中 → label=1 (非谣言)

原始 JSON 字段（与你的特征直接对应）：
  text              → 文本内容
  user.verified     → 信源是否认证
  user.followers    → 粉丝数
  reposts           → 转发数（可用于估算 similar_report_count）
  comments          → 评论数
  time              → 发布时间（Unix 时间戳）
  has_url           → 是否含链接
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any

import numpy as np


# 数据集根目录
DATASET_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "Chinese_Rumor_Dataset" / "CED_Dataset"


def _collect_filenames(directory: Path) -> set[str]:
    """收集目录下所有文件名（不含扩展名）"""
    if not directory.exists():
        return set()
    return {f.stem for f in directory.iterdir() if f.is_file()}


def load_ced_dataset(root: Path | None = None) -> tuple[list[dict[str, Any]], list[int], dict[str, Any]]:
    """
    加载 CED 数据集，返回 (texts, labels, metadata_list)

    返回：
      texts:         微博原文文本列表
      labels:        0=谣言, 1=非谣言
      metadata_list: 每条微博的结构化元数据（可直接喂给 FeatureExtractor）
      stats:         数据集统计信息
    """
    if root is None:
        root = DATASET_ROOT

    original_dir = root / "original-microblog"
    rumor_dir = root / "rumor-repost"
    non_rumor_dir = root / "non-rumor-repost"

    if not original_dir.exists():
        raise FileNotFoundError(
            f"数据集未找到：{root}\n"
            f"请先运行: git clone https://github.com/thunlp/Chinese_Rumor_Dataset.git data/Chinese_Rumor_Dataset"
        )

    # 收集谣言和非谣言的文件名集合
    rumor_files = _collect_filenames(rumor_dir)
    non_rumor_files = _collect_filenames(non_rumor_dir)

    texts = []
    labels = []
    metadata_list = []

    skipped = 0
    unknown_label = 0

    for file_path in sorted(original_dir.iterdir()):
        if not file_path.is_file() or not file_path.suffix == ".json":
            continue

        # 文件名（不含扩展名）用于匹配标签
        stem = file_path.stem

        # 判定标签
        if stem in rumor_files:
            label = 0  # 谣言
        elif stem in non_rumor_files:
            label = 1  # 非谣言
        else:
            unknown_label += 1
            continue  # 既不在谣言也不在非谣言中，跳过

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            skipped += 1
            continue

        text = data.get("text", "")
        if not text or len(text) < 5:
            skipped += 1
            continue

        user = data.get("user", {})
        if not isinstance(user, dict):
            user = {}

        # 提取元数据（对应 FeatureExtractor 的 9 维特征输入）
        # 注意：sentiment_intensity 需要 3 号的 NLP 模块计算，
        # CED 数据集中没有这个字段，设为中性默认值 0.5
        metadata = {
            "source_verified": user.get("verified", False) if isinstance(user.get("verified"), bool) else False,
            "source_followers": user.get("followers", 0),
            # 情感强度：CED 数据集无法提供，设为中性。
            # 真实系统由 3 号 NLP 模块提供。
            "sentiment_intensity": 0.5,
            # 独立信源数：用转发数近似
            "similar_report_count": data.get("reposts", 0),
            # 事件发生后的时长：取发布时间的时分秒，近似为当天的小时偏移
            # （真实的小时数需要 1 号提供事件首次爆发时间）
            "hours_since_event_start": _estimate_hours(data.get("time", 0)),
            "has_url": data.get("has_url", False),
            # 保留原始字段供后续使用
            "_original": {
                "reposts": data.get("reposts", 0),
                "comments": data.get("comments", 0),
                "likes": data.get("likes", 0),
                "pics": data.get("pics", 0),
                "source": data.get("source", ""),
                "user_description": user.get("description", ""),
                "user_gender": user.get("gender", ""),
                "user_location": user.get("location", ""),
            },
        }

        texts.append(text)
        labels.append(label)
        metadata_list.append(metadata)

    stats = {
        "total_loaded": len(texts),
        "rumors": labels.count(0),
        "non_rumors": labels.count(1),
        "skipped": skipped,
        "unknown_label": unknown_label,
        "rumor_files_found": len(rumor_files),
        "non_rumor_files_found": len(non_rumor_files),
        "original_files": len(list(original_dir.iterdir())) if original_dir.exists() else 0,
        "source": "THUNLP CED Dataset (Song et al., 2018)",
    }

    return texts, labels, metadata_list, stats


def _estimate_hours(time_val: object) -> float:
    """
    估算"事件发生后的时长"（小时）

    由于 CED 数据集不包含事件首次爆发时间，这里用发布时间在一天中的
    位置作为近似。真实场景中，这个字段应由 1 号爬虫提供首次报道时间。
    """
    # 处理可能的类型
    unix_time = 0
    if isinstance(time_val, (int, float)):
        unix_time = int(time_val)
    elif isinstance(time_val, str):
        try:
            unix_time = int(time_val)
        except ValueError:
            pass

    if unix_time > 0:
        try:
            dt = datetime.fromtimestamp(unix_time)
            return float(dt.hour) + float(dt.minute) / 60.0
        except (OSError, ValueError):
            pass
    return 12.0  # 默认值


def dataset_to_features(
    texts: list[str],
    labels: list[int],
    metadata_list: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray]:
    """
    将数据集转换为特征矩阵 X 和标签向量 y

    使用 FakeDetectorTrainer 的特征提取器
    """
    from time_series.fake_detection import FeatureExtractor

    extractor = FeatureExtractor()
    X_list = []
    y_list = []

    for text, label, meta in zip(texts, labels, metadata_list):
        features = extractor.extract(text, meta)
        X_list.append(features)
        y_list.append(label)

    X = np.array(X_list)
    y = np.array(y_list)
    return X, y


# ====== 自测 ======
if __name__ == "__main__":
    print("=" * 60)
    print("CED 数据集加载器 — 自测")
    print("=" * 60)

    # 1. 加载数据
    texts, labels, metadata_list, stats = load_ced_dataset()

    print(f"\n[数据统计]")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # 2. 看几个样本
    print(f"\n[样本预览]")
    for i in [0, 500, 1500, 2500]:
        if i < len(texts):
            label_str = "谣言" if labels[i] == 0 else "非谣言"
            text_preview = texts[i][:80].replace("\n", " ")
            meta = metadata_list[i]
            print(f"\n  [{i}] {label_str}")
            print(f"    文本: {text_preview}...")
            print(f"    认证: {meta['source_verified']} | 粉丝: {meta['source_followers']} | "
                  f"转发: {meta['_original']['reposts']} | 评论: {meta['_original']['comments']}")

    # 3. 转换为特征
    print(f"\n[特征转换]")
    X, y = dataset_to_features(texts, labels, metadata_list)
    print(f"  X shape: {X.shape}")
    print(f"  y shape: {y.shape}")
    print(f"  谣言占比: {np.mean(y == 0):.1%}")
    print(f"  非谣言占比: {np.mean(y == 1):.1%}")

    # 4. 特征分布对比
    print(f"\n[特征分布对比]")
    from time_series.fake_detection import FeatureExtractor
    extractor = FeatureExtractor()
    names = extractor.FEATURE_NAMES
    for j, name in enumerate(names):
        rumor_vals = X[y == 0, j]
        non_rumor_vals = X[y == 1, j]
        print(f"  {name:25s} | 谣言均值={rumor_vals.mean():.3f} | 非谣言均值={non_rumor_vals.mean():.3f}")

    print(f"\n[完成] 数据集加载成功！可以直接训练了。")

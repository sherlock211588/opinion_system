"""
CHEF 数据集加载器
===============
加载 CHEF (Chinese Evidence-based Fact-checking) 数据集。
与 CED 微博数据集联合训练，覆盖新闻文章域的虚假检测。

数据集位置：data/CHEF/raw_data/CHEF/

标签映射（CHEF 三分类 → 你的二分类训练标签）：
  CHEF 0 (Supported)        → 1 (可信)
  CHEF 1 (Refuted)          → 0 (虚假)
  CHEF 2 (Not Enough Info)  → 跳过（不参与二分类训练，保留用于校准）

论文：Hu et al., "CHEF: A Pilot Chinese Dataset for Evidence-Based Fact-Checking", NAACL 2022
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

# 数据集根目录
DATASET_ROOT = (
    Path(__file__).resolve().parent.parent.parent
    / "data" / "CHEF" / "raw_data" / "CHEF"
)

# ── 正规新闻源白名单（用于估算 source_verified） ──
VERIFIED_SOURCES = frozenset({
    "新华社", "中新网", "中国新闻网", "人民日报", "央视新闻", "央视网",
    "环球网", "环球时报", "中国青年网", "光明网", "中国政府网",
    "中国互联网辟谣平台", "上海辟谣平台", "北京日报", "南方都市报",
    "中国驻英国使馆网站", "中国驻美国使馆网站", "外交部网站",
    "国家卫健委", "交通运输部", "中国人民银行", "银保监会",
    "澎湃新闻", "新京报", "北京青年报", "参考消息",
    "香港金管局", "澳门特别行政区政府",
    "台湾事实核查中心", "MyGoPen", "腾讯较真", "中国互联网联合辟谣平台",
    "科普中国", "科学辟谣", "丁香医生",
})


def _is_verified_source(source: str) -> bool:
    """判断是否是正规/认证新闻源"""
    for vs in VERIFIED_SOURCES:
        if vs in source:
            return True
    return False


def _estimate_followers(source: str) -> int:
    """根据来源名称粗略估算影响力（用于元数据特征）"""
    if any(k in source for k in ("新华社", "人民日报", "央视")):
        return 50_000_000
    if any(k in source for k in ("中新网", "中国新闻网")):
        return 20_000_000
    if any(k in source for k in ("环球",)):
        return 10_000_000
    if any(k in source for k in ("辟谣", "较真")):
        return 5_000_000
    if any(k in source for k in ("北京", "上海", "南方", "澎湃", "新京报")):
        return 3_000_000
    if any(k in source for k in ("驻", "使馆")):
        return 1_000_000
    return 100_000  # 默认较低


def _extract_text(item: dict[str, Any]) -> str:
    """从 CHEF 样本中提取完整文本：claim + 全部 evidence 拼接"""
    parts = [item.get("claim", "")]

    evidence = item.get("evidence", {})
    if isinstance(evidence, dict):
        for key in sorted(evidence.keys(), key=lambda k: int(k) if k.isdigit() else 999):
            ev = evidence[key]
            if isinstance(ev, dict):
                ev_text = ev.get("text", "")
                if ev_text:
                    parts.append(ev_text)

    return " ".join(parts)


def load_chef_dataset(
    root: Path | None = None,
) -> tuple[list[str], list[int], list[dict[str, Any]], dict[str, Any]]:
    """
    加载 CHEF 数据集用于联合训练

    返回：
      texts:         文本列表（claim + evidence）
      labels:        0=虚假, 1=可信（二分类）
      metadata_list: 每条的结构化元数据（与 FeatureExtractor 对齐）
      stats:         数据集统计信息
    """
    if root is None:
        root = DATASET_ROOT

    if not root.exists():
        raise FileNotFoundError(
            f"CHEF 数据集未找到：{root}\n"
            f"下载地址: https://drive.google.com/file/d/1QKe9i-yXDKh87p4ukRFSnzE03-hAzMto/view\n"
            f"下载后解压到: {root}"
        )

    texts: list[str] = []
    labels: list[int] = []
    metadata_list: list[dict[str, Any]] = []

    stats: dict[str, Any] = {
        "total_in_files": 0,
        "total_loaded": 0,
        "supported": 0,
        "refuted": 0,
        "nie_skipped": 0,
        "skipped_empty": 0,
        "domains": {},
        "source": "CHEF (Hu et al., NAACL 2022)",
    }

    for split_name in ["train.json", "dev.json", "test.json"]:
        file_path = root / split_name
        if not file_path.exists():
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        stats["total_in_files"] += len(data)

        for item in data:
            chef_label = item.get("label", -1)

            # Not Enough Info (label=2)：不参与二分类训练
            if chef_label == 2:
                stats["nie_skipped"] += 1
                continue

            # 标签映射：CHEF 0(Supported)→1(可信), CHEF 1(Refuted)→0(虚假)
            if chef_label == 0:
                label = 1
                stats["supported"] += 1
            elif chef_label == 1:
                label = 0
                stats["refuted"] += 1
            else:
                stats["nie_skipped"] += 1
                continue

            text = _extract_text(item)
            if not text or len(text) < 10:
                stats["skipped_empty"] += 1
                continue

            source = item.get("source", "")
            domain = item.get("domain", "")
            if domain:
                stats["domains"][domain] = stats["domains"].get(domain, 0) + 1

            # ── 构建元数据（字段名与 FeatureExtractor 对齐） ──
            metadata: dict[str, Any] = {
                "source_verified": _is_verified_source(source),
                "source_followers": _estimate_followers(source),
                "sentiment_intensity": 0.5,  # CHEF 不含情感标注，默认中性
                # 证据句子数 ≈ 独立信源覆盖
                "similar_report_count": len(item.get("evidence", {})),
                "hours_since_event_start": 24.0,  # 无精确时间戳，默认1天
                "has_url": bool(item.get("url", "")),
                # 保留原始字段（调试 & 后续扩展用）
                "_original": {
                    "chef_label": chef_label,
                    "source": source,
                    "domain": domain,
                    "category": item.get("category", ""),
                    "verification_method": item.get("verification method", ""),
                    "publish_date": item.get("publish_date", ""),
                    "editor": item.get("editor", ""),
                    "url": item.get("url", ""),
                },
            }

            texts.append(text)
            labels.append(label)
            metadata_list.append(metadata)

    stats["total_loaded"] = len(texts)

    return texts, labels, metadata_list, stats


def load_chef_nie_samples(
    root: Path | None = None,
) -> list[dict[str, Any]]:
    """
    单独加载 CHEF 中 Not Enough Info (label=2) 的样本

    这些样本不参与训练，但可用于：
      - 校准模型的"不确定度"阈值
      - 评估模型对信息不足案例的判定是否合理
    """
    if root is None:
        root = DATASET_ROOT

    nie_samples: list[dict[str, Any]] = []

    for split_name in ["train.json", "dev.json", "test.json"]:
        file_path = root / split_name
        if not file_path.exists():
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            if item.get("label") == 2:
                nie_samples.append({
                    "claim": item.get("claim", ""),
                    "text": _extract_text(item),
                    "source": item.get("source", ""),
                    "domain": item.get("domain", ""),
                    "evidence_count": len(item.get("evidence", {})),
                })

    return nie_samples


# ====== 自测 ======
if __name__ == "__main__":
    print("=" * 60)
    print("CHEF 数据集加载器 — 自测")
    print("=" * 60)

    # 1. 加载训练数据
    texts, labels, metadata_list, stats = load_chef_dataset()

    print("\n[数据统计]")
    for k, v in stats.items():
        if k == "domains":
            top10 = dict(sorted(v.items(), key=lambda x: x[1], reverse=True)[:10])
            print(f"  {k}: {top10}")
        else:
            print(f"  {k}: {v}")

    # 2. 样本预览
    print("\n[样本预览]")
    for i in [0, 100, 500, 2000, 5000]:
        if i < len(texts):
            label_str = "虚假" if labels[i] == 0 else "可信"
            text_preview = texts[i][:100].replace("\n", " ")
            meta = metadata_list[i]
            print(f"\n  [{i}] {label_str}")
            print(f"    文本: {text_preview}...")
            print(f"    来源: {meta['_original']['source']}")
            print(f"    认证: {meta['source_verified']} | 领域: {meta['_original']['domain']}")
            print(f"    证据数: {meta['similar_report_count']}")

    # 3. NIE 样本
    nie = load_chef_nie_samples()
    print(f"\n[NIE 样本] 共 {len(nie)} 条'信息不足'案例")
    if nie:
        print(f"  示例: {nie[0]['claim'][:80]}...")
        print(f"  来源: {nie[0]['source']}")

    # 4. 标签分布
    fake_count = labels.count(0)
    real_count = labels.count(1)
    print(f"\n[标签分布] 虚假={fake_count}, 可信={real_count}, "
          f"虚假占比={fake_count/max(len(labels),1):.1%}")

    print(f"\n[完成] CHEF 数据集加载成功！")

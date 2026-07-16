"""
传播图拓扑特征提取器
===================
从传播图中提取结构特征，用于辅助虚假信息判别。

理论依据：
  真实新闻和假新闻的传播图长得不一样：
    - 真实新闻：多源头、宽而浅、跨平台自然扩散、节点度分布均匀
    - 假新闻：  单源头、窄而深、集中1~2个平台、少数超级节点硬推

10 维拓扑特征（每维都可解释）：
  0. source_count          — 源头数（多源=真实）
  1. max_depth             — 最大传播深度（深=可疑）
  2. avg_path_length       — 平均路径长度（长=精心策划的传播）
  3. density               — 图密度（密=真实讨论，疏=单线传播）
  4. avg_clustering        — 平均聚类系数（高=社区讨论，低=广播模式）
  5. avg_out_degree        — 平均出度（高=用户主动转发，低=靠大V推）
  6. max_out_degree        — 最大出度（单一超级传播者指示器）
  7. platform_count        — 涉及平台数（多=真实跨平台扩散）
  8. cross_platform_ratio  — 跨平台边占比（高=有机扩散）
  9. follower_gini         — 粉丝分布基尼系数（高=少数人主导，低=群众参与）
"""

from __future__ import annotations
from typing import Any


def extract_graph_topology(G: Any, nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """
    从传播图中提取拓扑特征

    参数：
      G: networkx DiGraph（来自 PropagationTracer._build_graph）
      nodes: 原始节点列表（用于平台/粉丝数等属性）

    返回：
      {
        "topology_features": {10维特征字典},
        "verdict_adjustment": "reinforce_real" | "reinforce_fake" | "neutral",
        "topology_interpretation": "人类可读的解释",
      }
    """
    import math

    n = G.number_of_nodes()
    if n < 2:
        return {
            "topology_features": {},
            "verdict_adjustment": "neutral",
            "topology_interpretation": "传播图太小，无法提取有意义的拓扑特征",
        }

    # 0. 源头数
    source_count = sum(1 for nid in G.nodes() if G.in_degree(nid) == 0)
    source_ratio = source_count / n

    # 1. 最大传播深度
    try:
        import networkx as nx
        if nx.is_directed_acyclic_graph(G):
            max_depth = nx.dag_longest_path_length(G) + 1
        else:
            sources = [nid for nid in G.nodes() if G.in_degree(nid) == 0]
            if not sources:
                sources = [list(G.nodes())[0]]
            max_d = 0
            for src in sources:
                lengths = nx.single_source_shortest_path_length(G, src)
                max_d = max(max_d, max(lengths.values()) if lengths else 0)
            max_depth = max_d + 1
    except Exception:
        max_depth = n  # fallback

    # 2. 平均路径长度
    try:
        G_undirected = G.to_undirected()
        if nx.is_connected(G_undirected):
            avg_path = nx.average_shortest_path_length(G_undirected)
        else:
            # 取最大连通分量
            largest_cc = max(nx.connected_components(G_undirected), key=len)
            subgraph = G_undirected.subgraph(largest_cc)
            avg_path = nx.average_shortest_path_length(subgraph) if len(subgraph) > 1 else 0.0
    except Exception:
        avg_path = 0.0

    # 3. 图密度
    density = nx.density(G) if n > 1 else 0.0

    # 4. 平均聚类系数
    try:
        avg_clustering = nx.average_clustering(G.to_undirected())
    except Exception:
        avg_clustering = 0.0

    # 5/6. 出度统计
    out_degrees = [d for _, d in G.out_degree()]
    avg_out_degree = sum(out_degrees) / n if n > 0 else 0.0
    max_out_degree = max(out_degrees) if out_degrees else 0

    # 7. 平台数
    platforms = set()
    for nd in nodes:
        p = nd.get("source", "")
        if p:
            platforms.add(p)
    platform_count = len(platforms) if platforms else 1

    # 8. 跨平台边占比
    node_platform = {}
    for nd in nodes:
        node_platform[nd["node_id"]] = nd.get("source", "")
    cross_edges = 0
    total_edges = G.number_of_edges()
    for u, v in G.edges():
        if node_platform.get(u, "") != node_platform.get(v, ""):
            cross_edges += 1
    cross_platform_ratio = cross_edges / max(total_edges, 1)

    # 9. 粉丝基尼系数（衡量影响力分布不均度）
    followers = [nd.get("follower_count", 0) for nd in nodes]
    followers_sorted = sorted(followers)
    total_f = sum(followers_sorted)
    if total_f > 0 and len(followers_sorted) > 1:
        n_f = len(followers_sorted)
        weighted_sum = sum((i + 1) * followers_sorted[i] for i in range(n_f))
        gini = (2 * weighted_sum - (n_f + 1) * total_f) / (n_f * total_f)
        gini = max(0.0, min(1.0, gini))
    else:
        gini = 0.0

    # ---- 打包特征 ----
    features = {
        "source_count": source_count,
        "source_ratio": round(source_ratio, 4),
        "max_depth": max_depth,
        "avg_path_length": round(avg_path, 3),
        "density": round(density, 4),
        "avg_clustering": round(avg_clustering, 4),
        "avg_out_degree": round(avg_out_degree, 2),
        "max_out_degree": max_out_degree,
        "platform_count": platform_count,
        "cross_platform_ratio": round(cross_platform_ratio, 4),
        "follower_gini": round(gini, 4),
        "node_count": n,
    }

    # ---- 综合判定：此拓扑结构更像真实新闻还是假新闻 ----
    # 真实信号：多源头 + 宽而浅 + 多平台 + 低基尼
    real_signals = 0
    fake_signals = 0

    if source_count >= 2:
        real_signals += 1
    elif source_count == 1:
        fake_signals += 1

    if max_depth <= 3:
        real_signals += 1  # 浅=真实传播
    elif max_depth >= 6:
        fake_signals += 1  # 深=精心策划

    if density >= 0.2:
        real_signals += 1
    elif density < 0.1 and n >= 5:
        fake_signals += 1

    if platform_count >= 3:
        real_signals += 1
    elif platform_count <= 1 and n >= 5:
        fake_signals += 1

    if cross_platform_ratio >= 0.15:
        real_signals += 1

    if gini >= 0.7:
        fake_signals += 1  # 高度不平等=少数人主导
    elif gini < 0.4 and n >= 5:
        real_signals += 1

    # 判定
    if fake_signals >= 2 and fake_signals > real_signals:
        adjustment = "reinforce_fake"
        interpretation = (
            f"传播拓扑结构呈现假新闻特征："
            f"{'单源头' if source_count <= 1 else ''}"
            f"{'、' if source_count <= 1 and max_depth >= 5 else ''}"
            f"{'深传播链(深' + str(max_depth) + '层)' if max_depth >= 5 else ''}"
            f"{'、仅' + str(platform_count) + '个平台' if platform_count <= 1 else ''}"
            f"{'、粉丝高度集中(Gini=' + str(round(gini, 2)) + ')' if gini >= 0.7 else ''}"
            f"。真实信息通常多源头、跨平台、浅层扩散。"
        )
    elif real_signals >= 2 and real_signals > fake_signals:
        adjustment = "reinforce_real"
        interpretation = (
            f"传播拓扑结构呈现真实信息特征："
            f"{'多源头(共' + str(source_count) + '个)' if source_count >= 2 else ''}"
            f"{'、跨' + str(platform_count) + '个平台' if platform_count >= 3 else ''}"
            f"{'、社区式扩散(聚类={:.2f})'.format(avg_clustering) if avg_clustering >= 0.1 else ''}"
            f"。"
        )
    else:
        adjustment = "neutral"
        interpretation = "传播拓扑结构无明显偏向，不足以辅助判断。"

    return {
        "topology_features": features,
        "real_signals": real_signals,
        "fake_signals": fake_signals,
        "verdict_adjustment": adjustment,
        "topology_interpretation": interpretation,
    }

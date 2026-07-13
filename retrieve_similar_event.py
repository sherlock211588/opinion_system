import os
import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# 路径配置
MODEL_LOCAL_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\models\BAAI\bge-base-zh-v1.5"
FAISS_INDEX_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_faiss.index"
EVENT_MAPPING_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_mapping.csv"
EVENT_TABLE_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_table_llm.csv"

# 双阈值分离，互不干扰
TOP_K = 5
CLASSIFY_DIST_THRESHOLD = 0.6   # 归类标准（L2）
SHOW_DIST_THRESHOLD = 0.7     # 前端页面过滤标准

#删掉BGE检索Prompt！不再拼接前缀
# BGE_QUERY_PROMPT = "为这个句子生成表示以用于检索："

# 前置文件存在校验
if not os.path.exists(MODEL_LOCAL_PATH):
    raise FileNotFoundError(f"模型文件夹不存在：{MODEL_LOCAL_PATH}")
if not os.path.exists(FAISS_INDEX_PATH):
    raise FileNotFoundError(f"FAISS索引不存在！请先运行 build_faiss_index.py 生成 {FAISS_INDEX_PATH}")
if not os.path.exists(EVENT_MAPPING_PATH):
    raise FileNotFoundError(f"映射文件不存在：{EVENT_MAPPING_PATH}")
if not os.path.exists(EVENT_TABLE_PATH):
    raise FileNotFoundError(f"事件详情表不存在：{EVENT_TABLE_PATH}")

# 加载映射表和事件详情表
event_mapping = pd.read_csv(
    EVENT_MAPPING_PATH,
    encoding="utf-8-sig"
)
event_table = pd.read_csv(
    EVENT_TABLE_PATH,
    encoding="utf-8-sig"
)

# 全局加载模型与索引
model = SentenceTransformer(MODEL_LOCAL_PATH)
faiss_index = faiss.read_index(FAISS_INDEX_PATH)

def get_text_embedding(text: str) -> np.ndarray:
    """纯原文编码 + L2归一化 + 除零保护，和聚类/索引向量保持一致"""
    emb = model.encode(text)  # 直接编码原文，不加prompt
    norm = np.linalg.norm(emb)
    if norm > 1e-8:
        emb = emb / norm
    return np.array([emb], dtype=np.float32)

def search_faiss(query_text: str, top_k: int = TOP_K):
    query_vec = get_text_embedding(query_text)
    distances, faiss_ids = faiss_index.search(
        query_vec,
        top_k
    )
    results = []
    for dist, fid in zip(
        distances[0],
        faiss_ids[0]
    ):
        # faiss_id查询event_id
        event_row = event_mapping[
            event_mapping["faiss_id"] == fid
        ]
        if len(event_row) == 0:
            continue
        event_id = event_row.iloc[0]["event_id"]
        # 查询事件详情
        info = event_table[
            event_table["event_id"] == event_id
        ]
        if len(info) == 0:
            continue
        info = info.iloc[0]
        results.append({
            "event_id": event_id,
            "faiss_id": int(fid),
            "distance": round(float(dist), 4),
            "title": info["event_title"],
            "category": info["category"],
            "summary": info["event_summary"],
            "keywords": info["event_keywords"],
            "locations": info["event_locations"],
            "times": info["event_times"]
        })
    return results

def judge_new_event(search_result):
    """按L2=0.3阈值判断是否新建事件"""
    if not search_result:
        return True
    top1_l2_dist = search_result[0]["distance"]
    return top1_l2_dist >= CLASSIFY_DIST_THRESHOLD

if __name__ == "__main__":
    test_input = "广西近日强降雨导致洪水，多地群众受灾"
    results = search_faiss(
        test_input,
        TOP_K
    )
    is_new = judge_new_event(results)
    print("检索结果：")
    for r in results:
        print("===================")
        print("事件ID:", r["event_id"])
        print("距离:", r["distance"])
        print("标题:", r["title"])
        print("分类:", r["category"])
        print("概要:", r["summary"])
    print(f"\n是否需要新建事件：{is_new}")
    print(f"前端过滤阈值：仅展示 L2距离 < {SHOW_DIST_THRESHOLD} 的数据")
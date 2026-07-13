import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# 路径配置
MODEL_LOCAL_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\models\BAAI\bge-base-zh-v1.5"
FAISS_INDEX_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_faiss.index"

# 双阈值分离，互不干扰
TOP_K = 5
CLASSIFY_DIST_THRESHOLD = 0.6   # 归类标准（L2）
SHOW_DIST_THRESHOLD = 0.8      # 前端页面过滤标准

#删掉BGE检索Prompt！不再拼接前缀
# BGE_QUERY_PROMPT = "为这个句子生成表示以用于检索："

# 前置文件存在校验
if not os.path.exists(MODEL_LOCAL_PATH):
    raise FileNotFoundError(f"模型文件夹不存在：{MODEL_LOCAL_PATH}")
if not os.path.exists(FAISS_INDEX_PATH):
    raise FileNotFoundError(f"FAISS索引不存在！请先运行 build_faiss_index.py 生成 {FAISS_INDEX_PATH}")

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
    """检索返回全部Top5原始数据"""
    query_vec = get_text_embedding(query_text)
    distances, faiss_ids = faiss_index.search(query_vec, top_k)
    res = []
    for dist, fid in zip(distances[0], faiss_ids[0]):
        res.append((int(fid), round(dist, 4)))
    return res

def judge_new_event(search_result):
    """按L2=0.3阈值判断是否新建事件"""
    if not search_result:
        return True
    top1_l2_dist = search_result[0][1]
    return top1_l2_dist >= CLASSIFY_DIST_THRESHOLD

if __name__ == "__main__":
    try:
        test_input = "虞书欣主演新剧《灿如繁星》即将上线，讲述青春成长故事"
        search_res = search_faiss(test_input, TOP_K)
        print("全部Top5检索结果 [faiss_id, L2距离]：")
        for item in search_res:
            print(item)
        is_new = judge_new_event(search_res)
        print(f"是否需要新建事件：{is_new}")
        print(f"前端过滤阈值：仅展示 L2距离 < {SHOW_DIST_THRESHOLD} 的数据（本脚本为完整调试结果，不受此过滤影响）")
    except Exception as e:
        print(f"脚本运行失败，错误详情：{repr(e)}")
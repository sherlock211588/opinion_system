import faiss
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer


class EventSemanticSearch:
    """
    FAISS向量语义检索历史事件
    输入自然语言query，BGE编码后检索事件向量库，返回相似结构化事件
    """
    def __init__(
        self,
        model_path: str,
        faiss_index_path: str,
        mapping_csv_path: str,
        event_table_csv_path: str,
        top_k: int = 5,
        search_threshold: float = 0.7
    ):
        # 加载BGE向量模型
        # 正确写法
        self.model = SentenceTransformer(r"./models/BAAI/bge-base-zh-v1.5")
        print("模型加载成功")
        print(self.model.encode("测试文本").shape)
        # 加载FAISS事件向量索引
        self.index = faiss.read_index(faiss_index_path)
        # faiss_id <-> event_id 映射表
        self.mapping_df = pd.read_csv(mapping_csv_path, encoding="utf-8-sig")
        # 主事件详情总表
        self.event_df = pd.read_csv(event_table_csv_path, encoding="utf-8-sig")
        # 检索参数
        self.top_k = top_k
        self.search_threshold = search_threshold

    def encode(self, text: str) -> np.ndarray:
        """文本向量化 + L2归一化（和建库编码格式保持一致，不额外加prompt）"""
        vec = self.model.encode(text)
        vec = vec / np.linalg.norm(vec)
        return np.array([vec], dtype=np.float32)

    def search(self, query: str) -> list:
        """语义检索主方法，返回过滤后的相似事件列表"""
        vector = self.encode(query)
        distances, ids = self.index.search(vector, self.top_k)
        result = []

        for dist, fid in zip(distances[0], ids[0]):
            # 距离过滤，超出阈值则丢弃
            if dist > self.search_threshold:
                continue

            # 根据faiss索引id查找真实事件id
            event_id = self.mapping_df[self.mapping_df["faiss_id"] == fid]["event_id"].values[0]
            # 在事件主表读取完整事件信息
            row = self.event_df[self.event_df["event_id"] == event_id].iloc[0]

            result.append({
                "event_id": event_id,
                "title": row["event_title"],
                "category": row["category"],
                "summary": row["event_summary"],
                "keywords": row["event_keywords"],
                "locations": row["event_locations"],
                "times": row["event_times"],
                "distance": round(float(dist), 4)
            })
        return result
# interface/similar_service.py
import sys
import os

# 把项目根目录加入Python模块搜索路径
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)

from retrieve_similar_event import search_faiss

class SimilarEventService:
    def __init__(self, event_service):
        self.event_service = event_service

    def search(self, query, top_k=5):
        # 1.调用FAISS向量检索函数，拿到原始相似结果
        raw = search_faiss(query, top_k)
        res = []
        # 2.遍历每一条FAISS返回的原始数据
        for item in raw:
            eid = item["event_id"]
            # 3.用统一build_event获取完整事件结构（含时序、情感、平台、新闻）
            data = self.event_service.build_event(eid, include_detail=True)
            if data:
                # distance越小越相似，相似度=1-distance
                data["similarity"] = 1 - item["distance"]
                res.append(data)
        return res
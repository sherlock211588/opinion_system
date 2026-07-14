# interface/news_service.py
import pandas as pd
from typing import List, Optional
from config import *


class NewsService:
    """
    新闻数据服务类
    - 读取新闻聚类映射、正文、情感三张数据表
    - 根据 event_id 查询对应新闻列表，返回前端指定格式（article_id = 原始 news_id）
    - 统一情感标签、格式化时间、正文兜底读取
    """
    def __init__(self):
        # 读取三张核心数据表
        self.cluster_df = pd.read_csv(NEWS_CLUSTER_PATH, encoding="utf-8-sig")
        self.content_df = pd.read_csv(NEWS_CONTENT_PATH, encoding="utf-8-sig")
        self.sentiment_df = pd.read_csv(NEWS_SENTIMENT_PATH, encoding="utf-8-sig")

        # 构建 event_id -> news_id 列表映射，快速查找事件对应新闻
        self.event_news_map = (
            self.cluster_df
            .groupby("event_id")["news_id"]
            .apply(list)
            .to_dict()
        )

        # 合并正文表和情感表，以 news_id 作为索引
        self.news_df = pd.merge(
            self.content_df,
            self.sentiment_df,
            on="news_id",
            how="left"
        ).set_index("news_id")

        # 情感标签统一映射规则
        self.sentiment_mapping = {
            "pos": "positive",
            "positive": "positive",
            "neg": "negative",
            "negative": "negative",
            "neutral": "neutral",
            "积极": "positive",
            "消极": "negative",
            "中性": "neutral"
        }

    def _safe_value(self, val, default: str = "") -> str:
        """空值/NaN 兜底处理"""
        return default if pd.isna(val) else str(val).strip()

    def _format_time(self, time_val) -> str:
        """统一时间格式：YYYY-MM-DD HH:mm:ss，异常则原样返回"""
        try:
            return pd.to_datetime(time_val).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(time_val)

    def get_articles_by_event(self, event_id: str) -> List[dict]:
        """
        根据事件ID获取关联新闻列表
        :param event_id: 舆情事件ID
        :return: 新闻数组，主键字段为 article_id (映射原始 news_id)
        """
        # 获取当前事件对应的全部 news_id
        news_id_list = self.event_news_map.get(event_id, [])
        if not news_id_list:
            return []

        # 索引匹配筛选目标新闻
        match_index = self.news_df.index.intersection(news_id_list)
        target_news_df = self.news_df.loc[match_index]

        result = []
        for news_id, row in target_news_df.iterrows():
            # 优先读取 text 正文字段，不存在则降级读取 content
            raw_text = self._safe_value(row.get("text"))
            if not raw_text:
                raw_text = self._safe_value(row.get("content"))

            # 标准化情感标签
            raw_sentiment = self._safe_value(row.get("sentiment")).lower()
            standard_sentiment = self.sentiment_mapping.get(raw_sentiment, "neutral")

            # 组装单条新闻结构，主键字段使用 article_id
            news_item = {
                "article_id": str(news_id),  # 前端要求字段名，值=原始news_id
                "title": self._safe_value(row.get("title")),
                "cleaned_text": raw_text,
                "sentiment": standard_sentiment,
                "source": self._safe_value(row.get("source")),
                "publish_time": self._format_time(row.get("publish_time"))
            }
            result.append(news_item)

        # 按发布时间升序排序
        result.sort(key=lambda x: x["publish_time"])
        return result

    def get_single_article(self, article_id: str) -> Optional[dict]:
        """
        根据 article_id(news_id) 获取单条新闻详情
        :param article_id: 新闻唯一标识（原始 news_id）
        :return: 单条新闻详情字典 / None
        """
        if article_id not in self.news_df.index:
            return None

        row = self.news_df.loc[article_id]

        # 正文兜底读取
        raw_text = self._safe_value(row.get("text"))
        if not raw_text:
            raw_text = self._safe_value(row.get("content"))

        # 标准化情感标签
        raw_sentiment = self._safe_value(row.get("sentiment")).lower()
        standard_sentiment = self.sentiment_mapping.get(raw_sentiment, "neutral")

        return {
            "article_id": str(article_id),
            "title": self._safe_value(row.get("title")),
            "cleaned_text": raw_text,
            "sentiment": standard_sentiment,
            "source": self._safe_value(row.get("source")),
            "publish_time": self._format_time(row.get("publish_time"))
        }
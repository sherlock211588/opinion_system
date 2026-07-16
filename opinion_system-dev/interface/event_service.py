# interface/event_service.py
import pandas as pd
import json
from config import *
from news_service import NewsService


class EventService:
    """
    事件数据服务类
    - 完全对齐 event_table_llm.csv 字段名
    - 提供事件列表、单事件详情、关键词/类别筛选功能
    - 内置情感分布、平台分布、按天统计时序数据
    - 做了数据截断保护，避免Swagger/前端卡死
    """
    def __init__(self):
        # 1. 读取事件主表，event_id 设为索引，完全对齐CSV字段
        self.event_df = pd.read_csv(
            EVENT_TABLE_PATH,
            encoding="utf-8-sig"
        ).set_index("event_id")

        # 2. 加载并处理时序数据：按天统计，适配前端展示
        try:
            with open(EVENT_TIMESERIES_PATH, "r", encoding="utf-8") as f:
                raw_timeseries = json.load(f)

            # 统一转为 {event_id: 时序数据数组} 格式
            self.timeseries_map = {}
            for item in raw_timeseries:
                event_id = item.get("event_id")
                ts_data = item.get("timeseries", [])
                
                #  六小时数据聚合为按天统计（核心修改）
                daily_agg = {}
                for point in ts_data:
                    # 提取日期部分（YYYY-MM-DD），忽略时分秒
                    date_str = pd.to_datetime(point["date"]).strftime("%Y-%m-%d")
                    # 按日期累加新闻数量
                    daily_agg[date_str] = daily_agg.get(date_str, 0) + point["count"]
                
                # 转回数组格式，保持时序结构
                self.timeseries_map[event_id] = [
                    {"date": k, "count": v} for k, v in sorted(daily_agg.items())
                ]
        except Exception:
            self.timeseries_map = {}

        # 3. 绑定新闻服务，用于获取关联新闻
        self.news_service = NewsService()

    def _safe_number(self, val, default: float = 0) -> float:
        """数字类型空值兜底，防止NaN报错"""
        if pd.isna(val):
            return default
        return float(val)

    def _safe_str(self, val, default: str = "") -> str:
        """字符串类型空值兜底，防止空值报错"""
        if pd.isna(val):
            return default
        return str(val).strip()

    def _get_sentiment_dist(self, event_id: str) -> dict:
        """
        获取事件情感分布：优先读取CSV预计算值，兜底实时统计
        完全对齐CSV里的 positive_ratio/negative_ratio/neutral_ratio 字段
        """
        if event_id in self.event_df.index:
            row = self.event_df.loc[event_id]
            try:
                return {
                    "positive": self._safe_number(row["positive_ratio"]),
                    "negative": self._safe_number(row["negative_ratio"]),
                    "neutral": self._safe_number(row["neutral_ratio"])
                }
            except Exception:
                pass

        # 兜底：实时统计该事件下所有新闻的情感
        articles = self.news_service.get_articles_by_event(event_id)
        pos_count = sum(1 for a in articles if a["sentiment"] == "positive")
        neg_count = sum(1 for a in articles if a["sentiment"] == "negative")
        neu_count = sum(1 for a in articles if a["sentiment"] == "neutral")
        total = pos_count + neg_count + neu_count

        if total == 0:
            return {"positive": 0, "negative": 0, "neutral": 0}
        return {
            "positive": round(pos_count / total, 2),
            "negative": round(neg_count / total, 2),
            "neutral": round(neu_count / total, 2)
        }

    def _get_source_distribution(self, event_id: str) -> list:
        """
        获取事件平台分布：读取CSV里的 source_distribution_json 字段
        自动解析为前端可直接渲染的数组格式
        """
        if event_id not in self.event_df.index:
            return []
        row = self.event_df.loc[event_id]
        source_dist_raw = self._safe_str(row.get("source_distribution_json", "[]"))
        
        try:
            # 解析JSON字符串为原生数组，前端直接用
            return json.loads(source_dist_raw)
        except Exception:
            return []

    def build_event(self, event_id: str, include_detail: bool = False) -> dict | None:
        """
        核心方法：统一构造事件标准结构
        :param event_id: 事件唯一ID
        :param include_detail: 是否加载完整详情（时序、新闻、情感、平台分布）
        :return: 事件标准字典 / None（事件不存在时）
        """
        # 事件不存在直接返回None，配合main.py返回404
        if event_id not in self.event_df.index:
            return None

        row = self.event_df.loc[event_id]

        #  基础字段：完全对齐 event_table_llm.csv 里的字段名
        base_event = {
            "event_id": event_id,
            "event_title": self._safe_str(row.get("event_title")),
            "summary": self._safe_str(row.get("event_summary")),
            "keywords": self._safe_str(row.get("event_keywords")),
            "locations": self._safe_str(row.get("event_locations")),
            "category": self._safe_str(row.get("category")),
            "hot_score": self._safe_number(row.get("hot_score")),
            "news_count": int(self._safe_number(row.get("news_count"))),
            "start_time": self._safe_str(row.get("start_time")),
            "end_time": self._safe_str(row.get("end_time"))
        }

        #  详情字段：仅 include_detail=True 时返回，减少基础列表接口数据量
        if include_detail:
            # 1. 情感分布
            base_event["sentiment_distribution"] = self._get_sentiment_dist(event_id)
            # 2. 平台分布
            base_event["source_distribution"] = self._get_source_distribution(event_id)
            # 3. 按天统计的时序数据，最多返回30天，防止前端卡死
            base_event["timeseries"] = self.timeseries_map.get(event_id, [])[:30]
            # 4. 关联新闻，最多返回10条，防止数据量过大
            base_event["articles"] = self.news_service.get_articles_by_event(event_id)[:10]

        return base_event

    def get_event_list(self) -> list[dict]:
        """获取全量事件基础列表（不带详情）"""
        return [
            self.build_event(event_id, include_detail=False)
            for event_id in self.event_df.index
        ]

    def get_single_event(self, event_id: str) -> dict | None:
        """获取单事件完整详情（带情感、平台、时序、新闻）"""
        return self.build_event(event_id, include_detail=True)

    def filter_events(
        self,
        category: str | None = None,
        keyword: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None
    ):
        df = self.event_df.copy()
        if category:
            df = df[df["category"] == category]
        if keyword and keyword.strip():
            keyword_lower = keyword.strip().lower()
            title_mask = df["event_title"].str.lower().str.contains(keyword_lower, na=False)
            summary_mask = df["event_summary"].str.lower().str.contains(keyword_lower, na=False)
            df = df[title_mask | summary_mask]
        if start_time:
            df = df[df["start_time"] >= start_time]
        if end_time:
            df = df[df["end_time"] <= end_time]
        return [self.build_event(eid, include_detail=False) for eid in df.index]
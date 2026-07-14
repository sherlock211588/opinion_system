import pandas as pd

class EventConditionFilter:
    """
    结构化条件筛选历史事件
    支持：固定分类筛选、时间筛选、全文关键词模糊检索（标题+摘要）
    """
    def __init__(self, event_table_csv_path: str):
        self.event_df = pd.read_csv(event_table_csv_path, encoding="utf-8-sig")
        # 统一转为datetime类型，保证时间筛选准确
        self.event_df["start_time"] = pd.to_datetime(self.event_df["start_time"])
        self.event_df["end_time"] = pd.to_datetime(self.event_df["end_time"])

    def filter(
        self,
        category: str = None,
        start_time: str = None,
        end_time: str = None,
        keyword: str = None   # 新增全文关键词参数
    ) -> list:
        df = self.event_df.copy()

        # 1. 原有固定分类精确匹配
        if category:
            df = df[df["category"] == category]

        # 2. 时间筛选
        if start_time:
            s_dt = pd.to_datetime(start_time)
            df = df[df["start_time"] >= s_dt]
        if end_time:
            e_dt = pd.to_datetime(end_time)
            df = df[df["end_time"] <= e_dt]

        # 3. 新增全文模糊检索（标题 + 摘要，不区分大小写）
        if keyword and keyword.strip() != "":
            key = keyword.strip()
            mask_title = df["event_title"].str.contains(key, na=False, case=False)
            mask_summary = df["event_summary"].str.contains(key, na=False, case=False)
            df = df[mask_title | mask_summary]  # 或逻辑：标题 OR 摘要包含关键词

        # 构造返回结果
        result = []
        for _, row in df.iterrows():
            result.append({
                "event_id": row["event_id"],
                "title": row["event_title"],
                "category": row["category"],
                "summary": row["event_summary"],
                "start_time": row["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": row["end_time"].strftime("%Y-%m-%d %H:%M:%S")
            })
        return result
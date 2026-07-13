import pandas as pd


class EventConditionFilter:
    """
    结构化条件筛选历史事件
    根据类别category、起止时间start_time/end_time直接过滤事件主表csv
    """
    def __init__(self, event_table_csv_path: str):
        # 加载主事件详情总表
        self.event_df = pd.read_csv(event_table_csv_path, encoding="utf-8-sig")

    def filter(
        self,
        category: str = None,
        start_time: str = None,
        end_time: str = None
    ) -> list:
        """按类别和时间条件过滤事件"""
        df = self.event_df.copy()

        # 类别筛选
        if category:
            df = df[df["category"] == category]

        # 起始时间筛选
        if start_time:
            df = df[df["start_time"] >= start_time]

        # 结束时间筛选
        if end_time:
            df = df[df["end_time"] <= end_time]

        result = []
        for _, row in df.iterrows():
            result.append({
                "event_id": row["event_id"],
                "title": row["event_title"],
                "category": row["category"],
                "summary": row["event_summary"],
                "start_time": row["start_time"],
                "end_time": row["end_time"]
            })
        return result
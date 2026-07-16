import pandas as pd

# ========== 文件路径 ==========
# 原始事件基础表
EVENT_BASE = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_table_v1.csv"
# 情绪统计附表
SENT_STAT = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_sentiment_stat.csv"
# 事件分类附表
CAT_FILE = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_category.csv"
# 热度分附表
HOT_FILE = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_hot_score.csv"
# 最终完整画像输出
FINAL_OUTPUT = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_table_final.csv"

# 读取四张表
df_event = pd.read_csv(EVENT_BASE, encoding="utf-8-sig")
df_sent = pd.read_csv(SENT_STAT, encoding="utf-8-sig")
df_cat = pd.read_csv(CAT_FILE, encoding="utf-8-sig")
df_hot = pd.read_csv(HOT_FILE, encoding="utf-8-sig")

# 逐层左连接，保证原始事件一条不丢
df_merge1 = pd.merge(df_event, df_sent, on="event_id", how="left")
df_merge2 = pd.merge(df_merge1, df_cat, on="event_id", how="left")
df_final = pd.merge(df_merge2, df_hot, on="event_id", how="left")

# 空值兜底填充
fill_zero_cols = [
    "positive_count", "negative_count", "neutral_count",
    "positive_ratio", "negative_ratio", "neutral_ratio"
]
df_final[fill_zero_cols] = df_final[fill_zero_cols].fillna(0)
df_final["category"] = df_final["category"].fillna("其他")
df_final["hot_score"] = df_final["hot_score"].fillna(0.0)

# 导出完整事件画像
df_final.to_csv(FINAL_OUTPUT, index=False, encoding="utf-8-sig")

print(f"合并完成，最终事件总数：{len(df_final)}")
print(f"完整画像文件已输出至：{FINAL_OUTPUT}")
print("最终包含字段：")
print(df_final.columns.tolist())
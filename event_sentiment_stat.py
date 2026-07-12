import pandas as pd

# ========== 文件路径（分层表）==========
# 新闻-事件映射
CLUSTER_FILE = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_event_cluster.csv"
# 单新闻情感标签
SENTIMENT_FILE = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_sentiment.csv"
# 输出：事件情感统计表
STAT_OUTPUT = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_sentiment_stat.csv"

# ========== 1. 读取两张明细底层表 ==========
df_cluster = pd.read_csv(CLUSTER_FILE, encoding="utf-8-sig")
df_sent = pd.read_csv(SENTIMENT_FILE, encoding="utf-8-sig")

# 关联：每条新闻绑定所属事件+情绪
df_merge = pd.merge(
    df_cluster[["news_id", "event_id"]],
    df_sent[["news_id", "sentiment"]],
    on="news_id",
    how="left"
)

# ========== 2. 按event分组统计三类情绪条数 ==========
# 分组计数，情绪转列，缺失类别填充0
group_cnt = df_merge.groupby("event_id")["sentiment"].value_counts().unstack(fill_value=0)
# 兜底补全三列，防止某类情绪为空丢失字段
for col in ["positive", "negative", "neutral"]:
    if col not in group_cnt.columns:
        group_cnt[col] = 0

# 重命名为_count后缀
group_cnt = group_cnt.rename(columns={
    "positive": "positive_count",
    "negative": "negative_count",
    "neutral": "neutral_count"
})

# ========== 3. 计算三类情绪占比 ==========
# 总新闻数
group_cnt["total"] = group_cnt[["positive_count", "negative_count", "neutral_count"]].sum(axis=1)
divisor = group_cnt["total"].replace(0, 1)
# round(数值, 3) 保留3位；想4位改成round(...,4)
group_cnt["positive_ratio"] = round(group_cnt["positive_count"] / divisor, 3)
group_cnt["negative_ratio"] = round(group_cnt["negative_count"] / divisor, 3)
group_cnt["neutral_ratio"] = round(group_cnt["neutral_count"] / divisor, 3)

# 保留指定字段，重置索引
stat_df = group_cnt[[
    "positive_count",
    "negative_count",
    "neutral_count",
    "positive_ratio",
    "negative_ratio",
    "neutral_ratio"
]].reset_index()

# ========== 4. 保存独立情感附表==========
stat_df.to_csv(STAT_OUTPUT, index=False, encoding="utf-8-sig")
print(f"情感聚合表生成完成，共{len(stat_df)}个事件")
print("输出字段：event_id,positive_count,negative_count,neutral_count,positive_ratio,negative_ratio,neutral_ratio")
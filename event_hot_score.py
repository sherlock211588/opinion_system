import pandas as pd
import numpy as np
from datetime import datetime

# ===================== 路径配置 =====================
EVENT_TABLE_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_table_v1.csv"
SENT_STAT_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_sentiment_stat.csv"
CLUSTER_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_event_cluster.csv"
NEWS_DATA_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn.csv"
OUT_HOT = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_hot_score.csv"

# ===================== 1. 读取数据 =====================
# 事件基础表
df_event = pd.read_csv(EVENT_TABLE_PATH, encoding="utf-8-sig")
# 情绪统计表（存放三类ratio）
df_sent = pd.read_csv(SENT_STAT_PATH, encoding="utf-8-sig")

# 校验情绪附表必须包含三列占比
need_sent_cols = ["positive_ratio", "negative_ratio", "neutral_ratio"]
miss_cols = [c for c in need_sent_cols if c not in df_sent.columns]
if miss_cols:
    raise KeyError(f"event_sentiment_stat.csv 缺失情绪字段：{miss_cols}\n请先运行情感聚合脚本 agg_event_sentiment_stat.py")

# 新闻聚类、新闻源数据
df_cluster = pd.read_csv(CLUSTER_PATH, encoding="utf-8-sig")
df_news = pd.read_csv(NEWS_DATA_PATH, encoding="utf-8-sig")[["news_id", "publish_time", "source"]]
df_merge = pd.merge(df_cluster, df_news, on="news_id", how="left")

# 主表 + 情绪附表合并，所有事件保留
df_full = pd.merge(df_event, df_sent, on="event_id", how="left")
# 无新闻事件情绪填充0
df_full[need_sent_cols] = df_full[need_sent_cols].fillna(0)

# ===================== 2. 全局归一化参数 =====================
# 每个事件独立媒体数量
source_cnt = df_merge.groupby("event_id")["source"].nunique().reset_index()
source_cnt.columns = ["event_id", "unique_source_num"]

max_news = df_full["news_count"].max() if len(df_full) > 0 else 1
max_source = source_cnt["unique_source_num"].max() if len(source_cnt) > 0 else 1

# 动态获取今日日期
today = datetime.now().date()

# ===================== 3. 逐事件计算热度 =====================
hot_result = []
for idx, row in df_full.iterrows():
    eid = row["event_id"]
    news_cnt = row["news_count"]
    end_time = pd.to_datetime(row["end_time"]).date()

    # 从合并后的表读取三类占比
    pos = row["positive_ratio"]
    neg = row["negative_ratio"]
    neu = row["neutral_ratio"]

    # 因子N：新闻数量对数归一
    N = np.log1p(news_cnt) / np.log1p(max_news)

    # 因子T：时间衰减
    day_diff = (today - end_time).days
    T = np.exp(-0.05 * day_diff)

    # 因子S：媒体来源归一
    src_row = source_cnt[source_cnt["event_id"] == eid]
    src_num = src_row["unique_source_num"].iloc[0] if len(src_row) > 0 else 0
    S = src_num / max_source

    # 因子E：综合情绪分
    E = 0.5 * neg + 0.3 * pos + 0.2 * neu

    # 最终热度 0~100，保留1位小数
    raw_hot = 0.35 * N + 0.25 * T + 0.2 * S + 0.2 * E
    hot_score = round(raw_hot * 100, 1)

    hot_result.append({"event_id": eid, "hot_score": hot_score})
    print(f"进度：{idx+1}/{len(df_full)} | event_id:{eid} hot_score:{hot_score}")

# ===================== 4. 输出热度附表 =====================
df_hot = pd.DataFrame(hot_result)
df_hot.to_csv(OUT_HOT, index=False, encoding="utf-8-sig")
print(f"\n热度分表生成完成，共{len(df_hot)}个事件")
print("输出文件：event_hot_score.csv")
print("字段：event_id, hot_score")
import pandas as pd
import json
from datetime import datetime, timedelta
import math

# ===================== 全局配置 =====================
TIME_SLICE_H = 6  # 6小时时间片
FILL_EMPTY_SLICE = True  # True=补齐无新闻空白时间片；False=只保留有报道切片
DATA_ROOT = r"C:\Users\YoLo\Downloads\opinion_system_C\data"

# 输入文件路径
PATH_CLEAN_NEWS = f"{DATA_ROOT}/cleaned_data_cn.csv"
PATH_NEWS_EVENT_MAP = f"{DATA_ROOT}/news_event_cluster.csv"
PATH_NEWS_SENT = f"{DATA_ROOT}/news_sentiment.csv"
PATH_EVENT_TABLE = f"{DATA_ROOT}/event_table_v1.csv"  # 修正：event_table_v1
PATH_EVENT_CATEGORY = f"{DATA_ROOT}/event_category.csv"
PATH_EVENT_GLOBAL_HOT = f"{DATA_ROOT}/event_hot_score.csv"
PATH_EVENT_GLOBAL_SENT = f"{DATA_ROOT}/event_sentiment_stat.csv"

# 输出文件
OUT_JSON = f"{DATA_ROOT}/event_timeseries_result.json"
OUT_DAILY_CSV = f"{DATA_ROOT}/event_sentiment_timeline.csv"
TIME_FMT = "%Y-%m-%d %H:%M:%S"

# 自定义JSON序列化器：处理Timestamp/datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime(TIME_FMT)
        if isinstance(obj, datetime):
            return obj.strftime(TIME_FMT)
        return super().default(obj)

# ===================== 工具函数1：6小时切片左边界生成 =====================
def get_slice_start(dt: datetime):
    hour = dt.hour
    slice_start_h = (hour // TIME_SLICE_H) * TIME_SLICE_H
    slice_start_dt = dt.replace(hour=slice_start_h, minute=0, second=0, microsecond=0)
    slice_start_str = slice_start_dt.strftime(TIME_FMT)
    slice_date = slice_start_dt.strftime("%Y-%m-%d")
    return slice_start_str, slice_date, slice_start_dt

# ===================== 工具函数2：单切片热度计算 =====================
def calc_slice_hot_score(slice_df, ref_now_dt: datetime):
    N = len(slice_df)
    slice_start_str = slice_df["slice_start"].iloc[0]
    slice_start_dt = datetime.strptime(slice_start_str, TIME_FMT)
    slice_mid_dt = slice_start_dt + timedelta(hours=TIME_SLICE_H / 2)
    day_diff = abs((ref_now_dt - slice_mid_dt).total_seconds() / (3600 * 24))
    T = math.exp(-day_diff / 7)
    S = slice_df["source"].nunique()
    S_norm = min(S / 30, 1.0)
    total = len(slice_df)
    neg_cnt = (slice_df["sentiment"] == "negative").sum()
    E = neg_cnt / total if total > 0 else 0
    raw_hot = 0.4 * (N / 50) + 0.3 * T + 0.2 * S_norm + 0.1 * E
    hot_score = round(raw_hot * 100, 1)
    return hot_score

# ===================== 工具函数3：生成起止时间内全部6小时切片字符串 =====================
def generate_all_slice_times(start_dt: datetime, end_dt: datetime):
    all_slices = []
    current = start_dt
    while current <= end_dt:
        s_str = current.strftime(TIME_FMT)
        all_slices.append(s_str)
        current += timedelta(hours=TIME_SLICE_H)
    return all_slices

# ===================== 步骤1：合并单新闻全维度数据 =====================
def merge_all_news_data():
    # 新闻时间字段publish_time
    df_news = pd.read_csv(PATH_CLEAN_NEWS, encoding="utf-8-sig", usecols=["news_id", "publish_time", "source"])
    df_news["publish_dt"] = pd.to_datetime(df_news["publish_time"])
    df_map = pd.read_csv(PATH_NEWS_EVENT_MAP, encoding="utf-8-sig", usecols=["news_id", "event_id"])
    df_sent = pd.read_csv(PATH_NEWS_SENT, encoding="utf-8-sig", usecols=["news_id", "sentiment"])

    df_merge = pd.merge(df_news, df_map, on="news_id", how="inner")
    df_merge = pd.merge(df_merge, df_sent, on="news_id", how="inner")

    slice_info = df_merge["publish_dt"].apply(get_slice_start)
    df_merge["slice_start"] = [x[0] for x in slice_info]
    df_merge["slice_date"] = [x[1] for x in slice_info]
    df_merge["slice_start_dt"] = [x[2] for x in slice_info]
    return df_merge

# ===================== 步骤2：按event_id+6小时切片聚合有数据的窗口 =====================
def calc_slice_metrics(df_all_news, ref_now):
    slice_result = []
    group_keys = ["event_id", "slice_start"]
    for (eid, slice_t), group_df in df_all_news.groupby(group_keys):
        total_cnt = len(group_df)
        pos_cnt = (group_df["sentiment"] == "positive").sum()
        neg_cnt = (group_df["sentiment"] == "negative").sum()
        neu_cnt = (group_df["sentiment"] == "neutral").sum()

        pos_ratio = round(pos_cnt / total_cnt, 3) if total_cnt > 0 else 0.0
        neg_ratio = round(neg_cnt / total_cnt, 3) if total_cnt > 0 else 0.0
        neu_ratio = round(neu_cnt / total_cnt, 3) if total_cnt > 0 else 0.0
        hs = calc_slice_hot_score(group_df, ref_now)

        slice_result.append({
            "event_id": eid,
            "time": slice_t,
            "news_count": total_cnt,
            "hot_score": hs,
            "positive_ratio": pos_ratio,
            "negative_ratio": neg_ratio,
            "neutral_ratio": neu_ratio
        })
    df_slice = pd.DataFrame(slice_result)
    df_slice["slice_dt"] = pd.to_datetime(df_slice["time"])
    df_slice = df_slice.sort_values(["event_id", "slice_dt"]).reset_index(drop=True)
    return df_slice

# ===================== 步骤3：补齐空白无新闻切片 =====================
def fill_empty_slice_data(df_slice, df_all_news, ref_now):
    if not FILL_EMPTY_SLICE:
        return df_slice
    full_list = []
    event_ids = df_slice["event_id"].unique()
    for eid in event_ids:
        evt_slice = df_slice[df_slice["event_id"] == eid].copy()
        evt_news = df_all_news[df_all_news["event_id"] == eid]
        min_slice_dt = evt_slice["slice_dt"].min()
        max_slice_dt = ref_now
        all_window_times = generate_all_slice_times(min_slice_dt, max_slice_dt)
        exist_dict = dict(zip(evt_slice["time"], evt_slice.to_dict("records")))
        for win_t in all_window_times:
            if win_t in exist_dict:
                full_list.append(exist_dict[win_t])
            else:
                empty_item = {
                    "event_id": eid,
                    "time": win_t,
                    "news_count": 0,
                    "hot_score": 0.0,
                    "positive_ratio": 0.0,
                    "negative_ratio": 0.0,
                    "neutral_ratio": 0.0
                }
                full_list.append(empty_item)
    df_full = pd.DataFrame(full_list)
    df_full["slice_dt"] = pd.to_datetime(df_full["time"])
    df_full = df_full.sort_values(["event_id", "slice_dt"]).reset_index(drop=True)
    return df_full

# ===================== 步骤4：读取事件全局完整画像 =====================
def get_event_global_info():
    df_evt = pd.read_csv(PATH_EVENT_TABLE, encoding="utf-8-sig", usecols=[
        "event_id", "event_title", "news_count"
    ])
    df_cat = pd.read_csv(PATH_EVENT_CATEGORY, encoding="utf-8-sig", usecols=["event_id", "category"])
    df_evt_sent = pd.read_csv(PATH_EVENT_GLOBAL_SENT, encoding="utf-8-sig", usecols=[
        "event_id", "positive_ratio", "negative_ratio", "neutral_ratio"
    ])
    df_hot = pd.read_csv(PATH_EVENT_GLOBAL_HOT, encoding="utf-8-sig", usecols=["event_id", "hot_score"])

    df_global = pd.merge(df_evt, df_cat, on="event_id", how="left")
    df_global = pd.merge(df_global, df_evt_sent, on="event_id", how="left")
    df_global = pd.merge(df_global, df_hot, on="event_id", how="left")
    return df_global

# ===================== 步骤5：组装标准JSON（删除slice_dt时间列，避免Timestamp） =====================
def build_output_json(df_global, df_slice):
    output_list = []
    for _, evt_row in df_global.iterrows():
        eid = evt_row["event_id"]
        # 关键：只保留需要的字段，丢弃slice_dt时间字段
        evt_timeseries = df_slice[df_slice["event_id"] == eid].drop(columns=["event_id", "slice_dt"])
        timeseries_arr = evt_timeseries.to_dict("records")

        item = {
            "event_id": eid,
            "event_title": evt_row["event_title"],
            "category": evt_row["category"],
            "hot_score": float(evt_row["hot_score"]),
            "news_count": int(evt_row["news_count"]),
            "sentiment_distribution": {
                "positive": round(float(evt_row["positive_ratio"]), 3),
                "negative": round(float(evt_row["negative_ratio"]), 3),
                "neutral": round(float(evt_row["neutral_ratio"]), 3)
            },
            "timeseries": timeseries_arr
        }
        output_list.append(item)
    return output_list

# ===================== 步骤6：导出每日情绪趋势表 =====================
def export_daily_timeline(df_all_news):
    df_all_news["date"] = df_all_news["publish_dt"].dt.strftime("%Y-%m-%d")
    daily_group = df_all_news.groupby(["event_id", "date", "sentiment"]).size().reset_index(name="cnt")
    daily_pivot = daily_group.pivot_table(
        index=["event_id", "date"],
        columns="sentiment",
        values="cnt",
        fill_value=0
    ).reset_index()
    for col in ["positive", "neutral", "negative"]:
        if col not in daily_pivot.columns:
            daily_pivot[col] = 0
    daily_pivot["day_total"] = daily_pivot["positive"] + daily_pivot["neutral"] + daily_pivot["negative"]
    daily_pivot["pos_ratio"] = (daily_pivot["positive"] / daily_pivot["day_total"]).round(4)
    daily_pivot["neu_ratio"] = (daily_pivot["neutral"] / daily_pivot["day_total"]).round(4)
    daily_pivot["neg_ratio"] = (daily_pivot["negative"] / daily_pivot["day_total"]).round(4)
    daily_pivot.to_csv(OUT_DAILY_CSV, index=False, encoding="utf-8-sig")
    print(f"每日情绪趋势表输出完成：{OUT_DAILY_CSV}")
    return daily_pivot

# ===================== 主执行入口 =====================
if __name__ == "__main__":
    print("1. 合并清洗新闻、事件映射、情感数据...")
    df_full_news = merge_all_news_data()
    print(f"有效新闻总量：{len(df_full_news)}")

    now_dt = datetime.now()
    print("2. 计算6小时切片时序指标...")
    df_slice_data = calc_slice_metrics(df_full_news, ref_now=now_dt)

    print("3. 补齐无新闻空白时间片（FILL_EMPTY_SLICE=True开启）")
    df_slice_full = fill_empty_slice_data(df_slice_data, df_full_news, ref_now=now_dt)

    print("4. 加载event_table_v1事件全局画像...")
    df_event_global = get_event_global_info()

    print("5. 组装标准JSON结构")
    final_json = build_output_json(df_event_global, df_slice_full)

    # 修复：指定cls=DateTimeEncoder，兼容时间对象
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
    print(f"时序JSON文件生成：{OUT_JSON}")

    print("6. 导出每日情绪趋势表 event_sentiment_timeline.csv")
    export_daily_timeline(df_full_news)

    print("\n===== JSON样例输出 =====")
    print(json.dumps(final_json[0], ensure_ascii=False, indent=2, cls=DateTimeEncoder))
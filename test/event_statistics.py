from collections import defaultdict

# 模拟输入数据（聚类+情感推理后的原始结果）
news_result = [
    {"event_id": 0, "sentiment": "negative", "time": "10:00"},
    {"event_id": 0, "sentiment": "negative", "time": "10:10"},
    {"event_id": 0, "sentiment": "neutral", "time": "10:20"},
    {"event_id": 1, "sentiment": "positive", "time": "14:00"},
    {"event_id": 1, "sentiment": "neutral", "time": "14:10"},
    {"event_id": 1, "sentiment": "neutral", "time": "14:20"},
]

# 1. 按event_id分组，统计每个事件下三种情感条数
event_sentiment_cnt = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
for item in news_result:
    eid = item["event_id"]
    sent = item["sentiment"]
    event_sentiment_cnt[eid][sent] += 1

# 2. 遍历每个事件，计算占比，生成目标输出格式
output_list = []
for eid, cnt_dict in event_sentiment_cnt.items():
    total = cnt_dict["positive"] + cnt_dict["negative"] + cnt_dict["neutral"]
    # 防止除0（无新闻边界）
    if total == 0:
        pos_ratio = neg_ratio = neu_ratio = 0.0
    else:
        pos_ratio = round(cnt_dict["positive"] / total, 2)
        neg_ratio = round(cnt_dict["negative"] / total, 2)
        neu_ratio = round(cnt_dict["neutral"] / total, 2)

    event_stat = {
        "event_id": eid,
        "positive_ratio": pos_ratio,
        "negative_ratio": neg_ratio,
        "neutral_ratio": neu_ratio
    }
    output_list.append(event_stat)

# 打印最终交付结果
for res in output_list:
    print(res)
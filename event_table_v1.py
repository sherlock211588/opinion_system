import pandas as pd
import numpy as np

# ====================== 路径配置 ======================
# 输入文件路径
path_cluster = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_event_cluster.csv"
path_clean = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn.csv"
path_embedding = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_embedding.csv"
# 输出基础事件表v1
output_v1 = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_table_v1.csv"

# 余弦相似度工具函数
def calc_cosine(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

# ====================== Step1 读取三份数据源 ======================
print("1/3 读取所有基础数据文件")
# 1. 新闻-事件关联表，过滤EVT_NOISE候选新闻
df_cluster = pd.read_csv(path_cluster, encoding="utf-8-sig")
df_valid_event = df_cluster[df_cluster["event_id"] != "EVT_NOISE"].copy()

# 2. 新闻基础信息：news_id -> title、time
df_clean = pd.read_csv(path_clean, encoding="utf-8-sig")
df_clean["publish_time"] = pd.to_datetime(df_clean["publish_time"])
news_info_map = {}
for _, row in df_clean.iterrows():
    news_info_map[row["news_id"]] = {
        "title": row["title"],
        "publish_time": row["publish_time"]
    }

# 3. 新闻向量映射：news_id -> 768维向量数组
df_emb = pd.read_csv(path_embedding, encoding="utf-8-sig")
emb_cols = [col for col in df_emb.columns if col != "news_id"]
news_vec_map = {}
for _, row in df_emb.iterrows():
    news_vec_map[row["news_id"]] = row[emb_cols].values.astype(np.float64)

# ====================== Step2 按event_id分组聚合计算全部字段 ======================
print("2/3 逐事件计算基础指标")
group_result = []
event_groups = df_valid_event.groupby("event_id")

for event_id, group_df in event_groups:
    news_id_list = group_df["news_id"].tolist()
    news_count = len(news_id_list)

    # 收集当前事件所有新闻标题、时间、向量
    title_list = []
    time_list = []
    vec_list = []
    title_vec_pairs = []
    for nid in news_id_list:
        info = news_info_map[nid]
        vec = news_vec_map[nid]
        title_list.append(info["title"])
        time_list.append(info["publish_time"])
        vec_list.append(vec)
        title_vec_pairs.append((info["title"], vec))

    # 1. 计算事件中心向量
    vec_array = np.array(vec_list)
    center_vec = vec_array.mean(axis=0)
    center_emb_str = ",".join([str(v) for v in center_vec])

    # 2. event_title：选取与事件中心余弦相似度最高的原文标题
    sim_list = []
    for title, vec in title_vec_pairs:
        sim = calc_cosine(vec, center_vec)
        sim_list.append((sim, title))
    # 按相似度降序，取第一条作为事件标题
    sim_list.sort(key=lambda x: x[0], reverse=True)
    event_title = sim_list[0][1]

    # 3. 事件起止时间
    start_time = min(time_list).strftime("%Y-%m-%d %H:%M:%S")
    end_time = max(time_list).strftime("%Y-%m-%d %H:%M:%S")

    # 组装单行数据
    row = {
        "event_id": event_id,
        "event_title": event_title,
        "news_count": news_count,
        "center_embedding": center_emb_str,
        "start_time": start_time,
        "end_time": end_time
    }
    group_result.append(row)

# ====================== Step3 导出event_table_v1.csv ======================
print("3/3 生成并保存基础事件表")
df_out = pd.DataFrame(group_result)
# 固定输出字段顺序
out_columns = [
    "event_id",
    "event_title",
    "news_count",
    "center_embedding",
    "start_time",
    "end_time"
]
df_out = df_out[out_columns]
df_out.to_csv(output_v1, index=False, encoding="utf-8-sig")

print(f"基础事件表event_table_v1.csv 生成完成，路径：{output_v1}")
print("\n前5行预览：")
print(df_out.head())
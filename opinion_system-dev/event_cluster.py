import pandas as pd
import numpy as np
import hdbscan

# ========================== 路径配置 ==========================
embedding_path = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_embedding.csv"
output_path = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_event_cluster.csv"

# 聚类超参（稳定事件核心配置）
MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = 3

# 1. 读取向量表
df_emb = pd.read_csv(embedding_path, encoding="utf-8-sig")
news_id_arr = df_emb["news_id"].copy()
X = df_emb.drop(columns=["news_id"]).values.astype(np.float32)
print(f"向量矩阵尺寸（样本数,向量维度）：{X.shape}")
print(f"向量数据类型：{X.dtype}")

# 2. HDBSCAN聚类
cluster = hdbscan.HDBSCAN(
    min_cluster_size=MIN_CLUSTER_SIZE,
    min_samples=MIN_SAMPLES,
    metric="euclidean",
    cluster_selection_method="eom"
)
cluster_labels = cluster.fit_predict(X)

# 统计聚类结果
stat_series = pd.Series(cluster_labels)
total_samples = len(stat_series)
candidate_num = (stat_series == -1).sum()
valid_cluster_num = stat_series[stat_series != -1].nunique()

print("\n==== 聚类统计结果 ====")
print(f"总新闻样本：{total_samples} 条")
print(f"候选新闻（无稳定事件）：{candidate_num} 条")
print(f"有效事件簇总数：{valid_cluster_num} 个")
print("各簇新闻数量分布：")
print(stat_series.value_counts().sort_index())

# 3. 构造映射表
df_cluster = pd.DataFrame()
df_cluster["news_id"] = news_id_arr
df_cluster["cluster_id"] = cluster_labels

# 转换标准event_id
def make_event_id(cid):
    if cid == -1:
        return "EVT_NOISE"
    serial = cid + 1
    return f"EVT_{serial:06d}"

# 新增事件状态字段
def get_event_status(cid):
    if cid == -1:
        return "candidate"
    return "cluster"

df_cluster["event_id"] = df_cluster["cluster_id"].apply(make_event_id)
df_cluster["event_status"] = df_cluster["cluster_id"].apply(get_event_status)

# 固定输出列顺序：news_id, cluster_id, event_id, event_status
df_cluster = df_cluster[["news_id", "cluster_id", "event_id", "event_status"]]

# 按event_id升序排列，同事件新闻连续集中
df_cluster = df_cluster.sort_values(by="event_id", ignore_index=True)

# 4. 保存结果文件
df_cluster.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"\n聚类映射文件保存完成，路径：{output_path}")
print("\n文件前10行预览：")
print(df_cluster.head(10))
import os

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

DATA_DIR = os.path.join(BASE_DIR, "data")

# 事件
EVENT_TABLE_PATH = os.path.join(DATA_DIR, "event_table_llm.csv")
EVENT_TIMESERIES_PATH = os.path.join(DATA_DIR, "event_timeseries_result.json")
EVENT_FAISS_INDEX_PATH = os.path.join(DATA_DIR, "event_faiss.index")
EVENT_MAPPING_PATH = os.path.join(DATA_DIR, "event_mapping.csv")

# 新闻
NEWS_CONTENT_PATH = os.path.join(DATA_DIR, "cleaned_data_cn.csv")
NEWS_CLUSTER_PATH = os.path.join(DATA_DIR, "news_event_cluster.csv")
NEWS_SENTIMENT_PATH = os.path.join(DATA_DIR, "news_sentiment.csv")

# 模型
MODEL_PATH = os.path.join(BASE_DIR, "models", "BAAI", "bge-base-zh-v1.5")

TOP_K = 5
SEARCH_THRESHOLD = 0.7
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN


model_path = r"C:\Users\Yolo\Downloads\opinion_system_C\models\BAAI\bge-base-zh-v1.5"


model = SentenceTransformer(model_path)


news=[
"南方地区发生暴雨灾害",
"暴雨导致多地出现洪水",
"强降雨造成交通中断",
"某明星发布新电影",
"明星电影获得大量关注",
"娱乐圈发布新作品"
]


vectors=model.encode(
    news,
    normalize_embeddings=True
)


# cosine距离
cluster=DBSCAN(
    eps=0.3,
    min_samples=2,
    metric="cosine"
)


labels=cluster.fit_predict(vectors)



for text,label in zip(news,labels):

    print(
        "event_id:",
        label,
        "|",
        text
    )
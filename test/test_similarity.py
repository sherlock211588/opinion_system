from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


model_path = r"C:\Users\Yolo\Downloads\opinion_system_C\models\BAAI\bge-base-zh-v1.5"


model = SentenceTransformer(model_path)


texts=[
    "南方地区发生严重暴雨，多地出现洪水",
    "持续强降雨导致多个城市受灾",
    "某明星发布新歌曲获得关注"
]


vectors=model.encode(
    texts,
    normalize_embeddings=True
)


sim=cosine_similarity(vectors)


print(sim)
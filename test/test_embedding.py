from sentence_transformers import SentenceTransformer
import numpy as np

# 正确平铺模型顶层路径
model_path = r"C:\Users\Yolo\Downloads\opinion_system_C\models\BAAI\bge-base-zh-v1.5"
model = SentenceTransformer(model_path)

texts = [
    "南方地区发生严重暴雨，多地出现洪水",
    "持续强降雨导致多个城市受灾",
    "某明星发布新歌曲获得关注"
]

embeddings = model.encode(
    texts,
    normalize_embeddings=True
)

print("向量数量:", len(embeddings))
print("向量维度:", embeddings.shape)
print("\n第一条新闻向量前10维:")
print(embeddings[0][:10])
import pandas as pd
import torch
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# ==========================
# 路径配置
# ==========================
INPUT = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn.csv"
OUTPUT = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_embedding.csv"
model_path = r"C:\Users\Yolo\Downloads\opinion_system_C\models\BAAI\bge-base-zh-v1.5"

# ==========================
# 自动使用GPU加速（有显卡自动切换）
# ==========================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"使用计算设备：{device}")
 
# ==========================
# 加载BGE向量模型
# ==========================
model = SentenceTransformer(model_path, device=device)
print("模型加载完成")

# ==========================
# 读取清洗后的新闻
# ==========================
df = pd.read_csv(INPUT, encoding="utf-8-sig")
# 空文本过滤，避免编码报错
df = df[df["content"].notna() & (df["content"].str.strip() != "")]
# 超长文本截断（BGE输入有长度限制，防止报错）
def truncate_text(s, max_len=510):
    if len(s) > max_len:
        return s[:max_len]
    return s
df["content_short"] = df["content"].apply(truncate_text)
texts = df["content_short"].tolist()
news_ids = df["news_id"].tolist()

# ==========================
# 批量生成语义向量
# ==========================
embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True,
    convert_to_numpy=True
)
print("向量总条数 & 维度：", embeddings.shape)

# ==========================
# 保存向量文件（第一列为news_id，后面全是向量维度）
# ==========================
df_embedding = pd.DataFrame(embeddings)
df_embedding.insert(0, "news_id", news_ids)
df_embedding.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
print(f"向量文件保存完成，输出路径：{OUTPUT}")
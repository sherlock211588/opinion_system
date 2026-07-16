import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# ====================== 路径配置 ======================
# 输入清洗新闻表（含news_id、content）
clean_data_path = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn.csv"
# 情感模型本地路径
sentiment_model_path = r"C:\Users\Yolo\Downloads\opinion_system_C\models\yangjiurong\chinese-sentiment-c3-v1"
# 输出单新闻情感结果
sentiment_out_path = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_sentiment.csv"

# 分类映射：模型输出0/1/2 对应情绪标签
label_mapping = {
    0: "negative",
    1: "neutral",
    2: "positive"
}

# ====================== 加载模型与分词器 ======================
print("加载中文三分类情感模型...")
tokenizer = AutoTokenizer.from_pretrained(sentiment_model_path)
model = AutoModelForSequenceClassification.from_pretrained(sentiment_model_path)
model.eval()
# 自动使用GPU加速，无GPU则CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"模型加载完成，推理设备：{device}")

# ====================== 批量推理函数 ======================
def infer_sentiment(text_list, batch_size=32):
    total_text = len(text_list)
    pred_labels = []
    for start in range(0, total_text, batch_size):
        batch_text = text_list[start:start + batch_size]
        # 分词
        inputs = tokenizer(
            batch_text,
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors="pt"
        ).to(device)
        # 推理不计算梯度
        with torch.no_grad():
            outputs = model(**inputs)
        preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
        pred_labels.extend([label_mapping[p] for p in preds])
    return pred_labels

# ====================== 读取新闻数据并推理 ======================
print("\n读取新闻清洗数据...")
df_clean = pd.read_csv(clean_data_path, encoding="utf-8-sig")
# 过滤空正文，避免推理报错
df_valid = df_clean[df_clean["content"].notna()].copy()
news_id_list = df_valid["news_id"].tolist()
content_list = df_valid["content"].tolist()

print(f"待推理新闻总量：{len(news_id_list)} 条，开始情感预测...")
sentiment_result = infer_sentiment(content_list)

# 组装输出表
df_sentiment = pd.DataFrame({
    "news_id": news_id_list,
    "sentiment": sentiment_result
})

# 保存csv
df_sentiment.to_csv(sentiment_out_path, index=False, encoding="utf-8-sig")
print(f"\n情感推理完成，结果已保存至：{sentiment_out_path}")
print("前5行预览：")
print(df_sentiment.head())
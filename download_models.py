from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import os

# 锁定项目根目录（脚本在opinion_system_C顶层）
script_abs = os.path.abspath(__file__)
project_root = os.path.dirname(script_abs)
models_root = os.path.join(project_root, "models")

# 严格规定目标路径
bge_target = os.path.join(models_root, "BAAI", "bge-base-zh-v1.5")
sent_target = os.path.join(models_root, "IDEA-CCNL", "Erlangshen-Roberta-110M-Sentiment")

# 创建分层文件夹
os.makedirs(bge_target, exist_ok=True)
os.makedirs(sent_target, exist_ok=True)
print(f"项目根目录：{project_root}")
print(f"BGE平铺目录：{bge_target}")
print(f"情感模型平铺目录：{sent_target}\n")

# 1. BGE向量模型，平铺保存
print("===== 下载 BAAI/bge-base-zh-v1.5 =====")
bge_model = SentenceTransformer("BAAI/bge-base-zh-v1.5")
# save会平铺所有模型文件，无snapshots嵌套
bge_model.save(bge_target)
# 校验
test_vec = bge_model.encode("南方暴雨洪涝")
print(f"BGE校验完成，向量维度：{test_vec.shape}\n")

# 2. 情感模型平铺保存
print("===== 下载 IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment =====")
model_name = "IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
sent_model = AutoModelForSequenceClassification.from_pretrained(model_name)
# 平铺导出全套配置与权重
tokenizer.save_pretrained(sent_target)
sent_model.save_pretrained(sent_target)

# 情感校验
from transformers import pipeline
sent_pipe = pipeline("text-classification", model=sent_model, tokenizer=tokenizer)
test_res = sent_pipe("暴雨致大量房屋损毁")
print(f"情感模型校验完成，输出：{test_res}\n")

print(" 执行完毕！模型平铺在 opinion_system_C/models/BAAI、opinion_system_C/models/IDEA-CCNL")
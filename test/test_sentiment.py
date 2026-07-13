from transformers import pipeline


model_path=r"C:\Users\Yolo\Downloads\opinion_system_C\models\yangjiurong\chinese-sentiment-c3-v1"


classifier=pipeline(
    "sentiment-analysis",
    model=model_path,
    tokenizer=model_path
)

label_mapping = classifier.model.config.id2label
print("===== 模型情感分类信息 =====")
print("数字编号 -> 情感标签：", label_mapping)
print("模型一共能分辨的情感类别数量：", len(label_mapping))
print("所有标签名称：", list(label_mapping.values()))

texts=[
"救援工作顺利开展，群众得到帮助",
"救援行动取得阶段性成果",
"群众生活逐渐恢复",
"政策实施获得认可",
"事故造成重大损失",
"灾害造成严重损失，多人受伤",
"事件引发社会关注",
"政府发布事件通报",
"相关部门召开新闻发布会",
"今天发布了一条普通新闻",
"记者报道现场情况"
]


for t in texts:

    result=classifier(t)

    print(
        t,
        result
    )
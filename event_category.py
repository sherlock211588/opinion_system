import pandas as pd
import openai
import time
from openai import OpenAI

# 路径配置
EVENT_TABLE_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_table_v1.csv"
CLUSTER_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_event_cluster.csv"
NEWS_DATA_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn.csv"
OUT_CATEGORY = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_category.csv"

# 固定分类列表
CATEGORY_LIST = [
    "社会民生", "政治政策", "经济财经", "科技互联网",
    "体育赛事", "娱乐明星", "教育考试", "健康医疗",
    "灾害事故", "国际事件", "其他"
]
CATEGORY_STR = "、".join(CATEGORY_LIST)

# LLM配置（替换成key/接口）
# 初始化DeepSeek客户端
# 完整地址：https://api.deepseek.com/v1
client = OpenAI(
    api_key="sk-xxxxxxxxxxxxxxxxxxxxxxxx",  填写DeepSeek的API Key
    base_url="https://api.deepseek.com/v1"
)

def llm_classify(title, news_titles):
    prompt = f"""
请根据事件标题+配套新闻标题，仅输出一个匹配的分类名称，只能从【{CATEGORY_STR}】里选，不要多余文字。
事件标题：{title}
相关新闻：
{chr(10).join([f"{i+1}.{t}" for i,t in enumerate(news_titles)])}
只输出分类名称：
"""
    resp = client.chat.completions.create(
        model="deepseek-v4-pro", # 可选 deepseek-v4-flash
        messages=[{"role":"user","content":prompt}],
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()

# 1. 读取数据
df_event = pd.read_csv(EVENT_TABLE_PATH, encoding="utf-8-sig")
df_cluster = pd.read_csv(CLUSTER_PATH, encoding="utf-8-sig")
df_news = pd.read_csv(NEWS_DATA_PATH, encoding="utf-8-sig")[["news_id","title"]]

# 关联event与新闻标题
df_event_news = pd.merge(df_cluster, df_news, on="news_id", how="left")

# 按event_id聚合，每个事件取前5条新闻标题
event_news_title_map = {}
for eid, group in df_event_news.groupby("event_id"):
    titles = group["title"].dropna().unique().tolist()[:5]
    event_news_title_map[eid] = titles

# 2. 批量LLM分类
res_list = []
for _, row in df_event.iterrows():
    eid = row["event_id"]
    e_title = row["event_title"]
    top5_news = event_news_title_map.get(eid, [])
    cat = llm_classify(e_title, top5_news)
    res_list.append({"event_id": eid, "category": cat})
    time.sleep(0.3) # 限流防报错

# 3. 输出分类附表
df_cat = pd.DataFrame(res_list)
df_cat.to_csv(OUT_CATEGORY, index=False, encoding="utf-8-sig")
print(f"分类表生成完成，共{len(df_cat)}个事件")
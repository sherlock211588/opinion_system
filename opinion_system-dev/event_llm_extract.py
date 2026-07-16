"""
文件：event_llm_extract.py
功能：
1. 读取三张基础数据表，对每个事件抽取LLM结构化信息（概要/关键词/人物/地点/时间）
2. 自动统计事件新闻来源平台分布，生成平台占比结构化数据
3. LLM使用DeepSeek在线API
输入：
    event_table_final.csv 事件基础表（自带category无需AI分类）
    news_event_cluster.csv 新闻-event关联表
    cleaned_data_cn.csv 新闻明细（字段publish_time、source平台字段）
输出：event_table_llm.csv
新增字段：
    event_summary LLM事件概要
    event_keywords JSON关键词数组
    event_persons JSON人物数组
    event_locations JSON地点数组
    event_times JSON时间数组
    source_distribution_json JSON平台分布[{平台,条数,占比}]
"""
import os
import json
import logging
import time
import pandas as pd
from collections import Counter
from tqdm import tqdm
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

# ====================== 全局配置区 ======================
# 文件路径
EVENT_TABLE_RAW = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_table_final.csv"
CLUSTER_MAPPING = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_event_cluster.csv"
NEWS_DATA_CSV = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn.csv"
OUTPUT_FULL = r"C:\Users\Yolo\Downloads\opinion_system_C\data\event_table_llm.csv"
LOG_PATH = r"./event_llm_run.log"

# DeepSeek API配置（替换自己的key）
LLM_API_KEY = "sk-xxxxxxxxxxxx"
LLM_BASE_URL = "https://api.deepseek.com/v1"
MODEL_NAME = "deepseek-chat"
LLM_TEMP = 0.2
LLM_MAX_TOKENS = 800
RETRY_TIMES = 3
RETRY_WAIT = 2

# 文本控制参数
MAX_EVENT_NEWS = 5        # 单事件最多取5条新闻送入LLM
SINGLE_CONTENT_CUT = 800  # 单条正文截断长度
TOTAL_INPUT_LIMIT = 4000 # 总输入文本上限
# ======================================================================

# 日志初始化
def init_logger():
    logger = logging.getLogger("EventLLMExtract")
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    log_format = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger

logger = init_logger()

# DeepSeek客户端初始化
client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

# JSON清洗、安全解析工具
def clean_llm_json(raw_text: str) -> str:
    text = raw_text.strip()
    text = text.replace("```json", "").replace("```", "")
    text = text.replace("\n", "").replace(" ", "")
    return text

def safe_parse_json(text: str):
    try:
        clean_txt = clean_llm_json(text)
        data = json.loads(clean_txt)
        std_keys = ["summary", "keywords", "persons", "locations", "times"]
        for k in std_keys:
            if k not in data:
                data[k] = "" if k == "summary" else []
        return data
    except Exception as e:
        logger.warning(f"JSON解析失败，报错：{str(e)} 原文片段：{text[:300]}")
        return {
            "summary": "",
            "keywords": [],
            "persons": [],
            "locations": [],
            "times": []
        }

# 构造抽取Prompt
def build_extract_prompt(news_merge_text: str) -> str:
    prompt = """你是专业舆情事件分析师，仅输出标准JSON，禁止多余文字、解释、说明。
依据多条同事件新闻完成5项提取：
1.summary事件概要：100~200字，完整概括起因、发展、舆情影响，禁止简单拼接标题；
2.keywords关键词：5~10个核心名词，数组；
3.persons人物/机构：新闻明确出现主体，无则空数组；
4.locations省市地点：无则空数组；
5.times明确事发/发布时间，无则空数组。
固定输出JSON结构，不允许增减字段：
{
"summary":"",
"keywords":[],
"persons":[],
"locations":[],
"times":[]
新闻材料：
"""
    full_prompt = prompt + news_merge_text[:TOTAL_INPUT_LIMIT]
    return full_prompt

# 带重试DeepSeek调用
@retry(stop=stop_after_attempt(RETRY_TIMES), wait=wait_fixed(RETRY_WAIT))
def call_llm_extract(prompt_text: str):
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt_text}],
        temperature=LLM_TEMP,
        max_tokens=LLM_MAX_TOKENS
    )
    output_raw = resp.choices[0].message.content
    parse_result = safe_parse_json(output_raw)
    return parse_result
++
# 加载数据表（仅读取必要列）
def load_base_data():
    logger.info("开始加载原始数据表...")
    df_event = pd.read_csv(
        EVENT_TABLE_RAW,
        usecols=["event_id", "event_title", "category", "news_count", "hot_score",
                 "start_time", "end_time", "positive_ratio", "negative_ratio", "neutral_ratio"],
        encoding="utf-8-sig"
    )
    df_cluster = pd.read_csv(
        CLUSTER_MAPPING,
        usecols=["news_id", "event_id"],
        encoding="utf-8-sig"
    )
    # 新闻表增加source字段用于统计平台分布
    df_news = pd.read_csv(
        NEWS_DATA_CSV,
        usecols=["news_id", "title", "content", "publish_time", "source"],
        encoding="utf-8-sig"
    )
    df_relation = pd.merge(df_cluster, df_news, left_on="news_id", right_on="news_id", how="inner")
    logger.info(f"事件总数：{len(df_event)}；新闻关联记录：{len(df_relation)}")
    return df_event, df_relation

# 拼接单事件新闻文本送入LLM
def merge_event_news_text(event_news_df):
    news_slice = event_news_df.head(MAX_EVENT_NEWS)
    merge_text = ""
    for _, row in news_slice.iterrows():
        title = row["title"]
        pub_time = row["publish_time"]
        content = str(row["content"])[:SINGLE_CONTENT_CUT]
        block = f"""
【新闻标题】{title}
【发布时间】{pub_time}
【正文片段】{content}
------------------------
"""
        merge_text += block
    return merge_text

# 新增：计算事件平台分布
def calc_source_dist(event_news_df):
    """输入事件全部新闻，输出各平台数量、占比列表"""
    total = len(event_news_df)
    source_counter = Counter(event_news_df["source"].tolist())
    dist_list = []
    for source, cnt in source_counter.items():
        ratio = round(cnt / total, 4)
        dist_list.append({
            "source": source,
            "news_num": cnt,
            "ratio": ratio
        })
    # 按新闻数量降序排序
    dist_list.sort(key=lambda x: x["news_num"], reverse=True)
    return dist_list

# 主执行全量抽取
def run_extract_pipeline():
    # 文件校验
    check_files = [EVENT_TABLE_RAW, CLUSTER_MAPPING, NEWS_DATA_CSV]
    for fp in check_files:
        if not os.path.exists(fp):
            logger.error(f"缺失文件：{fp}，程序终止")
            raise FileNotFoundError(fp)

    df_event, df_relation = load_base_data()
    result_list = []
    total_task = len(df_event)

    logger.info("开始全量处理所有事件，无增量跳过逻辑")
    for _, row in tqdm(df_event.iterrows(), total=total_task, desc="处理进度"):
        eid = row["event_id"]
        logger.info(f"当前处理 event_id = {eid}")
        sub_news = df_relation[df_relation["event_id"] == eid]

        # 1. 计算平台分布（所有新闻参与统计，不限制Top5）
        source_dist = calc_source_dist(sub_news)
        source_json = json.dumps(source_dist, ensure_ascii=False)

        # 2. LLM抽取分支
        if len(sub_news) == 0:
            logger.warning(f"event_id={eid} 无关联新闻，填充空LLM数据")
            llm_data = {
                "summary": "",
                "keywords": [],
                "persons": [],
                "locations": [],
                "times": []
            }
        else:
            input_text = merge_event_news_text(sub_news)
            prompt = build_extract_prompt(input_text)
            try:
                llm_data = call_llm_extract(prompt)
                logger.info(f"event_id={eid} LLM抽取成功")
            except Exception as err:
                logger.error(f"event_id={eid} 调用DeepSeek全部重试失败：{str(err)}")
                llm_data = {"summary": "", "keywords": [], "persons": [], "locations": [], "times": []}
            time.sleep(0.15) # API限流缓冲

        # 组装单行结果
        res_item = {
            "event_id": eid,
            "event_summary": llm_data["summary"],
            "event_keywords": json.dumps(llm_data["keywords"], ensure_ascii=False),
            "event_persons": json.dumps(llm_data["persons"], ensure_ascii=False),
            "event_locations": json.dumps(llm_data["locations"], ensure_ascii=False),
            "event_times": json.dumps(llm_data["times"]),
            "source_distribution_json": source_json
        }
        result_list.append(res_item)

    # 合并原始事件表与抽取结果
    df_ext = pd.DataFrame(result_list)
    df_final = pd.merge(df_event, df_ext, on="event_id", how="left")
    df_final.to_csv(OUTPUT_FULL, index=False, encoding="utf-8-sig")
    logger.info(f"全部处理完成！输出文件：{OUTPUT_FULL}")
    logger.info(f"输出总记录数：{len(df_final)}")

if __name__ == "__main__":
    import pandas
    run_extract_pipeline()
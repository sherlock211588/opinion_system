import pandas as pd
import re
from tqdm import tqdm
from opencc import OpenCC
import os

# ==============================
# 文件路径配置
# ==============================
INPUT_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data.csv"
OUTPUT_PATH = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn.csv"

# ==============================
# 读取原始数据
# ==============================
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
print("==============================")
print("原始数据总量:", len(df))
print("原始字段列表:", df.columns.tolist())

# 核心：复制time字段，新建publish_time，全程保留
df["publish_time"] = df["time"].copy()
print("复制publish_time完成，当前字段：", df.columns.tolist())

tqdm.pandas()

# ==============================
# 1. 繁体统一转换简体
# ==============================
converter = OpenCC("t2s")

def convert_simple(text):
    if pd.isna(text):
        return ""
    return converter.convert(str(text))

print("\n[1] 执行繁转简")
df["title"] = df["title"].progress_apply(convert_simple)
df["text"] = df["text"].progress_apply(convert_simple)

# ==============================
# 2. 清除标题/正文末尾来源后缀
# ==============================
def clean_source(text):
    if pd.isna(text):
        return ""
    text = str(text)
    pattern = (
        r"\s*[-—|｜]\s*"
        r"(腾讯新闻|新浪新闻|网易新闻|网易|凤凰网|人民网|新华网|央视新闻|澎湃新闻|"
        r"thepaper\.cn|[\w]+\.chinanews\.cn|chinanews\.cn|[\w\.-]+\.(com|cn|net))"
        r".*$"
    )
    text = re.sub(pattern, "", text, flags=re.I)
    return text.strip()

print("\n[2] 清理新闻来源后缀")
df["title"] = df["title"].progress_apply(clean_source)
df["text"] = df["text"].progress_apply(clean_source)

# ==============================
# 3. 清除网页Cookie、链接、相关推荐等噪声
# ==============================
def clean_web_noise(text):
    text = str(text)
    patterns = [
        r"If you click.*", r"Accept all.*", r"We and our partners.*",
        r"cookie.*", r"privacy.*", r"consent.*",
        r"<[^>]*>", r"https?://\S+",
        r"相关阅读.*", r"相关推荐.*", r"热门新闻.*",
        r"更多推荐.*", r"上一篇.*", r"下一篇.*"
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.I)
    return text.strip()

print("\n[3] 清理网页广告噪声")
df["title"] = df["title"].progress_apply(clean_web_noise)
df["text"] = df["text"].progress_apply(clean_web_noise)

# ==============================
# 4. 过滤日文占比过高新闻
# ==============================
def japanese_ratio(text):
    text = str(text)
    jp_chars = len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff]", text))
    return jp_chars / len(text) if len(text) > 0 else 0

print("\n[4] 过滤日文资讯")
df["jp_ratio"] = (df["title"].fillna("") + df["text"].fillna("")).apply(japanese_ratio)
before_jp = len(df)
df = df[df["jp_ratio"] < 0.01]
df = df.drop(columns=["jp_ratio"])
print("日文过滤：", before_jp, "->", len(df))

# ==============================
# 5. 过滤中文占比过低外文资讯
# ==============================
def chinese_ratio(text):
    text = str(text)
    cn = len(re.findall(r"[\u4e00-\u9fff]", text))
    total = len(re.findall(r"[A-Za-z\u4e00-\u9fff]", text))
    return cn / total if total else 0

print("\n[5] 低中文占比资讯过滤")
df["cn_ratio"] = (df["title"].fillna("") + df["text"]).apply(chinese_ratio)
before_cn = len(df)
df = df[df["cn_ratio"] >= 0.2]
df = df.drop(columns=["cn_ratio"])
print("外文过滤：", before_cn, "->", len(df))

# ==============================
# 6. 固定黑名单文本清除
# ==============================
def clean_black_keyword(text):
    text = str(text)
    blacklist = [
        "International Journal of", "Journal of Nanomedicine",
        "Abstract", "Keywords", "Pica Pica Café", "Google",
        "[+", "chars]", "[FTNN]", "[Newtalk]", "©", "All rights reserved"
    ]
    for word in blacklist:
        text = text.replace(word, "")
    return text.strip()

print("\n[6] 清除固定垃圾文本")
df["title"] = df["title"].progress_apply(clean_black_keyword)
df["text"] = df["text"].progress_apply(clean_black_keyword)

# ==============================
# 7. 清理超长数字、密集数字符号乱码
# ==============================
def clean_number_noise(text):
    text = str(text)
    text = re.sub(r"\d{10,}", "", text)
    text = re.sub(r"[\d\(\)%]{12,}", "", text)
    text = re.sub(r"%{3,}", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

print("\n[7] 清理超长数字串")
df["title"] = df["title"].progress_apply(clean_number_noise)
df["text"] = df["text"].progress_apply(clean_number_noise)

# ==============================
# 8. 截断文末连续纯英文段
# ==============================
def clean_tail_noise(text):
    text = str(text)
    words = text.split()
    cut_index = len(words)
    pure_eng_count = 0
    for i in range(len(words)-1, -1, -1):
        word = words[i]
        if not re.search(r"[\u4e00-\u9fff]", word):
            pure_eng_count += 1
        else:
            break
        if pure_eng_count >= 8:
            cut_index = i
            break
    return " ".join(words[:cut_index]).strip()

print("\n[8] 截断文末大段纯英文")
df["text"] = df["text"].progress_apply(clean_tail_noise)

# ==============================
# 【兜底清洗函数：只删尾部无汉字乱码，不删中间正文】
# ==============================
def clean_tail_mess(text):
    if pd.isna(text):
        return ""

    s = str(text).strip()
    if not s:
        return ""

    chinese_matches = list(re.finditer(r'[\u4e00-\u9fff]', s))
    if not chinese_matches:
        return s

    last_chinese_end = chinese_matches[-1].end()
    tail_part = s[last_chinese_end:]

    # 完全沿用你定义的尾部允许字符集合
    pattern = r'^[a-zA-Z0-9\s，。！？；：“”‘’「」『』（）()【】《》…\.\-—、,%&+=~_/!?;:]+'
    tail_match = re.match(pattern, tail_part)

    if tail_match:
        tail = tail_match.group()
        # 匹配所有句末终止标记：中文标点 / 连续英文点省略号
        end_marks = list(re.finditer(r'[。！？!?…]+|\.{2,}', tail))
        if end_marks:
            # 核心改动：只保留【第一个出现的终止符】，其后全部丢弃
            cut_pos = end_marks[0].end()
            tail = tail[:cut_pos]
            # 清除终止符前多余顿号逗号
            tail = re.sub(r'[，、；：]+(?=[。！？!?…\.])', '', tail)
            s = s[:last_chinese_end] + tail
        else:
            # 无任何句末终止符，舍弃全部尾部内容
            s = s[:last_chinese_end]
    else:
        s = s[:last_chinese_end]

    # 统一压缩重复标点，美化输出
    s = re.sub(r'[。…]{2,}', '…', s)
    s = re.sub(r'[!]{2,}', '!', s)
    s = re.sub(r'[?]{2,}', '?', s)
    s = re.sub(r'\.{3,}', '...', s)

    return s.rstrip()
print("\n[9] 精准清除尾部零散数字/英文乱码")
df["text"] = df["text"].progress_apply(clean_tail_mess)

# ==============================
# 10. 过滤文本过短无效数据
# ==============================
df["text"] = df["text"].fillna("")
before_len = len(df)
df = df[df["text"].str.len() > 20]
print("短文本过滤：", before_len, "->", len(df))

# ==============================
# 11. 拼接模型输入content字段
# ==============================
print("\n[10] 拼接模型输入content")
df["content"] = "标题：" + df["title"].fillna("") + "。正文：" + df["text"]

# ==============================
# 12. 生成自增唯一新闻编号news_id
# ==============================
print("\n[11] 生成news_id")
df.insert(0, "news_id", [f"NEWS_{i:06d}" for i in range(1, len(df)+1)])

# ==============================
# 13. 输出字段固定顺序
# ==============================
output_cols = [
    "news_id",
    "title",
    "text",
    "content",
    "url",
    "source",
    "publish_time"
]
df_output = df[output_cols].copy()

print("\n输出字段列表：", df_output.columns.tolist())
print("\n前3行预览：")
print(df_output.head(3))

# ==============================
# 保存文件（修复try-except语法）
# ==============================
try:
    df_output.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n 完成，输出文件：{OUTPUT_PATH}")
except PermissionError:
    new_file = OUTPUT_PATH.replace(".csv", "_new_output.csv")
    df_output.to_csv(new_file, index=False, encoding="utf-8-sig")
    print(f"\n 原文件被占用，另存新文件：{new_file}")
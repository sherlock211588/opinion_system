"""
第三步：数据清洗与预处理（完整版）
修改说明：
1. 时间异常不删除，标记为"未知时间"
2. 所有删除原因都记录到 stats 和日志
3. 过短文本不删除，单独导出
4. SimHash 默认关闭（舆情需要保留多源报道）
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import logging
import json
import numpy as np
from datetime import datetime

from config import (
    OUTPUT_DIR, LOG_DIR, STOPWORDS_DIR, REPORT_DIR,
    MIN_TEXT_LENGTH, USE_SIMHASH, SIMHASH_THRESHOLD,
    ENABLE_PROGRESS_BAR
)
from utils.cleaners import clean_all, clean_title
from utils.deduplicators import deduplicate
from utils.tokenizers import EnhancedTokenizer
from utils.validators import validate_dataframe, assert_data_quality
from utils.progress import process_with_progress

# ==========================================
# 配置日志
# ==========================================
LOG_FILE = LOG_DIR / '03_clean_deduplicate.log'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def log_info(msg):
    print(msg)
    logging.info(msg)

print("=" * 60)
print("[第三步] 数据清洗与预处理（完整版）")
print("=" * 60)

# ==========================================
# 1. 加载数据
# ==========================================
input_file = OUTPUT_DIR / 'extracted_data.csv'
if not input_file.exists():
    log_info(f"[ERROR] 找不到文件: {input_file}")
    sys.exit(1)

try:
    df = pd.read_csv(
        input_file,
        encoding='utf-8-sig',
        engine='python',
        on_bad_lines='skip',
        quoting=1
    )
except Exception as e:
    log_info(f"[ERROR] 读取 CSV 失败: {e}")
    sys.exit(1)

log_info(f"[DATA] 共加载 {len(df)} 条数据")

# ==========================================
# 2. 初始化统计字典（完整记录所有删除原因）
# ==========================================
stats = {
    "原始数据": len(df),
    "删除空正文": 0,
    "URL去重删除": 0,
    "标题+正文完全重复删除": 0,
    "无效时间标记为未知": 0,      # 时间异常不删除，只标记
    "标题清洗后为空删除": 0,
    "过滤非简体中文/噪声删除": 0,
    "过短文本数量": 0,             # 不删除，只统计
    "SimHash近重复删除": 0,
    "清洗后保留": 0,
}

# ==========================================
# 3. 确保有 'title' 列
# ==========================================
if 'title' not in df.columns:
    df['title'] = df['extracted_body'].fillna('').str[:20] + '...'
    log_info("[INFO] 数据中没有 'title' 字段，已从正文前20字符自动生成")

# ==========================================
# 4. 删除完全空数据（空正文）
# ==========================================
before = len(df)
df = df.dropna(subset=['extracted_body'])
df = df[df['extracted_body'].str.strip() != '']
stats['删除空正文'] = before - len(df)
log_info(f"[OK] 删除空正文: {stats['删除空正文']} 条")

# ==========================================
# 5. URL 去重
# ==========================================
if 'url' in df.columns:
    before = len(df)
    df = df.drop_duplicates(subset=['url'], keep='first')
    stats['URL去重删除'] = before - len(df)
    log_info(f"[OK] URL去重: {stats['URL去重删除']} 条")
else:
    log_info("[WARN] 没有 'url' 字段，跳过 URL 去重")

# ==========================================
# 6. title + text 完全一样 → 删除
# ==========================================
text_col = 'text' if 'text' in df.columns else 'extracted_body'
if 'title' in df.columns and text_col in df.columns:
    before = len(df)
    df = df.drop_duplicates(subset=['title', text_col], keep='first')
    stats['标题+正文完全重复删除'] = before - len(df)
    log_info(f"[OK] 标题+正文完全相同去重: {stats['标题+正文完全重复删除']} 条")

# ==========================================
# 7. 时间处理（修复：不删除，只标记为"未知时间"）
# ==========================================
time_fields = ['publish_time', 'time', 'pubtime', 'pub_date', 'date', 'timestamp']
found_time = None
for tf in time_fields:
    if tf in df.columns:
        found_time = tf
        break

if found_time:
    before = len(df)
    df[found_time] = pd.to_datetime(df[found_time], errors='coerce')
    stats['无效时间标记为未知'] = df[found_time].isna().sum()
    # 格式化并填充为"未知时间"
    df[found_time] = df[found_time].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('未知时间')
    df.rename(columns={found_time: 'publish_time'}, inplace=True)
    log_info(f"[OK] 时间字段已标准化，{stats['无效时间标记为未知']} 条标记为'未知时间'（未删除）")
else:
    log_info("[WARN] 未找到时间字段")
    df['publish_time'] = '未知时间'
    stats['无效时间标记为未知'] = len(df)

# ==========================================
# 8. 标题清洗
# ==========================================
log_info("[PROCESS] 执行标题清洗...")
if 'title' in df.columns:
    before_title = len(df)
    df['title'] = df['title'].apply(clean_title)
    df = df[df['title'].str.strip() != '']
    stats['标题清洗后为空删除'] = before_title - len(df)
    log_info(f"[OK] 标题清洗完成，删除 {stats['标题清洗后为空删除']} 条空标题记录")

# ==========================================
# 9. 综合清洗（简体中文过滤 + 数字噪声过滤）
# ==========================================
log_info("[PROCESS] 执行综合清洗（简体中文过滤 + 数字噪声过滤）...")
before_clean = len(df)

if ENABLE_PROGRESS_BAR:
    results = process_with_progress(
        df['extracted_body'].tolist(),
        clean_all,
        desc="清洗文本"
    )
    df['cleaned_body'] = results
else:
    df['cleaned_body'] = df['extracted_body'].apply(clean_all)

empty_after = df['cleaned_body'].isna() | (df['cleaned_body'] == '')
stats['过滤非简体中文/噪声删除'] = empty_after.sum()
log_info(f"[OK] 过滤非简体中文/数字噪声: {stats['过滤非简体中文/噪声删除']} 条")

df = df[~empty_after]
log_info(f"[OK] 过滤后剩余: {len(df)} 条")

# ==========================================
# 10. 过短文本（修复：不删除，只统计和标记）
# ==========================================
short_mask = df['cleaned_body'].str.len() < MIN_TEXT_LENGTH
stats['过短文本数量'] = short_mask.sum()
log_info(f"[OK] 过短文本: {stats['过短文本数量']} 条（已保留，标记为 is_short_text）")

if stats['过短文本数量'] > 0:
    low_quality_df = df[short_mask].copy()
    low_quality_path = OUTPUT_DIR / 'low_quality_data.json'
    low_quality_df.to_json(low_quality_path, orient='records', force_ascii=False, indent=2)
    log_info(f"[OK] 过短数据已单独保存至: {low_quality_path}")
    df['is_short_text'] = short_mask
else:
    df['is_short_text'] = False

# ==========================================
# 11. 数据质量验证
# ==========================================
try:
    assert_data_quality(df, 'cleaned_body', min_length=1)
    log_info("[OK] 数据质量验证通过")
except ValueError as e:
    log_info(f"[ERROR] 数据质量验证失败: {e}")
    sys.exit(1)

# ==========================================
# 12. SimHash 近重复检测（默认关闭，舆情需要保留多源报道）
# ==========================================
if USE_SIMHASH:
    before = len(df)
    df = deduplicate(df, 'cleaned_body', use_simhash=True, threshold=SIMHASH_THRESHOLD)
    stats['SimHash近重复删除'] = before - len(df)
    log_info(f"[OK] SimHash 近重复检测删除: {stats['SimHash近重复删除']} 条")
else:
    stats['SimHash近重复删除'] = 0
    log_info("[INFO] SimHash 近重复检测已关闭（保留多源报道）")

# ==========================================
# 13. 加载停用词
# ==========================================
stopwords = set()
stopwords_file = STOPWORDS_DIR / 'hit_stopwords.txt'
if stopwords_file.exists():
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        stopwords = set(f.read().splitlines())
    log_info(f"[OK] 加载 {len(stopwords)} 个停用词")

extra_file = STOPWORDS_DIR / 'extra_stopwords.txt'
if extra_file.exists():
    with open(extra_file, 'r', encoding='utf-8') as f:
        extra = set(f.read().splitlines())
        stopwords.update(extra)
        log_info(f"[OK] 扩展停用词 {len(extra)} 个，总计 {len(stopwords)} 个")

# ==========================================
# 14. 分词
# ==========================================
user_dict = STOPWORDS_DIR / 'user_dict.txt'
tokenizer = EnhancedTokenizer(stopwords, user_dict)

log_info("[PROCESS] 开始分词...")
if ENABLE_PROGRESS_BAR:
    seg_results = process_with_progress(
        df['cleaned_body'].tolist(),
        lambda x: ' '.join(tokenizer.segment(x, pos_filter=False)),
        desc="分词"
    )
    df['segmented'] = seg_results
else:
    df['segmented'] = df['cleaned_body'].apply(
        lambda x: ' '.join(tokenizer.segment(x, pos_filter=False))
    )

df['word_count'] = df['segmented'].str.split().str.len()
log_info(f"[OK] 平均词数: {df['word_count'].mean():.1f}")

# ==========================================
# 15. 保存结果
# ==========================================
stats['清洗后保留'] = len(df)

# 完整版
output_file = OUTPUT_DIR / 'cleaned_data.csv'
df.to_csv(output_file, index=False, encoding='utf-8-sig')
log_info(f"[OK] 完整版清洗数据已保存至: {output_file}")

# 精简版 final_data.csv
final_cols = ['id', 'title', 'cleaned_body', 'url', 'publish_time', 'source']
available_cols = [c for c in final_cols if c in df.columns]
if len(available_cols) == len(final_cols):
    final_df = df[final_cols].copy()
    final_df.columns = ['id', 'title', 'text', 'url', 'time', 'source']
    final_output = OUTPUT_DIR / 'final_data.csv'
    final_df.to_csv(final_output, index=False, encoding='utf-8-sig')
    log_info(f"[OK] 精简版最终数据已保存至: {final_output}")
else:
    log_info(f"[WARN] 精简版导出失败，缺少列: {set(final_cols) - set(df.columns)}")

# ==========================================
# 16. 生成清洗报告
# ==========================================
def convert_to_serializable(obj):
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    else:
        return obj

stats_serializable = {k: convert_to_serializable(v) for k, v in stats.items()}

report_path = OUTPUT_DIR / 'clean_report.json'
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(stats_serializable, f, ensure_ascii=False, indent=2)
log_info(f"[OK] 清洗报告已生成: {report_path}")

# ==========================================
# 17. 最终统计（完整展示所有删除原因）
# ==========================================
print("\n" + "=" * 60)
print("[清洗报告摘要]")
print("=" * 60)
print(f"  原始数据: {stats['原始数据']} 条")
print(f"  ─── 删除原因 ───")
print(f"  删除空正文: {stats['删除空正文']} 条")
print(f"  URL去重删除: {stats['URL去重删除']} 条")
print(f"  标题+正文完全重复删除: {stats['标题+正文完全重复删除']} 条")
print(f"  标题清洗后为空删除: {stats['标题清洗后为空删除']} 条")
print(f"  过滤非简体中文/噪声删除: {stats['过滤非简体中文/噪声删除']} 条")
if stats.get('SimHash近重复删除', 0) > 0:
    print(f"  SimHash近重复删除: {stats['SimHash近重复删除']} 条")
print(f"  ─── 保留但标记 ───")
print(f"  无效时间（已标记为'未知时间'）: {stats['无效时间标记为未知']} 条")
print(f"  过短文本（已保留，标记为 is_short_text）: {stats['过短文本数量']} 条")
print(f"  ─── 最终结果 ───")
print(f"  清洗后保留: {stats['清洗后保留']} 条")
print(f"  总删除率: {(1 - stats['清洗后保留'] / stats['原始数据']) * 100:.1f}%")
print("=" * 60)

print("\n[SUCCESS] 03_clean_deduplicate.py 执行完成！")

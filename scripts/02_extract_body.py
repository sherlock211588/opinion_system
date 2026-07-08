"""
第二步：网页正文内容提取（去除HTML标签）
从 01 加载的真实数据中提取正文
"""

import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from readability import Document
import re

# ==========================================
# 1. 定位项目根目录和文件路径
# ==========================================
project_root = Path(__file__).parent.parent

# 读取 01 加载的真实数据（而不是测试数据）
input_file = project_root / 'output' / 'loaded_data.csv'
output_file_path = project_root / 'output' / 'extracted_data.csv'

print("=" * 60)
print("[第二步] 网页正文内容提取（去除HTML标签）")
print("=" * 60)

# ==========================================
# 2. 加载真实数据
# ==========================================
print(f"[INFO] 正在读取: {input_file}")

if not input_file.exists():
    print(f"[ERROR] 找不到文件: {input_file}")
    print("请先运行 01_load_data.py")
    exit()

df = pd.read_csv(input_file, encoding='utf-8-sig')
print(f"[DATA] 共加载 {len(df)} 条原始记录")

# ==========================================
# 3. 检查是否有 html_content 字段
# ==========================================
if 'html_content' not in df.columns:
    print("[WARN] 数据中没有 'html_content' 字段！")
    print(f"[INFO] 当前字段: {df.columns.tolist()}")
    
    # 如果有 'text' 字段，映射为 html_content
    if 'text' in df.columns:
        df['html_content'] = df['text']
        print("[INFO] 已将 'text' 字段映射为 'html_content'（但效果可能不如HTML源码好）")
    else:
        print("[ERROR] 没有可用的内容字段，请让1号提供 'html_content' 或 'text' 字段")
        exit()

# ==========================================
# 4. 定义正文提取函数
# ==========================================
def extract_article_body(html_content, url=''):
    if not html_content or not isinstance(html_content, str):
        return {'title': '', 'body': ''}
    
    try:
        doc = Document(html_content, url=url)
        title = doc.title() or ''
        article_html = doc.summary()
        soup = BeautifulSoup(article_html, 'lxml')
        body_text = soup.get_text()
        body_text = re.sub(r'\s+', ' ', body_text).strip()
        return {'title': title, 'body': body_text}
    except Exception as e:
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            return {'title': '', 'body': text}
        except:
            return {'title': '', 'body': ''}

# ==========================================
# 5. 执行正文提取
# ==========================================
print("\n[PROCESS] 开始提取正文...")

# 记录原始HTML长度
df['html_length'] = df['html_content'].str.len()

# 应用提取函数
extracted = df['html_content'].apply(lambda html: extract_article_body(html, url=''))
df['extracted_title'] = extracted.apply(lambda x: x['title'])
df['extracted_body'] = extracted.apply(lambda x: x['body'])
df['body_length'] = df['extracted_body'].str.len()

# ==========================================
# 6. 打印效果预览
# ==========================================
print("\n[提取效果预览]")
for index, row in df.head(3).iterrows():
    print(f"\n--- 第 {index+1} 条: {row.get('title', '无标题')[:30]} ---")
    print(f"  原始HTML长度: {row['html_length']} 字符")
    print(f"  提取后正文长度: {row['body_length']} 字符")
    preview = row['extracted_body'][:60] + "..." if len(row['extracted_body']) > 60 else row['extracted_body']
    print(f"  正文预览: {preview}")

# ==========================================
# 7. 保存结果
# ==========================================
output_file_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_file_path, index=False, encoding='utf-8-sig')

success_count = df[df['body_length'] > 10].shape[0]
print(f"\n[OK] 提取完成！结果已保存至: {output_file_path}")
print(f"[DATA] 提取成功率: {success_count}/{len(df)} 条 (正文长度 > 10 字符视为成功)")
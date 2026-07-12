import pandas as pd
from dateutil import parser

# 时间格式化函数（兼容你提到的3种格式）
def format_publish_time(time_str):
    if pd.isna(time_str):
        return ""
    s = str(time_str).strip()
    if not s:
        return ""
    try:
        # 自动解析任意标准时间格式
        dt = parser.parse(s)
        # 输出目标格式：年/月/日 时:分:秒（不补前导零）
        return f"{dt.year}/{dt.month}/{dt.day} {dt.hour}:{dt.minute}:{dt.second}"
    except Exception as e:
        # 解析失败时返回原内容，避免数据丢失
        print(f"时间解析失败：{time_str}，错误：{e}")
        return time_str

# CSV文件路径（r原始字符串避免Windows路径转义问题）
file_path = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn.csv"

# 1. 读取CSV文件
try:
    df = pd.read_csv(file_path)
    print(f"成功读取文件，共 {len(df)} 行数据")
except FileNotFoundError:
    print(f"错误：文件不存在，请检查路径是否正确：{file_path}")
    exit()
except Exception as e:
    print(f"读取文件失败：{e}")
    exit()

# 2. 检查publish_time列是否存在
if "publish_time" not in df.columns:
    print("错误：CSV文件中未找到publish_time列，请检查列名是否正确")
    exit()

# 3. 批量处理时间列
df["publish_time"] = df["publish_time"].apply(format_publish_time)
print("publish_time列格式转换完成")

# 4. 保存修改后的文件（另存为新文件，不覆盖原始数据）
output_path = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn_timefmt.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"修改后的文件已保存至：{output_path}")
# test_config.py
import sys
import os

# 当前脚本目录
current_dir = os.path.dirname(__file__)
# 往上两层，定位到根目录 opinion_system_C
root_dir = os.path.abspath(os.path.join(current_dir, "..", "interface"))
sys.path.append(root_dir)

from config import *

def test_config_paths():
    print("=== 路径配置校验 ===")
    print("BASE_DIR:", BASE_DIR)
    print("DATA_DIR:", DATA_DIR)
    print("EVENT_TABLE_PATH:", EVENT_TABLE_PATH)
    print("EVENT_TIMESERIES_PATH:", EVENT_TIMESERIES_PATH)
    print("EVENT_FAISS_INDEX_PATH:", EVENT_FAISS_INDEX_PATH)
    print("NEWS_CLUSTER_PATH:", NEWS_CLUSTER_PATH)
    print("NEWS_CONTENT_PATH:", NEWS_CONTENT_PATH)
    print("NEWS_SENTIMENT_PATH:", NEWS_SENTIMENT_PATH)
    print("MODEL_PATH:", MODEL_PATH)

    import os
    check_files = [
        EVENT_TABLE_PATH,
        EVENT_TIMESERIES_PATH,
        EVENT_FAISS_INDEX_PATH,
        EVENT_MAPPING_PATH,
        NEWS_CLUSTER_PATH,
        NEWS_CONTENT_PATH,
        NEWS_SENTIMENT_PATH
    ]
    all_ok = True
    for fp in check_files:
        exists = os.path.exists(fp)
        print(f" {fp}: 存在" if exists else f" {fp}: 缺失")
        if not exists:
            all_ok = False

    if all_ok:
        print("\n 全部数据文件路径正常！")
    else:
        print("\n 存在缺失文件，请检查config路径配置或文件位置！")

if __name__ == "__main__":
    test_config_paths()
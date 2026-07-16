import pandas as pd
import numpy as np
import faiss

# 配置（相对于脚本所在项目根目录）
import os
_BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_EVENT_TABLE = os.path.join(_BASE, "data", "event_table_final.csv")
OUT_INDEX        = os.path.join(_BASE, "data", "event_faiss.index")
OUT_MAPPING      = os.path.join(_BASE, "data", "event_mapping.csv")

def build_faiss():
    df_event = pd.read_csv(INPUT_EVENT_TABLE)
    vec_list = []
    id_mapping = []

    for idx, row in df_event.iterrows():
        event_id = row["event_id"]
        vec_str = row["center_embedding"]
        vec = np.array([float(x) for x in vec_str.split(",")], dtype=np.float32)
        
       
        # ========== 核心：均值向量重新归一化 ==========
        vec = vec / np.linalg.norm(vec)
        
        vec_list.append(vec)
        id_mapping.append({"faiss_id": idx, "event_id": event_id})

    vec_matrix = np.vstack(vec_list)
    dim = vec_matrix.shape[1]

    # 保持IndexFlatL2，和聚类欧氏距离统一
    index = faiss.IndexFlatL2(dim)
    index.add(vec_matrix)

    faiss.write_index(index, OUT_INDEX)
    print(f"FAISS索引已保存，总事件数：{index.ntotal}")

    df_mapping = pd.DataFrame(id_mapping)
    df_mapping.to_csv(OUT_MAPPING, index=False, encoding="utf-8-sig")
    print(f"ID映射表已保存")

if __name__ == "__main__":
    build_faiss()
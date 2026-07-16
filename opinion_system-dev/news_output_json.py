import pandas as pd
import json
import os

def main():
    # 固定文件绝对路径
    path_cluster = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_event_cluster.csv"
    path_sentiment = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_sentiment.csv"
    path_clean = r"C:\Users\Yolo\Downloads\opinion_system_C\data\cleaned_data_cn.csv"

    # 读取文件
    df_cluster = pd.read_csv(path_cluster)
    df_sentiment = pd.read_csv(path_sentiment)
    df_clean = pd.read_csv(path_clean)

    # 关联三张表
    df_merge = pd.merge(df_clean, df_sentiment, on="news_id", how="left")
    df_final = pd.merge(df_merge, df_cluster, on="news_id", how="left")

    # 组装JSON数据
    output_list = []
    for _, row in df_final.iterrows():
        item = {
            "news_id": row["news_id"],
            "event_id": row["event_id"] if pd.notna(row["event_id"]) else "",
            "title": row["title"],
            "text": row["text"],
            "source": row["source"],
            "publish_time":row["publish_time"],
            "sentiment": row["sentiment"] if pd.notna(row["sentiment"]) else ""
        }
        output_list.append(item)

    # 输出到data目录下 news_output.json
    out_path = r"C:\Users\Yolo\Downloads\opinion_system_C\data\news_output.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_list, f, ensure_ascii=False, indent=4)

    print(f"导出完成，总条数：{len(output_list)}")
    print(f"输出文件：{out_path}")

if __name__ == "__main__":
    main()
# opinion_system_C 舆情分析系统
舆情数据处理、文本情感分析、事件挖掘、相似检索全流程项目

## 整体目录结构
- `/models`：预训练模型存放目录
- `/data`：全量处理数据集、索引文件、结果输出文件
- `/test`：测试脚本/数据目录
- 根目录：核心Python处理脚本、日志文件

---

### 1. /models 模型文件夹
- `yangjiurong/`：自定义/第三方中文NLP模型目录
- `BAAI/`：BAAI系列大模型/嵌入模型（如BGE向量模型）
- `IDEA-CCNL/`：IDEA研究院开源中文大模型（情感/文本抽取模型）
> 用途：存放文本嵌入、情感分析、大语言模型权重，用于语义编码、文本理解、内容抽取
---

### 2. /data 数据文件夹
| 文件名 | 用途说明 |
|---|---|
| cleaned_data.csv / cleaned_data_cn.csv | 原始新闻数据清洗后的基础数据集（中文清洗版本） |
| news_output.json | 原始新闻结构化导出数据 |
| news_embedding.csv | 新闻文本向量嵌入结果，用于语义检索 |
| news_sentiment.csv | 新闻单条情感标签/分值结果 |
| news_event_cluster.csv | 新闻事件聚类结果，划分同类舆情事件 |
| event_table_v1.csv / event_table_final.csv | 舆情事件汇总表（初版/最终版） |
| event_table_llm.csv | LLM大模型抽取后的舆情事件汇总表 |
| event_category.csv | 舆情事件分类标签数据 |
| event_hot_score.csv | 舆情事件热度评分数据 |
| event_sentiment_stat.csv | 舆情情感整体统计结果 |
| event_sentiment_timeline.csv | 舆情情感时序数据（随时间情感变化） |
| event_timeseries_result.json | 舆情时序分析结果JSON文件 |
| event_mapping.csv | 事件ID映射FAISS编号对照文件 |
| event_faiss.index | FAISS向量检索索引文件，用于快速相似事件检索 |

---

### 3. 根目录 Python 脚本文件
| 文件名 | 用途说明 |
|---|---|
| data_preprocess.py | 原始数据基础预处理脚本 |
| data_preprocess_clean.py | 数据清洗、去噪、格式规整脚本 |
| timeformat_change.py | 统一时间字段格式，适配时序分析 |
| download_models.py | 自动下载/加载预训练模型脚本 |
| download_sentiment.py | 情感模型/情感基础数据下载脚本 |
| bge_embedding.py | BGE模型生成文本向量嵌入脚本 |
| news_sentiment_infer.py | 新闻文本情感推理、情感打分脚本 |
| event_category.py | 舆情事件自动分类脚本 |
| event_hot_score.py | 计算舆情事件热度指数脚本 |
| event_sentiment_stat.py | 统计整体舆情情感分布数据脚本 |
| event_sentiment_timeline.py | 生成舆情情感时序变化数据脚本 |
| event_cluster.py | 舆情新闻聚类，聚合同类事件脚本 |
| event_table_v1.py | 生成初版舆情事件汇总表脚本 |
| event_table_final.py | 生成最终版舆情事件汇总表脚本 |
| event_llm_extract.py | 大模型LLM抽取舆情要素（主体、时间、核心信息）脚本 |
| retrieve_similar_event.py | 基于向量索引检索相似舆情事件脚本 |
| build_faiss_index.py | 构建FAISS向量检索索引脚本 |
| news_output_json.py | 新闻数据导出为JSON格式脚本 |
| 1.40 | 辅助配置/参数文件 |

---
### 4. /interface FastAPI接口服务目录（新增模块）
提供前后端交互RESTful接口，内置Swagger在线文档，三层分层设计：路由层(main.py)、业务服务层、全局配置
| 文件 | 用途说明 |
|---|---|
| main.py | FastAPI服务入口，定义全部API路由、请求参数模型、跨域配置 |
| config.py | 全局路径配置，统一管理数据、模型、时序文件路径 |
| event_service.py | 事件核心业务服务：事件列表、单事件详情、多条件筛选、情感/平台分布计算、时序聚合 |
| history_service.py | 历史事件检索中间层，转发筛选参数至EventService |
| news_service.py | 新闻数据服务：根据事件ID批量查询关联新闻 |
| similar_service.py | 相似事件检索服务，加载FAISS向量索引做语义匹配 |

### 已开放核心API接口
1. 事件基础列表
`GET /api/analysis/events`
- 无请求体，返回精简事件列表（不含情感、平台、时序详情）

2. 单事件完整详情
`GET /api/analysis/event/{eid}`
- 路径参数eid：事件唯一ID；返回完整数据：情感分布、平台来源分布、时序曲线、关联新闻

3. 事件关联新闻列表
`GET /api/analysis/event/{eid}/articles`
- 根据事件ID查询全部绑定新闻

4. 历史事件多条件筛选（关键词+分类+起止时间）
`POST /api/history/filter`
- 请求体支持keyword/category/start_time/end_time，任意字段组合筛选
- 示例请求体
```json
{
  "keyword": "山洪",
  "start_time": "2026-07-01",
  "end_time": "2026-07-14"
}

5.相似事件语义检索
`POST /api//similar/search`
- 请求参数：query 检索文本、top_k 返回条数
- 示例请求体
```json
{
  "query": "暴雨山洪灾害",
  "top_k": 5
}

### 5. 日志 & 其他文件
| 文件名 | 用途说明 |
|---|---|
| event_llm_run.log | LLM抽取任务运行日志，用于调试和追溯执行过程 |
| README.md | 本文件，全项目文件用途说明文档 |
| /test | 单元测试、验证脚本目录 |

---

## 整体业务流程
1. 原始新闻数据 → `data_preprocess` / `data_preprocess_clean` 清洗处理
2. BGE嵌入模型生成向量：`bge_embedding.py`
3. 情感分析：`news_sentiment_infer.py` 做情感推理
4. 事件聚类、分类、热度计算、情感时序统计
5. LLM大模型抽取事件要素：`event_llm_extract.py`
6. 构建FAISS索引，实现相似舆情检索
7. 输出结构化csv/json结果，用于可视化/报表

## 使用注意事项
1. `/models` 模型文件可按需下载，勿随意修改模型权重
2. `event_faiss.index` 向量索引与嵌入数据版本保持一致，否则检索异常
3. 原始大体积数据文件可做外部备份，避免占用版本库空间
4. 新增脚本/数据文件请同步更新此README文档
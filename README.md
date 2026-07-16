# 网络舆情事件智能分析系统

> **5人团队课程设计项目** | 全栈舆情监测与分析平台

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com/)
[![Vite](https://img.shields.io/badge/Vite-8.x-purple.svg)](https://vitejs.dev/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-orange.svg)](https://scikit-learn.org/)

---

## 项目简介

本系统从多个信息源（新闻网站、微博、知乎、B站、今日头条、小红书等）采集舆情数据，经数据清洗、NLP语义分析、时序算法建模，实现热点事件自动发现、情感倾向分析、舆情生命周期预测、传播路径溯源、虚假信息检测及跨事件因果分析，最终通过 Web 前端提供可视化看板与智能问答。

### 系统功能全景

```
┌─────────────────────────────────────────────────────────────────────┐
│                     📊 前端可视化 (5号)                               │
│  热点看板 │ 事件详情 │ 传播图谱 │ 情感分析 │ 智能问答 │ 个人中心       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST API (FastAPI :8000 / :8002)
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
┌──────▼──────┐   ┌───────────▼──────────┐   ┌───────▼───────┐
│  3号 NLP    │   │  4号 时序算法+后端    │   │  5号 前端     │
│  语义分析   │   │  生命周期 · 传播溯源   │   │  Vue 3 +     │
│  事件聚合   │   │  虚假检测 · 跨事件因果 │   │  ECharts     │
│  情感计算   │   │  JWT认证 · AI问答     │   │  可视化      │
└──────▲──────┘   └───────────▲──────────┘   └───────────────┘
       │                       │
       │     ┌─────────────────┘
       │     │
┌──────┴─────┴┐
│   2号 预处理  │
│   18项清洗    │
│   中文分词    │
│   TF-IDF     │
└──────▲───────┘
       │
┌──────┴───────┐
│   1号 爬虫    │
│   11+平台     │
│   多源采集    │
└──────────────┘
```

---

## 团队分工

| 成员 | 角色 | 核心职责 | 技术栈 |
|:---:|------|------|------|
| **1号** | 爬虫工程师 | 11+平台数据采集、反爬处理、传播链构建、多源统一入库 | Python, requests, BS4, feedparser |
| **2号** | 数据预处理工程师 | 18项数据清洗、网页正文抽取、中文分词、TF-IDF特征提取 | Python, jieba, readability-lxml, OpenCC, SnowNLP |
| **3号** | NLP语义分析工程师 | 事件聚类/分类、情感分析、BGE向量嵌入、FAISS语义检索、LLM要素抽取 | Python, BGE, FAISS, scikit-learn, Transformers |
| **4号** | 时序算法工程师 | 生命周期预测、传播溯源、虚假检测、跨事件因果、JWT认证、AI问答后端 | Python, FastAPI, networkx, ruptures, scikit-learn |
| **5号** | 全栈整合/前端开发 | Vue 3 SPA、ECharts可视化、前后端联调、系统集成 | Vue 3, Vite, ECharts, Element Plus, Pinia |

---

## 项目结构

```
aaasystem/
├── opinion_system-feature-crawler-data/   # 1号 — 爬虫模块
│   ├── crawler/                           #   爬虫核心
│   │   ├── main.py                        #     总入口 (CLI)
│   │   ├── config.py                      #     全局配置
│   │   ├── http_client.py                 #     请求/重试
│   │   ├── save_data.py                   #     去重/保存
│   │   ├── search_fallback.py             #     公开搜索兜底
│   │   ├── news_crawler.py                #     新闻/GDELT
│   │   ├── bilibili_crawler.py            #     B站
│   │   ├── weibo_crawler.py               #     微博
│   │   ├── zhihu_crawler.py               #     知乎
│   │   ├── toutiao_crawler.py             #     今日头条
│   │   ├── xiaohongshu_crawler.py         #     小红书
│   │   ├── newsapi_crawler.py             #     NewsAPI
│   │   ├── currents_crawler.py            #     Currents API
│   │   ├── mediacloud_crawler.py          #     MediaCloud
│   │   ├── rss_news_crawler.py            #     RSS
│   │   ├── site_news_crawler.py           #     站点直采
│   │   ├── propagation_crawler.py         #     传播链构建
│   │   ├── propagation_batch.py           #     传播批量采集
│   │   └── check_output.py                #     输出校验
│   ├── crawlerall/                        #   旧版爬虫代码
│   ├── data/                              #   采集数据
│   ├── requirements.txt
│   └── .env.example
│
├── opinion_system-2-preprocess/           # 2号 — 数据预处理模块
│   ├── scripts/                           #   可执行脚本
│   │   ├── run_all.py                     #     一键运行入口
│   │   ├── 01_load_data.py                #     数据加载
│   │   ├── 02_extract_body.py             #     正文抽取
│   │   ├── 03_clean_deduplicate.py        #     清洗去重 (18项)
│   │   ├── 04_segment.py                  #     中文分词
│   │   ├── 05_feature_extract.py          #     TF-IDF 特征
│   │   ├── 06_generate_report.py          #     质量报告
│   │   └── 07_advanced_analysis.py        #     情感/摘要/实体
│   ├── utils/                             #   工具函数库
│   │   ├── cleaners.py                    #     18项清洗函数
│   │   ├── deduplicators.py               #     MD5 + SimHash
│   │   ├── tokenizers.py                  #     分词增强
│   │   ├── reporters.py                   #     报告生成
│   │   ├── validators.py                  #     数据验证
│   │   ├── progress.py                    #     进度条
│   │   └── logger.py                      #     日志配置
│   ├── stopwords/                         #   停用词与自定义词典
│   ├── config.py                          #   全局配置
│   ├── PROJECT_STRUCTURE.md               #   详细结构文档
│   └── requirements.txt
│
├── opinion_system-dev/                    # 3号 — NLP语义分析模块
│   ├── data_preprocess.py                 #   数据清洗
│   ├── data_preprocess_clean.py           #   深度清洗
│   ├── timeformat_change.py               #   时间格式标准化
│   ├── bge_embedding.py                   #   BGE 文本向量嵌入
│   ├── build_faiss_index.py               #   FAISS 向量索引
│   ├── news_sentiment_infer.py            #   情感推理
│   ├── event_cluster.py                   #   事件聚类
│   ├── event_category.py                  #   事件分类
│   ├── event_hot_score.py                 #   热度计算
│   ├── event_sentiment_stat.py            #   情感统计
│   ├── event_sentiment_timeline.py        #   情感时序
│   ├── event_table_v1.py / event_table_final.py  # 事件汇总表
│   ├── event_llm_extract.py               #   LLM 事件要素抽取
│   ├── retrieve_similar_event.py          #   相似事件检索
│   ├── event_semantic_search.py           #   语义搜索
│   ├── download_models.py                 #   模型下载
│   ├── interface/                         #   FastAPI 服务 (Port 8000)
│   │   ├── main.py                        #     API 路由入口
│   │   ├── config.py                      #     路径配置
│   │   ├── event_service.py               #     事件服务
│   │   ├── news_service.py                #     新闻服务
│   │   ├── history_service.py             #     历史筛选
│   │   └── similar_service.py             #     相似检索
│   ├── models/                            #   预训练模型
│   ├── data/                              #   数据文件
│   └── README.md
│
├── 4_time/                                # 4号 — 时序算法 + 后端API
│   ├── time_series/                       #   核心算法库
│   │   ├── pipeline.py                    #     统一报表接口
│   │   ├── cross_event.py                 #     跨事件因果分析
│   │   ├── report_generator.py            #     智能报告 + LLM问答
│   │   ├── lifecycle/                     #     模块1: 生命周期预测
│   │   │   ├── detector.py                #       主检测器
│   │   │   ├── stage.py                   #       阶段判定
│   │   │   ├── fusion.py                  #       多信号融合
│   │   │   ├── forecast.py                #       Holt 预测
│   │   │   ├── changepoint.py             #       PELT 变点
│   │   │   ├── resurgence.py              #       二次爆发
│   │   │   └── critical.py                #       临界减速预警
│   │   ├── propagation/                   #     模块2: 传播溯源
│   │   │   └── tracer.py                  #       PageRank + 反事实
│   │   ├── fake_detection/                #     模块3: 虚假检测
│   │   │   ├── __init__.py                #       FakeDetector
│   │   │   ├── ced_loader.py              #       CED数据集
│   │   │   ├── chef_loader.py             #       CHEF数据集
│   │   │   └── graph_features.py          #       拓扑特征
│   │   └── utils/mock_data.py             #     模拟数据生成
│   ├── app/                               #   FastAPI 服务层
│   │   ├── database.py                    #     SQLite 数据库
│   │   ├── models.py                      #     用户模型
│   │   ├── schemas.py                     #     Pydantic 模型
│   │   ├── security.py                    #     JWT + bcrypt
│   │   └── routers/
│   │       ├── auth.py                    #     用户认证路由
│   │       └── ai.py                      #     AI 问答路由
│   ├── server.py                          #   API 主入口 (Port 8002)
│   ├── demo.py                            #   一键演示
│   ├── run_real_data.py                   #   真实数据运行
│   ├── run_full_3data.py                  #   全流程运行
│   ├── docs/                              #   需求文档 & 设计报告
│   ├── data/                              #   数据集 (CED/CHEF)
│   ├── requirements.txt
│   └── .env
│
└── opinion_system-frontend/               # 5号 — 前端可视化
    └── frontend/
        ├── src/
        │   ├── main.js                    #   Vue 应用入口
        │   ├── App.vue                    #   根组件
        │   ├── router/index.js            #   路由配置
        │   ├── api/                       #   API 请求层
        │   │   ├── request.js             #     Axios + JWT
        │   │   ├── events.js              #     事件数据归一化
        │   │   ├── auth.js                #     认证接口
        │   │   ├── system.js              #     看板接口
        │   │   ├── articles.js            #     文章接口
        │   │   └── analysis.js            #     3号接口
        │   ├── stores/                    #   Pinia 状态管理
        │   │   ├── auth.js                #     认证状态
        │   │   ├── user.js                #     用户状态
        │   │   └── loginPrompt.js         #     登录提示
        │   ├── layouts/MainLayout.vue     #   主布局 (含AI面板)
        │   ├── views/                     #   页面组件
        │   │   ├── Login.vue              #     登录页
        │   │   ├── HomeView.vue           #     首页
        │   │   ├── DashboardView.vue      #     热点看板
        │   │   ├── HotEvents.vue          #     热点事件列表
        │   │   ├── EventDetail.vue        #     事件详情
        │   │   ├── NewsDetailView.vue     #     文章详情
        │   │   ├── CommunityView.vue      #     社区
        │   │   ├── AiAssistantView.vue    #     AI 助手
        │   │   └── profile/               #     个人中心
        │   └── components/                #   通用组件
        │       ├── Header.vue             #     顶部导航
        │       ├── MetricCard.vue         #     KPI 卡片
        │       ├── BaseChart.vue          #     图表基础组件
        │       ├── AuthModal.vue          #     认证弹窗
        │       ├── OpinionParticles.vue   #     粒子背景
        │       └── event/                 #     事件详情子组件
        │           ├── EventHeader.vue    #       事件标题
        │           ├── EventOverview.vue  #       事件概述
        │           ├── LifecycleAnalysis.vue  #   生命周期
        │           ├── EmotionAnalysis.vue    #   情感分析
        │           ├── KeywordAnalysis.vue    #   关键词云
        │           ├── PlatformDistribution.vue # 平台分布
        │           ├── PropagationAnalysis.vue # 传播图谱
        │           ├── RelatedNews.vue    #       关联新闻
        │           ├── CausalAnalysis.vue #       因果分析
        │           └── AIEventAssistant.vue  #   AI 问答
        ├── package.json                   #   依赖 & 脚本
        ├── vite.config.js                 #   Vite 配置
        └── index.html                     #   HTML 入口
```

---

## 技术架构总览

### 后端技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | 双服务架构 (Port 8000 + 8002) |
| ASGI | Uvicorn | 高性能异步服务器 |
| 数据库 | SQLite + SQLAlchemy | 用户认证数据 |
| 认证 | bcrypt + PyJWT | 密码哈希 + JWT 令牌 |
| 中文NLP | jieba, SnowNLP, OpenCC | 分词、情感、繁简转换 |
| 向量检索 | BGE + FAISS | 语义嵌入 + 向量检索 |
| 情感模型 | Erlangshen-Roberta-110M-Sentiment | 深度学习情感分析 |
| LLM | DeepSeek-V3 (SiliconFlow) | 事件要素抽取 + AI问答 |
| 时序算法 | ruptures, 手写 Holt/OLS/F-test | PELT变点、Holt预测、格兰杰因果 |
| 图算法 | networkx | PageRank、介数中心性、DiGraph |
| 机器学习 | scikit-learn | TF-IDF、Logistic Regression、GridSearchCV |

### 前端技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3 (Composition API) | 渐进式前端框架 |
| 构建 | Vite 8 | 极速开发服务器 |
| 状态管理 | Pinia 3 | 轻量级响应式状态 |
| 路由 | Vue Router 5 | SPA 路由 |
| UI 组件库 | Element Plus 2 | 企业级组件库 |
| 图表 | ECharts 6 | 数据可视化 |
| HTTP | Axios | 双后端 JWT 拦截 |

---

## 数据流转

```
                               1号 爬虫
                                  │
                    raw_data.json │ (JSON数组)
                                  ▼
                               2号 预处理
                    ┌─────────────┼─────────────┐
                    │             │             │
           segmented_data.csv  tfidf_matrix  advanced_analysis.csv
                    │             │             │
                    ▼             ▼             │
                               3号 NLP          │
                    ┌─────────────┬─────────────┤
                    │             │             │
         event_timeseries    news_output    event_table_llm
            _result.json        .json           .csv
                    │             │             │
                    ▼             ▼             ▼
                               4号 时序算法
                    ┌─────────────┬─────────────┐
                    │             │             │
              生命周期预测    传播溯源+判假   跨事件因果
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                          FastAPI :8002
                          FastAPI :8000  (3号接口)
                                  │
                                  ▼
                               5号 前端
                          Vue 3 + ECharts
```

### 数据文件约定

| 文件 | 生产者 | 消费者 | 内容 |
|------|:---:|:---:|------|
| `raw_data.json` | 1号 | 2号 | 原始采集数据 |
| `segmented_data.csv` | 2号 | 3号 | 分词后文本 |
| `tfidf_matrix.npz` | 2号 | 3号 | TF-IDF 特征矩阵 |
| `advanced_analysis(3).csv` | 2号 | 3/4/5号 | 情感+摘要+实体 |
| `event_timeseries_result.json` | 3号 | 4号 | 事件时序数据 (114个事件) |
| `news_output.json` | 3号 | 4号 | 结构化新闻 (含event_id) |
| `event_table_llm.csv` | 3号 | 4号 | LLM抽取的事件要素 |
| `event_faiss.index` | 3号 | 3号接口 | FAISS 向量索引 |
| `backend_propagation_nodes.json` | 1号 | 4号 | B站传播图节点 |
| `users.db` | 4号 | 4号 | 用户账户 (SQLite) |

---

## 快速开始

### 环境要求

- **Python**: 3.10+
- **Node.js**: 22.18+
- **Conda** (推荐): 用于管理 Python 环境

### 1. 安装依赖

```bash
# 1号 — 爬虫
cd opinion_system-feature-crawler-data
pip install -r requirements.txt

# 2号 — 预处理
cd ../opinion_system-2-preprocess
pip install -r requirements.txt

# 3号 — NLP (含模型下载)
cd ../opinion_system-dev
pip install -r requirements.txt
python download_models.py

# 4号 — 时序算法 + 后端
cd ../4_time
pip install -r requirements.txt

# 5号 — 前端
cd ../opinion_system-frontend/frontend
npm install
```

### 2. 配置环境变量

```bash
# 4号需要配置 .env 文件
cd 4_time
cp .env.example .env
# 编辑 .env 填入 LLM API Key
```

### 3. 运行数据管线（按顺序）

```bash
# Step 1: 数据采集
cd opinion_system-feature-crawler-data
python -m crawler.main --keywords "校园舆情" "暴雨灾害" "食品安全" --pages 3 --platforms news bilibili

# Step 2: 数据预处理
cd ../opinion_system-2-preprocess
python scripts/run_all.py

# Step 3: NLP 分析 (按顺序执行)
cd ../opinion_system-dev
python data_preprocess_clean.py
python bge_embedding.py
python news_sentiment_infer.py
python event_cluster.py
python event_category.py
python event_hot_score.py
python event_sentiment_stat.py
python event_sentiment_timeline.py
python event_llm_extract.py
python event_table_final.py
python build_faiss_index.py
```

### 4. 启动服务

```bash
# 启动 3号 API (Port 8000) — 事件详情/语义搜索
cd opinion_system-dev
uvicorn interface.main:app --host 0.0.0.0 --port 8000 --reload

# 启动 4号 API (Port 8002) — 看板/时序/认证/AI问答
cd 4_time
python server.py
# 或: uvicorn server:app --host 0.0.0.0 --port 8002 --reload

# 启动 5号 前端 (Port 5173)
cd opinion_system-frontend/frontend
npm run dev
```

### 5. 访问系统

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端页面 |
| http://localhost:8002/docs | 4号 API 文档 (Swagger) |
| http://localhost:8000/docs | 3号 API 文档 (Swagger) |
| http://localhost:8002/api/health | 4号 健康检查 |

---

## API 接口汇总

### 3号接口 (Port 8000) — NLP语义分析

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/analysis/events` | 事件列表 |
| `GET` | `/api/analysis/event/{eid}` | 单事件详情 |
| `GET` | `/api/analysis/event/{eid}/articles` | 事件关联新闻 |
| `POST` | `/api/history/filter` | 历史事件多条件筛选 |
| `POST` | `/api/similar/search` | FAISS 语义相似事件检索 |

### 4号接口 (Port 8002) — 时序算法 + 认证 + AI

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/dashboard` | 看板聚合数据 (KPI/情感/热度/关键词/平台) |
| `GET` | `/api/events` | 事件摘要列表（支持分类/关键词/时间筛选） |
| `GET` | `/api/event/{event_id}` | 单事件完整详情（含生命周期+传播+判假+因果） |
| `GET` | `/api/articles?event_id=` | 事件文章列表（含虚假检测判定） |
| `GET` | `/api/articles/{article_id}` | 单篇文章详情 |
| `GET` | `/api/cross-event` | 跨事件因果分析（格兰杰+传递熵） |
| `POST` | `/api/auth/register` | 用户注册 |
| `POST` | `/api/auth/login` | 用户登录 |
| `GET` | `/api/auth/me` | 当前用户信息 |
| `PUT` | `/api/auth/profile` | 修改个人资料 |
| `PUT` | `/api/auth/password` | 修改密码 |
| `POST` | `/api/ai/chat` | AI 智能问答 |

---

## 核心算法详解

### 模块1：舆情生命周期预测

判定舆情事件所处阶段（潜伏期→成长期→高潮期→衰退期→二次爆发），预测未来趋势。

| 算法 | 说明 |
|------|------|
| **多信号融合** | 四维（报道量40% + 情感分歧25% + 平台扩散20% + 互动15%）→ 综合热度指数 |
| **日周期剥离** | 统计24小时偏离因子，消除"凌晨低、白天高"的自然波动 |
| **Holt双指数平滑** | 趋势+水平双重指数衰减，含95%置信区间，自然收敛不过拟合 |
| **PELT变点检测** | 最小化[分段拟合误差 + 惩罚项]，自适应阈值替代固定差分 |
| **二次爆发检测** | 三条件联合：第一峰在前65% + 谷底反弹≥1.35倍 + 绝对增幅≥8 |
| ⭐**临界减速预警(CSD)** | 复杂系统相变理论：方差比+AR(1)自相关 → 系统跃迁前兆，比趋势提前4-6小时预警 |

### 模块2：传播溯源

构建传播有向图，识别关键节点，反事实推演真实因果影响力。

| 算法 | 说明 |
|------|------|
| **networkx DiGraph** | 替代嵌套树，支持多父节点，完整还原DAG传播结构 |
| **PageRank + 介数中心性** | 三维评分（PR 45% + BC 35% + 出度20%），发现"低粉高影响力"桥接节点 |
| ⭐**反事实推演** | 模拟移除关键节点 → 计算下游触达损失 → 因果影响力 ≠ 粉丝数 |

### 模块3：虚假文本检测

TF-IDF文本特征 + 元数据特征联合训练，三分类判定。

| 算法 | 说明 |
|------|------|
| **TF-IDF字符n-gram** | 2000维自动学习虚假文本模式，替代硬编码关键词 |
| **三元分类** | 可信 / 待验证 / 疑似虚假，区分"没证据"和"有证据" |
| **逻辑回归 + GridSearchCV** | 5折交叉验证自动选参，CV准确率~91% |
| ⭐**传播图拓扑增强** | 10维图特征（源头数、深度、密度、聚类系数等）交叉验证文本判假结果 |

**训练数据**: CED Dataset (清华大学 THUNLP), 3,381条标注微博 (1,533谣言 + 1,848非谣言)

### 模块4：跨事件因果分析

发现不同舆情事件之间的时序因果关系。

| 算法 | 说明 |
|------|------|
| **格兰杰因果检验** | 手写OLS回归+F检验，事件A的过去值→事件B的当前值的预测改善量 |
| ⭐**符号化传递熵** | 时序离散化→转移概率→信息论因果流，不依赖线性假设，对稀疏数据鲁棒 |

---

## 一键演示

无需完整数据管线，可直接体验4号全部算法：

```bash
cd 4_time
python demo.py
```

输出包括：
- 3个模拟事件的生命周期检测（不同时刻的阶段+热度+趋势+预警）
- 传播图构建（节点/边/PageRank/关键节点/反事实推演）
- 虚假检测（3个案例：官方通告/网友爆料/可疑消息）
- 统一报表接口演示
- 数据接口约定说明

---

## 许可证

MIT License

---

## 参考资料

- Song et al. (2018) — CED: Credible Early Detection of Social Media Rumors. *arXiv:1811.04175*
- Granger, C. W. J. (1969) — Investigating Causal Relations by Econometric Models. *Econometrica*
- Killick et al. (2012) — Optimal Detection of Changepoints. *JASA*
- Korenek & Sanda (2024-2025) — Symbolic Transfer Entropy. *Physical Review E*
- Zhu et al. (2024) — PSGT: Propagation Structure-Aware Graph Transformer. *KDD 2024*
- Brin & Page (1998) — The PageRank Citation Ranking

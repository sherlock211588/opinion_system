# 网络舆情事件智能分析系统 — 时序算法模块

**4号工程师** | 舆情生命周期预测 + 传播溯源 + 虚假文本检测 + 跨事件因果分析

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 项目简介

本模块是「网络舆情事件智能分析系统」的核心算法模块（4号工程师），负责对舆情事件进行全生命周期的时序分析。系统接收来自爬虫（1号）、文本清洗（2号）、NLP聚合（3号）的处理结果，输出生命周期预测、传播溯源、虚假检测和跨事件因果分析，最终通过 REST API 提供给前端可视化（5号）。

### 核心能力

| 能力 | 描述 |
|------|------|
| **生命周期预测** | 判定事件当前阶段（潜伏期/成长期/高潮期/衰退期/二次爆发），预测未来趋势，提供临界减速预警 |
| **传播溯源** | 构建传播有向图，识别关键传播节点（PageRank + 介数中心性），反事实推演信息枢纽 |
| **虚假文本检测** | 基于 TF-IDF + 元数据特征的联合模型，判断文章可信度（可信/待验证/疑似虚假） |
| **跨事件因果** | 格兰杰因果检验 + 符号化传递熵，发现事件间的线性和非线性时序因果关系 |

---

## 技术架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        5号 — 前端可视化                           │
│                    /api/* REST 接口 (FastAPI)                     │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│                     Pipeline (统一报表接口)                        │
│              pipe.event_report() / pipe.global_report()           │
└───┬──────────────┬─────────────────┬──────────────────┬──────────┘
    │              │                 │                  │
┌───▼───┐   ┌─────▼─────┐   ┌──────▼───────┐   ┌─────▼──────────┐
│ 模块1  │   │  模块2     │   │   模块3      │   │    模块4        │
│生命周期│   │  传播溯源   │   │  虚假检测    │   │  跨事件因果     │
│预测    │   │            │   │              │   │                │
└───┬───┘   └─────┬─────┘   └──────┬───────┘   └─────┬──────────┘
    │              │                 │                  │
    │         networkx              sklearn           scipy
    │         PageRank           TF-IDF+LR        Granger+TE
    │
    ├── stage.py       (阶段判定 + softmax)
    ├── fusion.py      (多信号融合 + 日周期剥离)
    ├── forecast.py    (Holt 指数平滑预测)
    ├── changepoint.py (PELT 变点检测)
    ├── resurgence.py  (二次爆发检测)
    └── critical.py    (临界减速预警 CSD)
```

### 数据流

```
1号爬虫 ──→ 转发关系链、账号粉丝数 ──→ 模块2 (传播溯源)
2号清洗 ──→ 清洗后文本 ────────────→ 模块3 (虚假检测)
3号NLP  ──→ 事件聚合 + 情感标签 ────→ 模块1 (生命周期) + 模块4 (因果)
                                     │
                                     ▼
                              Pipeline 统一报表
                                     │
                                     ▼
                         5号前端 / FastAPI Server
```

---

## 项目结构

```
4_time/
├── time_series/                      # 核心算法库
│   ├── __init__.py                   #   包入口，导出所有公共类
│   ├── pipeline.py                   #   统一报表接口 (Pipeline)
│   ├── cross_event.py                #   跨事件格兰杰因果 + 符号化传递熵
│   ├── report_generator.py           #   智能分析报告 & LLM 问答
│   │
│   ├── lifecycle/                    #   模块1：舆情生命周期预测
│   │   ├── __init__.py               #     LifecycleDetector 导出
│   │   ├── detector.py               #     主类：生命周期检测器
│   │   ├── stage.py                  #     阶段判定 + softmax 概率
│   │   ├── fusion.py                 #     多信号融合 + 日周期剥离
│   │   ├── forecast.py               #     Holt 指数平滑预测
│   │   ├── changepoint.py            #     PELT 变点检测
│   │   ├── resurgence.py             #     二次爆发检测
│   │   └── critical.py               #     临界减速预警 (CSD)
│   │
│   ├── propagation/                  #   模块2：事件传播溯源
│   │   └── tracer.py                 #     networkx DiGraph + PageRank + 反事实推演
│   │
│   ├── fake_detection/               #   模块3：虚假文本检测
│   │   ├── __init__.py               #     FakeDetector + FakeDetectorTrainer
│   │   ├── ced_loader.py             #     CED 谣言数据集加载器
│   │   ├── chef_loader.py            #     CHEF 事实验证数据集加载器
│   │   └── graph_features.py         #     传播图拓扑特征提取
│   │
│   └── utils/
│       └── mock_data.py              #   模拟数据生成（开发/演示用）
│
├── app/                              # FastAPI 服务层
│   ├── database.py                   #   SQLAlchemy 数据库引擎
│   ├── models.py                     #   用户数据模型
│   ├── schemas.py                    #   Pydantic 请求/响应模型
│   ├── security.py                   #   JWT + bcrypt 认证
│   └── routers/
│       ├── auth.py                   #   用户认证路由 (/api/auth/*)
│       └── ai.py                     #   AI 问答路由 (/api/ai/*)
│
├── data/                             # 数据集 (gitignore)
│   ├── CHEF/                         #   CHEF 事实验证数据集
│   └── Chinese_Rumor_Dataset/        #   CED 中文谣言数据集 (THUNLP)
│
├── server.py                         # FastAPI 主入口
├── demo.py                           # 一键演示（所有模块）
├── run_real_data.py                  # 用真实数据运行全部模块
├── run_full_3data.py                 # 完整流程（3.data 输入）
├── requirements.txt                  # 依赖列表
├── .env                              # 环境变量 (LLM API Key 等)
└── .gitignore
```

---

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装

```bash
cd 4_time
pip install -r requirements.txt
```

### 运行演示

```bash
# 一键演示全部 5 个模块
python demo.py
```

### 启动 API 服务

```bash
# 开发模式（热重载）
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# 生产模式
python server.py
```

启动后访问：
- API 文档: http://localhost:8001/docs
- 健康检查: http://localhost:8001/api/health

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/dashboard` | 看板聚合数据（KPI/情感/热度趋势/关键词/平台分布） |
| `GET` | `/api/events` | 事件摘要列表（首页看板），支持分类/关键词/时间筛选 |
| `GET` | `/api/event/{event_id}` | 单个事件详情（含生命周期+传播+判假+因果） |
| `GET` | `/api/articles?event_id=...` | 某事件全部文章（含虚假检测判定） |
| `GET` | `/api/articles/{article_id}` | 单篇文章详情 |
| `GET` | `/api/cross-event` | 跨事件因果分析结果 |
| `POST` | `/api/auth/register` | 用户注册 |
| `POST` | `/api/auth/login` | 用户登录 |
| `POST` | `/api/ai/chat` | AI 问答（基于事件数据） |

---

## 四个核心模块详解

### 模块1：舆情生命周期预测 (`LifecycleDetector`)

基于事件时序数据，判定舆情事件所处的生命周期阶段，并预测未来趋势。

**输入**：按时间聚合的事件数据 `[{time, news_count, hot_score, ...}, ...]`

**输出**：
- `current_stage`: 当前阶段（潜伏期/成长期/高潮期/衰退期/二次爆发）
- `stage_probabilities`: 各阶段 softmax 概率
- `trend_direction`: 趋势方向（上升/平稳/下降）
- `current_heat_index`: 综合热度指数 (0-100)
- `forecast`: 未来 24-72 小时预测值 + 置信区间
- `turning_points`: 拐点列表（PELT 算法）
- `resurgence`: 二次爆发检测结果
- `critical_early_warning`: 临界减速预警（红色/橙色/黄色/无）

**算法**：
- 多信号融合：报道量 + 情感分歧度 + 平台扩散度 + 互动强度 → 综合热度指数
- 日周期剥离：去除"凌晨低、白天高"的自然波动
- Holt 指数平滑：趋势 + 季节性双指数平滑预测
- PELT 变点检测：识别事件发展中的转折点
- 临界减速 (CSD)：监测方差增大 + AR(1) 自回归系数 → 系统即将发生相变的早期信号

### 模块2：传播溯源 (`PropagationTracer`)

基于转发关系链，构建传播有向图，识别关键传播节点和信息枢纽。

**输入**：传播节点列表 `[{node_id, account_name, follower_count, parent_node_id, ...}, ...]`

**输出**：
- `propagation_graph`: 传播图结构（节点数/边数/密度/DAG检测/源头数/叶子数）
- `key_nodes`: 关键节点排名（PageRank + 介数中心性 + 出度 综合评分）
- `propagation_depth`: 最长传播链深度
- `total_reach`: 去重触达人数估算
- `counterfactual_analysis`: 反事实推演（移除某节点后的信息损失）
- `graph_for_visualization`: 前端力导向图数据 (nodes + links + categories)

**算法**：
- networkx DiGraph 构建有向传播图
- PageRank 算法评估节点影响力
- 介数中心性 (Betweenness Centrality) 识别信息枢纽
- 反事实推演：模拟移除关键节点后的网络碎片化程度

### 模块3：虚假文本检测 (`FakeDetector`)

基于文本内容和元数据，判断信息的可信度。

**输入**：文章文本 + 元数据 `{source_verified, follower_count, sentiment_intensity, ...}`

**输出**：
- `verdict`: 判定结果（可信 / 待验证 / 疑似虚假）
- `confidence_score`: 可信度评分 (0-100)
- `fake_probability`: 虚假概率
- `risk_factors`: 风险因素列表
- `score_breakdown`: 各维度得分拆解

**特征维度** (v3.0)：
- TF-IDF 文本特征（从 CED 数据集提取的虚假文本模式）
- 8 维元数据特征：信源认证、粉丝数、情感强度、同行报道数、发布时间差、感叹号密度、文本长度、是否含链接
- 逻辑回归分类器 + 5 折交叉验证

**训练数据**：
- CED Dataset (清华大学 THUNLP)：3,381 条微博（1,533 谣言 + 1,848 非谣言）
- CHEF Dataset：事实验证数据

```bibtex
@article{song2018ced,
  title={CED: Credible Early Detection of Social Media Rumors},
  author={Song, Changhe and Tu, Cunchao and Yang, Cheng and Liu, Zhiyuan and Sun, Maosong},
  journal={arXiv preprint arXiv:1811.04175},
  year={2018}
}
```

### 模块4：跨事件因果分析 (`CrossEventAnalyzer`)

发现不同舆情事件之间的时序因果关系。

**输入**：多个事件的时间序列字典 `{event_id: [records], ...}`

**输出**：
- `pairs`: 格兰杰因果对列表（线性因果）
- `transfer_entropy_pairs`: 符号化传递熵对列表（非线性因果）
- `causal_graph`: 有向因果图
- `summary`: 人类可读摘要

**算法**：
- **格兰杰因果检验** (Granger, 1969)：检验事件A的过去值是否能显著提升对事件B当前值的预测精度（线性框架）
- **符号化传递熵** (Symbolic Transfer Entropy, Korenek & Sanda, 2024-2025)：将连续时序离散化为符号序列，计算信息论意义上的因果流向，不依赖线性假设，对稀疏数据更鲁棒

---

## Pipeline 统一报表接口

5号前端只需了解一个类：

```python
from time_series.pipeline import Pipeline

pipe = Pipeline(data_interval_hours=6)

# 接口1：单事件完整报表 → 前端「事件详情页」
report = pipe.event_report(event_data, articles, propagation_nodes)

# 接口2：全局报表 → 前端「热点看板首页」
report = pipe.global_report(all_events, all_articles, all_propagation)

# 接口3：批量文章判假
results = pipe.article_check(articles)
```

---

## 环境变量

在 `.env` 文件中配置：

```env
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_API_KEY=your_api_key_here
LLM_MODEL=deepseek-ai/DeepSeek-V3
LLM_TIMEOUT=60
LLM_MAX_TOKENS=1024
```

---

## 数据接口约定

### 你需要从队友那里拿到的数据

| 来源 | 数据 | 用途 |
|------|------|------|
| 1号爬虫 | 文章发布时间、转发关系链、账号粉丝数、来源平台、文章URL | 传播溯源、元数据特征 |
| 2号清洗 | 标准化时间字段、清洗后纯文本 | 虚假检测 |
| 3号NLP | 事件聚合结果、情感标签+强度、事件主题分类 | 生命周期建模、虚假检测特征 |

### 你输出给前端的数据

详见各 API 接口的响应格式，核心字段包括：
- 生命周期：`current_stage`, `trend_direction`, `forecast`, `turning_points`
- 传播图：`nodes`, `links`, `categories`（力导向图格式）
- 虚假检测：`verdict`, `confidence_score`, `risk_factors`
- 跨事件因果：`granger_pairs`, `transfer_entropy_pairs`, `causal_graph`

---

## 依赖项

```
numpy>=1.24           # 数值计算
scipy>=1.10           # 科学计算（F分布等）
scikit-learn>=1.3     # 机器学习（TF-IDF, Logistic Regression）
networkx>=3.0         # 图算法（PageRank, 介数中心性）
ruptures>=1.1         # 变点检测（PELT）
joblib>=1.3           # 模型持久化
fastapi>=0.100        # Web 框架
uvicorn>=0.23         # ASGI 服务器
bcrypt>=4.0           # 密码哈希
PyJWT>=2.8            # JWT 令牌
sqlalchemy>=2.0       # ORM（用户认证）
openai>=1.0           # LLM API 客户端
python-dotenv>=1.0    # 环境变量加载
```

---

## 开发说明

- **模型缓存**：虚假检测模型首次训练后自动缓存为 `fake_detector_model.pkl`（已加入 `.gitignore`）
- **编码规范**：所有 Python 文件使用 UTF-8 编码，类型注解使用 `from __future__ import annotations`
- **数据格式**：时间字段统一为 `YYYY-MM-DD HH:MM:SS` 或 ISO 8601 格式
- **API 文档**：FastAPI 自动生成 Swagger UI，启动后访问 `/docs`

---

## 许可证

MIT License

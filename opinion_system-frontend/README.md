# 网络舆情事件智能分析系统 — 前端可视化模块

**5号工程师** | Vue 3 + ECharts + Element Plus

---

## 项目简介

本模块是「网络舆情事件智能分析系统」的前端可视化部分（5号工程师），基于 Vue 3 Composition API 构建的单页应用 (SPA)，提供热点事件看板、舆情生命周期曲线、情感分布图表、传播路径图谱、关键词云、AI 智能问答等功能。

---

## 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.x | 渐进式前端框架 (Composition API) |
| Vite | 8.x | 极速开发构建工具 |
| Vue Router | 5.x | SPA 路由管理 |
| Pinia | 3.x | 轻量级状态管理 |
| Element Plus | 2.x | 企业级 UI 组件库 |
| ECharts | 6.x | 数据可视化图表 |
| Axios | 1.x | HTTP 客户端 (双后端 JWT 拦截) |

---

## 项目结构

```
opinion_system-frontend/
└── frontend/
    ├── index.html                      # HTML 入口
    ├── package.json                    # 依赖 & 脚本
    ├── vite.config.js                  # Vite 配置
    ├── jsconfig.json                   # 路径别名
    ├── eslint.config.js                # ESLint 配置
    ├── .prettierrc.json                # Prettier 配置
    └── src/
        ├── main.js                     # Vue 应用入口
        ├── App.vue                     # 根组件
        │
        ├── router/
        │   └── index.js                # 路由配置
        │
        ├── api/                        # API 请求层
        │   ├── request.js              #   Axios 实例 + JWT 拦截器 (双后端)
        │   ├── events.js               #   事件数据归一化 (1000+行)
        │   ├── auth.js                 #   用户认证 (登录/注册/个人)
        │   ├── system.js               #   看板 KPI 数据
        │   ├── articles.js             #   文章 + 虚假检测
        │   └── analysis.js             #   3号 NLP 分析接口
        │
        ├── stores/                     # Pinia 状态管理
        │   ├── auth.js                 #   认证状态
        │   ├── user.js                 #   用户信息
        │   └── loginPrompt.js          #   登录弹窗控制
        │
        ├── layouts/
        │   └── MainLayout.vue          # 主布局 (顶部导航 + AI 侧边面板)
        │
        ├── views/                      # 页面组件
        │   ├── Login.vue               #   登录页
        │   ├── HomeView.vue            #   首页
        │   ├── DashboardView.vue       #   热点看板 (KPI + 趋势 + 关键词)
        │   ├── HotEvents.vue           #   热点事件列表
        │   ├── EventDetail.vue         #   事件详情页 (全部子模块)
        │   ├── NewsDetailView.vue      #   文章详情页
        │   ├── CommunityView.vue       #   社区讨论
        │   ├── AiAssistantView.vue     #   AI 智能助手
        │   └── profile/                #   个人中心
        │       ├── ProfileOverviewView.vue  # 个人概览
        │       └── UserProfileView.vue      # 用户设置
        │
        ├── components/                 # 通用组件
        │   ├── Header.vue              #   顶部导航栏
        │   ├── MetricCard.vue          #   KPI 指标卡片
        │   ├── BaseChart.vue           #   ECharts 图表封装
        │   ├── AuthModal.vue           #   登录/注册弹窗
        │   ├── OpinionParticles.vue    #   粒子动画背景
        │   └── event/                  #   事件详情子组件
        │       ├── EventHeader.vue     #     事件标题 + 元信息
        │       ├── EventOverview.vue   #     事件概述 (时间/地点/人物)
        │       ├── LifecycleAnalysis.vue   #  生命周期曲线 + 阶段判定
        │       ├── EmotionAnalysis.vue     #  情感饼图 + 时序变化
        │       ├── KeywordAnalysis.vue     #  关键词词云
        │       ├── PlatformDistribution.vue # 平台来源占比
        │       ├── PropagationAnalysis.vue  # 传播力导向图
        │       ├── RelatedNews.vue     #     关联新闻列表 (含判假标签)
        │       ├── CausalAnalysis.vue  #     跨事件因果图
        │       └── AIEventAssistant.vue  #   AI 事件问答
        │
        ├── mock/                       # Mock 数据 (离线开发)
        │   ├── eventData.js
        │   └── newsDetailMock.js
        │
        ├── data/
        │   └── mockOpinion.js          # 舆情模拟数据
        │
        └── utils/
            └── recentViews.js          # 最近浏览记录
```

---

## 快速开始

### 环境要求

- Node.js >= 22.18.0
- npm

### 安装

```bash
cd opinion_system-frontend/frontend
npm install
```

### 开发模式

```bash
npm run dev
```

默认启动在 http://localhost:5173

### 生产构建

```bash
npm run build
npm run preview   # 预览构建结果
```

---

## 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/login` | Login | 登录页 |
| `/` | HomeView | 首页 |
| `/events` | HotEvents | 热点事件列表 |
| `/event/:id` | EventDetail | 事件详情 (含全部子模块) |
| `/report/:id` | EventDetail | 事件报告 (同上) |
| `/news/:articleId` | NewsDetailView | 文章详情 + 判假 |
| `/community` | CommunityView | 社区讨论 |
| `/ai` | AiAssistantView | AI 智能助手 |
| `/profile` | UserProfileView | 个人中心 |

---

## 后端接口对接

前端同时对接两个后端服务：

| 后端 | 地址 | 用途 |
|------|------|------|
| 3号 NLP | `http://localhost:8000` | 事件详情、语义搜索、历史筛选 |
| 4号 时序 | `http://localhost:8002` | 看板、生命周期、传播、判假、因果、认证、AI问答 |

JWT 令牌自动附加到所有 4号请求的 `Authorization` 头中。

---

## 代码规范

```bash
npm run lint     # ESLint + Oxlint 检查
npm run format   # Prettier 格式化
```

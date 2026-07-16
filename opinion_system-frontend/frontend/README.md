# 舆见（Opinion Insight）

舆见是一套面向公众的舆情事件分析前端系统，用于展示热点事件、新闻内容、传播趋势、情感倾向、平台分布及相关分析结果。

当前仓库的 `frontend` 分支主要保存前端项目代码。前端采用 Vue 3 + Vite 构建，并已完成基础页面、路由、状态管理、图表展示、登录与游客访问逻辑，以及后端接口调用层的初步封装。

## 一、项目功能

当前前端主要包含以下模块：

- 登录与注册
- 游客访问
- 系统首页
- 热点事件列表
- 事件详情分析
- 新闻详情
- 数据看板
- 社区页面
- AI 助手
- 个人中心
- 情感趋势、平台分布等可视化图表
- 新闻与事件相关接口封装
- 登录状态与用户权限管理

## 二、技术栈

- Vue 3
- Vite
- Vue Router
- Pinia
- Element Plus
- ECharts
- Axios
- ESLint
- Oxlint
- Prettier

## 三、项目目录

```text
opinion_system/
├─ README.md
└─ frontend/
   ├─ public/                 # 静态资源
   ├─ src/
   │  ├─ api/                # 接口请求封装
   │  │  ├─ articles.js      # 新闻文章接口
   │  │  ├─ auth.js          # 登录认证接口
   │  │  ├─ events.js        # 舆情事件接口
   │  │  ├─ helpers.js       # 接口辅助方法
   │  │  ├─ request.js       # Axios 请求实例
   │  │  └─ system.js        # 系统相关接口
   │  ├─ assets/             # 图片、样式等资源
   │  ├─ components/         # 通用组件
   │  ├─ data/               # 前端数据
   │  ├─ layouts/            # 页面布局
   │  ├─ mock/               # 模拟数据
   │  ├─ router/             # 路由配置
   │  ├─ stores/             # Pinia 状态管理
   │  ├─ utils/              # 工具函数
   │  ├─ views/              # 页面文件
   │  ├─ App.vue
   │  └─ main.js
   ├─ package.json
   ├─ package-lock.json
   └─ vite.config.js
```

## 四、主要页面

`src/views` 目录当前包含：

- `Login.vue`：登录与注册页面
- `HomeView.vue`：系统首页
- `HotEventView.vue`、`HotEventsView.vue`：热点事件页面
- `EventDetail.vue`、`EventDetailView.vue`：事件详情分析页面
- `NewsDetailView.vue`：新闻详情页面
- `DashboardView.vue`：数据看板
- `CommunityView.vue`：社区页面
- `AIChat.vue`、`AiAssistantView.vue`：AI 问答相关页面
- `ProfileView.vue`：个人中心
- `AboutView.vue`：项目说明页面

## 五、运行环境

建议使用：

```text
Node.js 22 或更高版本
npm
VS Code
```

推荐安装 VS Code 的 Vue 官方扩展。

## 六、本地运行

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动开发环境：

```bash
npm run dev
```

启动成功后，终端会显示本地访问地址，例如：

```text
http://localhost:5173/
```

如果 5173 端口被占用，Vite 会自动使用其他端口，例如：

```text
http://localhost:5174/
```

## 七、常用命令

启动开发服务器：

```bash
npm run dev
```

构建生产版本：

```bash
npm run build
```

预览构建结果：

```bash
npm run preview
```

代码检查：

```bash
npm run lint
```

格式化代码：

```bash
npm run format
```

## 八、接口说明

前端接口统一放在：

```text
frontend/src/api/
```

其中：

- `request.js`：Axios 请求实例和通用配置
- `auth.js`：登录、注册等认证接口
- `events.js`：舆情事件接口
- `articles.js`：新闻文章接口
- `system.js`：系统相关接口
- `helpers.js`：接口辅助方法

当前项目仍处于前后端联调阶段。部分页面可能继续使用本地数据或 Mock 数据；后端服务未启动、接口地址未配置或接口数据尚未提供时，相关真实数据功能无法完成验证。

前端不直接连接 MySQL、Elasticsearch 等数据库，所有数据均应通过后端 HTTP API 获取。

## 九、开发状态

当前已完成：

- 前端项目基础架构
- 主要页面与导航
- Vue Router 路由组织
- Pinia 登录状态管理
- 登录、注册及游客访问逻辑
- 舆情事件与新闻展示页面
- 图表可视化基础功能
- Axios 请求层及业务接口文件
- 基础代码规范与构建配置

仍需继续完成：

- 与后端真实接口联调
- 根据最终接口字段调整页面数据映射
- 清理不再使用的旧页面或重复组件
- 完善异常状态、空数据状态和加载状态
- 完成完整功能测试
- 优化生产环境配置与部署流程

## 十、分支说明

当前前端代码位于：

```text
frontend
```

该分支用于保存和维护前端功能。后续完成联调和测试后，再按照团队协作流程合并到目标分支。

## 十一、注意事项

请勿提交以下内容：

```text
node_modules/
dist/
.env
临时日志
缓存文件
```

提交代码前建议执行：

```bash
npm run lint
npm run build
git status
```

## 十二、项目定位

舆见旨在通过热点事件聚合、传播趋势分析、情感倾向分析、平台分布、关键词提取、相关新闻展示和智能问答等功能，帮助用户快速了解舆情事件的发展过程与公众观点。

# KIRIN-AI 项目架构说明

## 一、项目概述

KIRIN-AI（项目名 `lightmo`）是一个基于 **FastAPI + Vue3 + Naive UI** 的前后端分离 AI 求职助手平台。在传统 RBAC 权限管理系统的基础上，融合了 **LangGraph Agent 架构**，实现了从简历分析、岗位匹配、简历优化、投递计划生成到面试模拟的完整求职业务闭环。

### 核心特性

| 特性 | 说明 |
|------|------|
| 技术栈 | Python 3.11 + FastAPI + Vue3 + Vite + Naive UI |
| 权限模型 | RBAC（角色-菜单-API 三级权限控制） |
| 鉴权方式 | JWT Token |
| AI 引擎 | 阿里云 DashScope（Qwen 系列模型）+ LangGraph |
| 数据库 | PostgreSQL（Tortoise ORM 异步驱动） |
| 向量存储 | ChromaDB（RAG 知识检索） |
| 国际化 | vue-i18n（中/英） |

---

## 二、项目目录结构

```
demo/
├── app/                          # 后端应用
│   ├── __init__.py               # FastAPI 应用工厂（create_app）
│   ├── agent/                    # LangGraph Agent 核心
│   │   ├── langgraph_graph.py    # Agent 图定义（状态机）
│   │   ├── langgraph_nodes.py    # Agent 节点逻辑
│   │   ├── langgraph_state.py    # Agent 状态定义
│   │   ├── router.py             # 意图路由（关键词 + LLM 双模式）
│   │   ├── executor.py           # 工具执行器
│   │   └── job_agent.py          # 求职 Agent 入口
│   ├── api/                      # API 路由层
│   │   └── v1/                   # V1 版本接口
│   │       ├── apis/             # API 资源管理接口
│   │       ├── auditlog/         # 审计日志接口
│   │       ├── base/             # 基础接口（登录/Token）
│   │       ├── chat/             # 聊天/AI 对话接口
│   │       ├── depts/            # 部门管理接口
│   │       ├── menus/            # 菜单管理接口
│   │       ├── roles/            # 角色管理接口
│   │       └── users/            # 用户管理接口
│   ├── controllers/              # 业务控制器（API 与 Service 之间的协调层）
│   ├── core/                     # 核心基础设施
│   │   ├── bootstrap.py          # 中间件/路由/异常注册
│   │   ├── crud.py               # 通用 CRUD 基类
│   │   ├── dependency.py         # FastAPI 依赖注入（鉴权/权限校验）
│   │   ├── exceptions.py         # 统一异常处理
│   │   ├── middlewares.py        # 审计日志/后台任务中间件
│   │   ├── security.py           # JWT 生成与校验
│   │   └── seed.py               # 初始数据种子
│   ├── log/                      # 日志模块
│   ├── memory/                   # 对话记忆模块
│   ├── models/                   # Tortoise ORM 数据模型
│   │   ├── admin.py              # 用户/角色/菜单/部门/审计日志模型
│   │   ├── chat.py               # 聊天记录模型
│   │   ├── base.py               # 模型基类
│   │   └── enums.py              # 枚举定义
│   ├── rag/                      # RAG 向量检索模块
│   │   └── chromadb_client.py    # ChromaDB 客户端
│   ├── repositories/             # 数据访问层（Repository 模式）
│   ├── schemas/                  # Pydantic 数据校验模型
│   ├── settings/                 # 配置中心
│   │   └── config.py             # 全局配置（DB/JWT/CORS/AI 参数）
│   ├── tools/                    # Agent 工具集
│   │   ├── base.py               # 工具基类
│   │   ├── rag_tool.py           # 知识检索工具
│   │   ├── todo_tool.py          # 待办任务工具
│   │   ├── tracker_tool.py       # 求职进度追踪工具
│   │   ├── interview_tool.py     # 面试准备工具
│   │   ├── interview_sim_tool.py # 面试模拟工具
│   │   ├── salary_tool.py        # 薪资查询工具
│   │   ├── guide_tool.py         # 求职攻略工具
│   │   ├── feedback_tool.py      # 反馈评分工具
│   │   ├── resume_tool.py        # 简历解析工具
│   │   ├── jd_tool.py            # JD 解析工具
│   │   ├── match_tool.py         # 匹配度分析工具
│   │   ├── optimize_tool.py      # 简历优化工具
│   │   ├── plan_tool.py          # 投递计划生成工具
│   │   ├── resume_export_tool.py # 简历导出工具
│   │   └── conversation_tool.py  # 对话管理工具
│   └── utils/                    # 工具函数
├── web/                          # 前端应用
│   ├── build/                    # 构建配置
│   │   ├── config/               # Vite 构建变量
│   │   ├── plugin/               # Vite 插件配置
│   │   └── script/               # 构建脚本
│   ├── i18n/                     # 国际化资源
│   │   └── messages/             # 中/英翻译文件
│   ├── settings/                 # 前端运行时配置
│   │   ├── index.js              # 主题/布局配置
│   │   └── theme.json            # 主题色定义
│   ├── src/
│   │   ├── api/                  # 后端 API 调用封装
│   │   ├── assets/               # 静态资源（图片/SVG/图标）
│   │   ├── components/           # 通用组件
│   │   │   ├── avatar/           # 头像裁剪
│   │   │   ├── common/           # 通用布局组件
│   │   │   ├── icon/             # 图标选择器
│   │   │   ├── page/             # 页面容器
│   │   │   ├── query-bar/        # 查询条件栏
│   │   │   └── table/            # CRUD 表格/弹窗
│   │   ├── composables/          # 组合式函数
│   │   │   ├── useCRUD.js        # CRUD 逻辑复用
│   │   │   ├── useFileUpload.js  # 文件上传
│   │   │   └── useMarkdown.js    # Markdown 渲染
│   │   ├── directives/           # 自定义指令（权限指令）
│   │   ├── layout/               # 页面布局
│   │   │   └── components/       # 侧边栏/顶栏/标签页
│   │   ├── router/               # 路由配置
│   │   │   ├── guard/            # 路由守卫（鉴权/标题/加载）
│   │   │   └── routes/           # 路由表定义
│   │   ├── store/                # Pinia 状态管理
│   │   │   └── modules/          # 按业务拆分的 Store
│   │   ├── styles/               # 全局样式
│   │   ├── types/                # TypeScript 类型声明
│   │   ├── utils/                # 工具函数
│   │   │   ├── auth/             # Token 管理
│   │   │   ├── common/           # 通用工具
│   │   │   ├── http/             # Axios 封装（拦截器）
│   │   │   └── storage/          # 本地存储封装
│   │   └── views/                # 页面视图
│   │       ├── agent-chat/       # Agent 智能对话
│   │       ├── chat/             # AI 聊天
│   │       ├── job-assistant/    # 求职助手（核心业务页）
│   │       ├── interview-sim/    # 面试模拟
│   │       ├── knowledge/        # 知识库管理
│   │       ├── tracker/          # 求职进度
│   │       ├── todo/             # 待办任务
│   │       ├── workbench/        # 工作台
│   │       ├── system/           # 系统管理（用户/角色/菜单/部门/API/审计日志）
│   │       ├── login/            # 登录页
│   │       ├── profile/          # 个人中心
│   │       └── error-page/       # 错误页（401/403/404/500）
│   ├── .env.development          # 开发环境变量
│   ├── .env.production           # 生产环境变量
│   ├── vite.config.js            # Vite 配置
│   └── unocss.config.js          # UnoCSS 原子化样式配置
├── .env.example                  # 环境变量模板
├── pyproject.toml                # Python 项目配置与依赖
├── Dockerfile                    # Docker 构建文件
├── Makefile                      # 常用命令快捷入口
├── run.py                        # 后端启动入口
└── CLAUDE.md                     # AI 编码规范
```

---

## 三、后端架构详解

### 3.1 分层架构

```
请求 → API 路由层 → Controller → Repository → Model（Tortoise ORM）→ PostgreSQL
                ↓
           Schema（Pydantic 校验）
                ↓
           Agent/Tools（AI 业务逻辑）
```

| 层级 | 目录 | 职责 |
|------|------|------|
| API 路由 | `app/api/v1/` | HTTP 接口定义、权限依赖注入 |
| Controller | `app/controllers/` | 业务协调，串联 Repository 与 Schema |
| Repository | `app/repositories/` | 数据访问，封装 ORM 查询 |
| Model | `app/models/` | 数据模型定义（Tortoise ORM） |
| Schema | `app/schemas/` | 请求/响应数据校验（Pydantic） |
| Agent | `app/agent/` | LangGraph 状态机与意图路由 |
| Tools | `app/tools/` | Agent 可调用的工具集 |

### 3.2 Agent 架构（LangGraph）

Agent 采用 **LangGraph 状态图** 模式，核心流程：

```
用户输入 → intent_router（意图识别）
              ├─ chat → response_builder（直接对话）
              └─ tool → tool_executor（执行工具）
                           ├─ 单步完成 → response_builder
                           └─ 需继续 → workflow_continue → response_builder
```

**状态定义**（[langgraph_state.py](app/agent/langgraph_state.py)）：

| 字段 | 类型 | 说明 |
|------|------|------|
| query | str | 用户原始输入 |
| intent | str | 识别出的意图 |
| tool_name | str | 选中的工具名 |
| tool_args | dict | 工具调用参数 |
| tool_output | str | 工具执行结果 |
| iteration | int | 当前迭代次数 |
| max_iterations | int | 最大迭代次数（默认 3） |
| need_more | bool | 是否需要继续调用工具 |
| final_answer | str | 最终回复 |

**意图路由**（[router.py](app/agent/router.py)）支持两种模式：
- **关键词路由**：基于预定义关键词匹配，速度快
- **LLM 路由**：调用大模型判断意图，准确率高

支持的工具意图：`rag_tool` / `todo_tool` / `tracker_tool` / `interview_tool` / `salary_tool` / `guide_tool` / `feedback_tool` / `workflow` / `chat`

### 3.3 权限体系

```
用户(User) ←→ 角色(Role) ←→ 菜单(Menu)  → 前端路由/按钮控制
                        ←→ API(Api)     → 后端接口级权限
```

- **DependAuth**：验证 JWT Token，获取当前用户
- **DependPermission**：在 DependAuth 基础上，校验用户角色是否拥有当前 API 访问权限
- **v-permission 指令**：前端按钮级权限控制

### 3.4 数据模型

| 模型 | 表名 | 说明 |
|------|------|------|
| User | user | 用户（多对多关联 Role） |
| Role | role | 角色（多对多关联 Menu、Api） |
| Menu | menu | 菜单（树形结构，parent_id） |
| Api | api | API 资源（path + method 唯一） |
| Dept | dept | 部门（树形结构 + 闭包表 DeptClosure） |
| AuditLog | audit_log | 审计日志 |
| ChatHistory | chat_history | 聊天记录 |

---

## 四、前端架构详解

### 4.1 技术选型

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.3 | 响应式框架 |
| Vite | 4.4 | 构建工具 |
| Naive UI | 2.34 | UI 组件库 |
| Pinia | 2.1 | 状态管理 |
| Vue Router | 4.2 | 路由 |
| vue-i18n | 9 | 国际化 |
| UnoCSS | 0.55 | 原子化 CSS |
| Axios | 1.4 | HTTP 客户端 |
| marked | 18 | Markdown 渲染 |
| highlight.js | 11 | 代码高亮 |

### 4.2 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/workbench` | 工作台 | 首页仪表盘 |
| `/agent-chat` | Agent 智能对话 | AI 对话主界面 |
| `/knowledge` | 知识库管理 | RAG 知识库 |
| `/todo` | 待办任务 | 任务管理 |
| `/tracker` | 求职进度 | 投递追踪 |
| `/interview-sim` | 面试模拟 | 模拟面试 |
| `/profile` | 个人中心 | 用户信息 |
| `/system/user` | 用户管理 | 系统管理 |
| `/system/role` | 角色管理 | 系统管理 |
| `/system/menu` | 菜单管理 | 系统管理 |
| `/system/dept` | 部门管理 | 系统管理 |
| `/system/api` | API 管理 | 系统管理 |
| `/system/auditlog` | 审计日志 | 系统管理 |
| `/system/chathistory` | 聊天记录 | 系统管理 |
| `/login` | 登录页 | 认证入口 |

### 4.3 状态管理（Pinia Store）

| Store | 说明 |
|-------|------|
| `app` | 应用全局状态（主题/布局/侧边栏） |
| `user` | 用户信息与登录态 |
| `permission` | 动态路由与菜单权限 |
| `tags` | 标签页管理 |
| `chat` | AI 聊天状态 |
| `agent-chat` | Agent 对话状态 |
| `interview-sim` | 面试模拟状态 |
| `tracker` | 求职进度状态 |

### 4.4 HTTP 请求层

- 基于 Axios 封装，统一拦截器处理 Token 注入与错误提示
- 开发环境通过 Vite Proxy 代理到后端 `/api/v1`
- 请求/响应统一经 `interceptors.js` 处理

---

## 五、AI 业务闭环

项目围绕 **求职流程** 构建了完整的业务闭环：

```
上传简历 → 输入 JD → 匹配度分析 → 简历优化 → 生成投递计划 → 写入待办 → 面试准备
```

### 工具与业务对应关系

| 工具 | 业务场景 |
|------|----------|
| `resume_tool` | 解析上传的 PDF/Markdown 简历，提取结构化信息 |
| `jd_tool` | 解析岗位描述，提取技能要求与关键词 |
| `match_tool` | 简历与 JD 匹配度分析，输出评分与差距 |
| `optimize_tool` | 基于 JD 定向优化简历 |
| `plan_tool` | 生成投递行动计划 |
| `todo_tool` | 将计划拆解为待办任务 |
| `tracker_tool` | 求职进度追踪与投递记录管理 |
| `interview_tool` | 面试准备与面试题生成 |
| `interview_sim_tool` | 模拟面试对话 |
| `salary_tool` | 薪资查询与谈判建议 |
| `guide_tool` | 求职攻略与跨行业指导 |
| `rag_tool` | 基于知识库的 RAG 检索增强 |
| `feedback_tool` | 用户反馈与评分 |
| `resume_export_tool` | 简历导出（Word 格式） |
| `conversation_tool` | 对话上下文管理 |

---

## 六、环境配置

### 6.1 后端环境变量（`.env`）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key（必填） | - |
| `DASHSCOPE_BASE_URL` | DashScope API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `MODEL_NAME` | 使用的模型名称 | `qwen-turbo` |
| `MAX_TOKENS` | 最大生成 Token 数 | `2000` |
| `TEMPERATURE` | 生成温度 | `0.7` |
| `SECRET_KEY` | JWT 签名密钥（生产环境必须替换） | `change-me-in-production` |
| `JWT_EXPIRE_MINUTES` | Token 过期时间（分钟） | `10080`（7天） |
| `DB_HOST` | PostgreSQL 主机 | `localhost` |
| `DB_PORT` | PostgreSQL 端口 | `5432` |
| `DB_USER` | 数据库用户名 | `postgres` |
| `DB_PASSWORD` | 数据库密码 | - |
| `DB_NAME` | 数据库名 | `lightmo` |
| `CORS_ORIGINS` | 允许的跨域来源 | `http://localhost:3000` |
| `DEBUG` | 调试模式 | `false` |

### 6.2 前端环境变量

| 变量 | 说明 | 开发环境值 |
|------|------|-----------|
| `VITE_PUBLIC_PATH` | 资源公共路径 | `/` |
| `VITE_USE_PROXY` | 是否启用代理 | `true` |
| `VITE_BASE_API` | API 基础路径 | `/api/v1` |

---

## 七、本地启动

### 后端

```bash
# 1. 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 .env 文件（参考 .env.example）

# 4. 启动服务
python run.py
```

后端运行在 `http://localhost:9999`，API 文档访问 `http://localhost:9999/docs`

### 前端

```bash
# 1. 进入前端目录
cd web

# 2. 安装依赖
pnpm install

# 3. 启动开发服务器
pnpm dev
```

前端运行在 `http://localhost:3000`，自动代理 API 请求到后端

### Docker 部署

```bash
docker build --no-cache . -t vue-fastapi-admin
docker run -d --restart=always --name=vue-fastapi-admin -p 9999:80 vue-fastapi-admin
```

---

## 八、关键设计决策

1. **Repository 模式**：数据访问层与业务逻辑解耦，便于单元测试和替换持久化实现
2. **LangGraph 状态图**：Agent 执行流程可视化、可中断、可恢复，比纯函数调用链更可控
3. **双模式意图路由**：关键词路由保证速度，LLM 路由保证准确率，按需切换
4. **动态路由 + RBAC**：菜单由后端根据角色动态下发，前端动态注册路由，实现细粒度权限
5. **闭包表（DeptClosure）**：部门树查询使用闭包表模式，避免递归查询性能问题
6. **审计日志中间件**：通过 HTTP 中间件自动记录所有 API 调用，无需业务代码侵入

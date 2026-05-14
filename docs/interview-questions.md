# KIRIN-AI 项目技术面试深度追问

> 基于项目实际代码逐层深挖，从基础功能 → 实现细节 → 技术选型 → 难点瓶颈 → 性能优化 → 底层原理 → 线上问题 → 拓展延伸

---

## 一、基础深挖（15 题）

### 1. 你的 RBAC 权限模型具体是怎么实现的？一次请求的完整权限校验链路是怎样的？

**面试官考察点：** 对权限模型的理解深度，能否说清从请求到鉴权的完整链路。

**期望回答：**

权限模型采用 **RBAC（基于角色的访问控制）**，核心表结构为 User → Role → Api（三级关联）。具体链路：

1. 前端请求携带 `token` header，进入 FastAPI 的依赖注入链
2. `DependPermission` 触发 `PermissionControl.has_permission`，它内部先 `DependAuth`
3. `AuthControl.is_authed` 解码 JWT，验证 token 类型为 access（不是 refresh），从 payload 取 `user_id` 查数据库确认用户存在且 `is_active=True`
4. 设置 `CTX_USER_ID` ContextVar，将 user_id 注入当前协程上下文
5. `has_permission` 判断 `is_superuser`，超管直接放行
6. 普通用户加载所有角色并 `prefetch_related("apis")`，构建 `set[(method, path)]` 权限集合
7. 检查 `(request.method, request.url.path)` 是否在集合中，不在则 403

关键设计：权限粒度到 **API 级别**（method + path），不是菜单级别。按钮级控制前端用 `v-permission` 指令，后端用 `DependAuth`（仅鉴权不鉴权）或 `DependPermission`（鉴权+鉴权）。

---

### 2. ContextVar 在你的项目中是怎么用的？为什么不用函数参数传递 user_id？

**面试官考察点：** 对 Python 异步编程中上下文传播机制的理解。

**期望回答：**

项目用了两个 ContextVar：`CTX_USER_ID` 和 `CTX_BG_TASKS`。

**为什么不用参数传递：** 在分层架构中，user_id 从 API 层 → Controller → Service → Repository 逐层透传，每层都要加参数，侵入性大。ContextVar 是协程级别的"隐式参数"，一次设置，整条调用链自动可读。

**具体用法：**
- `AuthControl.is_authed` 中设置 `CTX_USER_ID.set(user.id)`
- Repository/Service 中读取 `CTX_USER_ID.get()` 获取当前用户
- `BgTasks` 类通过 `CTX_BG_TASKS` 在请求生命周期内累积后台任务，middleware 在响应后统一执行

**底层原理：** ContextVar 基于 `contextvars` 模块（Python 3.7+），每个协程有独立的上下文副本。`asyncio.create_task` 会自动 copy 当前上下文，所以子任务也能读到。但注意：**普通线程不共享 ContextVar**，如果用同步代码跑在不同线程会读不到。

---

### 3. 你的 Repository 基类是怎么实现泛型的？update 方法的 `exclude_unset=True` 有什么作用？

**面试官考察点：** 对 Python 泛型、Pydantic partial update 机制的理解。

**期望回答：**

`RepositoryBase[ModelType, CreateSchemaType, UpdateSchemaType]` 用 Python 泛型实现类型安全的 CRUD 基类。子类指定具体类型后，IDE 能推导出方法签名。

`update(id, obj_in)` 关键逻辑：
```python
obj_in.model_dump(exclude_unset=True, exclude={"id"})
```

`exclude_unset=True` 的作用：Pydantic v2 中，未传的字段保持"未设置"状态。用这个参数可以实现 **PATCH 语义**——只更新客户端实际传了的字段，没传的保持原值。如果用 `exclude_defaults=True`，当客户端显式传了默认值（比如 `priority=0`）也会被排除，导致更新丢失。

`exclude={"id"}` 防止主键被意外修改。

---

### 4. 前端动态路由是怎么从后端菜单数据生成的？组件是怎么映射的？

**面试官考察点：** 对前后端权限路由配合机制的理解。

**期望回答：**

1. 用户登录后，前端调用 `/api/v1/base/usermenu` 获取该用户可见的菜单树
2. `permissionStore.generateRoutes()` 调用 `buildRoutes()` 递归转换菜单数据
3. 父菜单分配 `Layout` 组件，子菜单通过 `import.meta.glob('../views/**/*.vue')` 动态加载对应视图组件
4. 路由通过 `router.addRoute()` 动态注册，未注册的路由 404

关键细节：
- `vueModules` 是 Vite 的 `import.meta.glob`，编译时生成模块映射表，运行时按路径懒加载
- 特殊路径如 `/chat/chathistory` 和 `/chat/chat` 有硬编码的组件映射
- 同时获取 `accessApis` 存入 store，用于按钮级 `v-permission` 指令判断

---

### 5. 前端 token 刷新机制是怎么防止并发请求同时触发 refresh 的？

**面试官考察点：** 对 token 刷新并发控制的理解。

**期望回答：**

用了 **锁 + 队列** 模式：

1. `isRefreshing` 变量作为锁，初始 `false`
2. 收到 401 时，如果 `isRefreshing === false`，设为 `true`，发起 refresh 请求
3. 同时创建一个 Promise，将 `resolve` 存入 `pendingRequests` 队列
4. 后续其他 401 请求不发 refresh，而是将 resolve 也推入队列，等待
5. refresh 成功后：更新 token，遍历 `pendingRequests` 逐个 resolve 并重放
6. refresh 失败：`forceLogout()` 清空状态

这个模式保证了 **refresh 请求只发一次**，所有并发请求复用同一个 refresh 结果。类似"请求合并"的思想。

---

### 6. 审计日志 middleware 为什么用纯 ASGI 而不是 BaseHTTPMiddleware？

**面试官考察点：** 对 ASGI 中间件机制和 FastAPI 中间件陷阱的理解。

**期望回答：**

FastAPI 的 `BaseHTTPMiddleware` 有个已知问题：它会 **消费 request body**。当它读取 body 后，后续的 middleware 或 endpoint 再读就会报错，因为 ASGI 的 `receive` callable 只能调用一次。

纯 ASGI 实现的做法：
1. 对非 multipart 请求，调用 `receive` 读取 body，然后用闭包 `inner_receive` 重复提供已缓存的 body
2. 对 multipart/octet-stream，**直接透传原始 `receive`**，避免破坏文件上传流
3. `send` 包装器捕获响应状态码、headers、body chunks

还做了：
- 敏感字段（password, token, secret, api_key）用 `******` 掩码
- 响应体超 1MB 截断
- 审计日志列表接口的 `response_body` 置空，防止递归记录

---

### 7. 你的 closure table 部门树查询是怎么工作的？和递归 CTE 相比有什么优劣？

**面试官考察点：** 对树形数据存储方案的理解深度。

**期望回答：**

`DeptClosure` 表存储所有 ancestor-descendant 对及其 level。新增部门时：
```python
# 对每个祖先，创建一条指向新部门的记录，level + 1
INSERT INTO dept_closure (ancestor, descendant, level)
SELECT ancestor, {new_id}, level + 1 FROM dept_closure WHERE descendant = {parent_id}
UNION ALL
SELECT {new_id}, {new_id}, 0  -- 自引用，level=0
```

查询某部门所有子部门：
```sql
SELECT * FROM dept_closure WHERE ancestor = {dept_id}
```

**vs 递归 CTE：**
| | Closure Table | 递归 CTE |
|---|---|---|
| 查询性能 | O(1) 索引查找 | O(depth) 递归 |
| 写入成本 | 需维护多条关联记录 | 只改 parent_id |
| 空间 | 额外存储所有路径对 | 无额外空间 |
| 适用场景 | 读多写少 | 写多读少 |

项目选 closure table 是因为部门树 **读多写少**（查权限、查组织架构），且树深度有限。

---

### 8. Pydantic v2 的 `model_dump` 和 v1 的 `dict()` 有什么关键区别？你的项目中有哪些地方利用了 v2 特性？

**面试官考察点：** 对 Pydantic 版本迁移和 v2 新特性的理解。

**期望回答：**

关键区别：
- v2 用 Rust 实现核心验证逻辑，性能提升 5-50 倍
- `dict()` → `model_dump()`，`schema()` → `model_json_schema()`
- v2 的 `model_dump(exclude_unset=True)` 行为更精确：只有客户端显式传了的字段才标记为"已设置"
- v2 用 `model_validator` 替代 v1 的 `validator(..., pre=True)`

项目中的 v2 特性使用：
- `RepositoryBase.update` 用 `model_dump(exclude_unset=True, exclude={"id"})` 实现 partial update
- `JWTPayload` schema 用于 JWT payload 编解码
- Settings 用 `pydantic-settings` 管理环境变量（虽然项目当前是普通 class）

---

### 9. `argon2` 密码哈希和 `bcrypt` 相比有什么优势？为什么选它？

**面试官考察点：** 对密码哈希算法选型的理解。

**期望回答：**

`passlib` 默认 scheme 是 `bcrypt`，项目用了 `argon2`（2015 年密码哈希竞赛 winner）。

优势：
1. **抗 GPU/ASIC 攻击：** argon2id 可配置内存消耗，GPU 并行计算优势被大幅削弱
2. **可调参数：** 时间成本、内存成本、并行度三个维度独立调节
3. **bcrypt 有 72 字节截断问题：** 超长密码会被截断，argon2 无此限制

项目中的配置：passlib 的 argon2 scheme 默认参数 `rounds=3, memory_cost=65536, parallelism=4`。

---

### 10. 你项目里同时有 `ChatHistory` 和 `Conversation` + `ConversationMessage` 两套聊天记录模型，为什么这么设计？

**面试官考察点：** 对数据模型设计意图的理解。

**期望回答：**

两套模型服务于不同场景：

- `ChatHistory`：原始聊天流水，按 `username` + `role` + `content` + `timestamp` 存储，主要用于 **系统管理后台的聊天记录查看**，是扁平的、不可编辑的
- `Conversation` + `ConversationMessage`：面向用户的 **对话管理**，支持创建、切换、重命名、删除对话，`ConversationMessage` 有外键级联删除。用于 Agent Chat 的会话持久化

分离原因：
1. `ChatHistory` 是早期模型，`Conversation` 是后来加的，两套共存是渐进式重构
2. 管理员看全局日志 vs 用户看自己的对话，权限和查询模式不同
3. `Conversation` 支持 `message_count` 等元数据，`ChatHistory` 没有

---

### 11. `to_dict` 方法里 `m2m=True` 时用 `asyncio.gather` 并发获取 M2M 字段，这有什么潜在问题？

**面试官考察点：** 对 ORM 懒加载、N+1 问题、并发查询风险的理解。

**期望回答：**

`to_dict(m2m=True)` 的实现：
```python
if m2m:
    fields = [getattr(self, field.name) for field in self._meta.m2m_fields]
    await asyncio.gather(*[field.all() for field in fields])
```

潜在问题：
1. **N+1 查询：** 如果对列表中的每个对象都调用 `to_dict(m2m=True)`，每个对象都会发起独立的 M2M 查询，性能灾难
2. **无限制并发：** M2M 字段数量不可控时，`gather` 的并发数没有上限
3. **Tortoise ORM 的 M2M 查询不走连接池复用：** 每个 M2M 字段是一个独立的 SQL 查询

项目中的缓解：列表接口通常不传 `m2m=True`，只在详情页使用。

---

### 12. 前端 `useCRUD` composable 是怎么抽象增删改查的？`modalAction` 的状态机是怎样的？

**面试官考察点：** 对 Vue 3 Composition API 抽象能力的理解。

**期望回答：**

`useCRUD` 封装了 Naive UI 弹窗表单的完整生命周期：

状态机：
```
modalAction: 'add' | 'edit' | 'view'
    ↓ handleAdd() → modalAction = 'add', 弹窗
    ↓ handleEdit(row) → modalAction = 'edit', 填充表单, 弹窗
    ↓ handleView(row) → modalAction = 'view', 只读模式, 弹窗
    ↓ handleSave() → 根据 modalAction 分发:
        'add' → doCreate(data)
        'edit' → doUpdate(id, data)
    ↓ handleDelete(id) → 确认弹窗 → doDelete(id)
```

配合 Naive UI 的 `n-form` 校验规则，`handleSave` 先触发 `formRef.value.validate()`，通过后才发请求。

---

### 13. Aerich 迁移失败时你的 `init_db` 做了什么兜底处理？为什么需要 `_ensure_business_tables`？

**面试官考察点：** 对数据库迁移容错机制的理解。

**期望回答：**

`init_db` 的容错链：
1. 先尝试 `aerich migrate`，如果失败（`AttributeError`），**删除整个 migrations 目录并重建**
2. 再尝试 `aerich upgrade`，如果失败，log 并继续（不阻塞启动）
3. 最后调用 `_ensure_business_tables()`，用 **原生 SQL `CREATE TABLE IF NOT EXISTS`** 兜底创建业务表

为什么需要兜底：
- Aerich 的模型检测依赖 AST 分析，模型字段变化可能导致迁移文件和实际 schema 不一致
- 业务表（TodoItem, TrackerApplication 等）是后加的，可能没有对应的迁移文件
- 原生 SQL 保证 **即使 Aerich 完全失败，核心业务表也能存在**

这是一种"宁可冗余也不丢失"的防御性设计。

---

### 14. 你的 CORS 配置是怎么做的？`allow_origins=["*"]` 有什么安全风险？

**面试官考察点：** 对 Web 安全基础的理解。

**期望回答：**

项目在 `bootstrap.py` 中配置 `CORSMiddleware`，origins 从 settings 读取。

`allow_origins=["*"]` 的风险：
1. **配合 `allow_credentials=True` 是致命组合：** 浏览器会拒绝这种配置（CORS spec 明确禁止），但如果中间件实现有 bug，可能导致凭证泄露
2. **任何域名都能发跨域请求：** 恶意网站可以伪造请求（虽然有 JWT token 保护，但降低了攻击门槛）
3. **CSRF 风险增加：** 虽然 JWT 不像 cookie 自动携带，但如果 token 存在 localStorage，XSS 攻击可以获取

项目的做法：通过环境变量配置 origins，生产环境应该指定具体域名。

---

### 15. 你的异常处理是怎么统一的？`AppError` 和 FastAPI 内置的 `HTTPException` 有什么区别？

**面试官考察点：** 对异常体系设计的理解。

**期望回答：**

项目注册了 6 个异常处理器，统一返回格式 `{"code": N, "msg": "...", "data": null}`：

- `AppError`：业务异常，自定义 code（如 400, 404, 500），用于业务逻辑错误
- `HTTPException`：FastAPI 内置，HTTP 层面异常
- `DoesNotExist`：Tortoise ORM 找不到记录
- `IntegrityError`：数据库约束违反（唯一键、外键等）
- `RequestValidationError`：请求参数校验失败，返回具体字段错误
- `ResponseValidationError`：响应数据不符合 schema

区别：`HTTPException` 是 HTTP 层的，`AppError` 是业务层的。项目用 `AppError` 统一业务错误，避免在 Service/Repository 层依赖 FastAPI 的 `HTTPException`，保持层间解耦。

---

## 二、架构设计（15 题）

### 16. 你为什么同时保留了 AgentExecutor（legacy）和 LangGraph 两套 Agent 执行路径？它们的差异在哪？

**面试官考察点：** 对架构演进决策的理解，是否理解技术债务。

**期望回答：**

历史原因：项目初期用 `AgentExecutor`（简单的 if-else 路由 + 工具分发），后来引入 LangGraph 做状态机化。

核心差异：

| | AgentExecutor | LangGraph |
|---|---|---|
| 流程控制 | 硬编码 if-else | 声明式图（节点 + 条件边） |
| 多步推理 | 只有 workflow 模式（RAG→Todo） | 通用循环，最多 3 次迭代 |
| 状态管理 | 函数局部变量 | `JobAssistantState` 结构化状态 |
| 可扩展性 | 加新流程要改代码 | 加节点 + 边即可 |

前端默认 `useLangGraph = true`，legacy 路径保留用于：
- LangGraph 依赖出问题时的降级
- 简单场景的快速响应（LangGraph 有额外开销）

**技术债：** 两套路径共享 `TOOL_MAP`，但逻辑重复（intent routing、response building），维护成本高。理想状态是统一到 LangGraph。

---

### 17. 你的 LangGraph 状态机中 `should_continue` 的条件判断逻辑是怎样的？为什么限制最大 3 次迭代？

**面试官考察点：** 对 Agent 循环控制和防无限循环的理解。

**期望回答：**

`should_continue` 的判断：
```python
if state["need_more"] and state["iteration"] < state["max_iterations"]:
    if state["intent"] == "workflow":
        return "workflow_continue"
    return "tool_selector"  # 循环回 intent_router
else:
    return "response_builder"
```

三条路径：
1. `workflow_continue`：workflow 意图第 1 次迭代后，自动执行 todo_tool
2. `tool_selector`：需要更多工具调用，回到 intent_router 重新路由
3. `response_builder`：结束循环，生成最终回答

**为什么 3 次：**
- 防无限循环（LLM 可能反复判断 need_more=True）
- 每次迭代有 LLM 调用成本（intent 分类 + 工具执行 + 可能的 RAG）
- 实际业务场景不需要超过 3 步：意图分类 → 工具执行 → 可能的 workflow 组合
- 3 次是经验值，平衡了能力和成本

---

### 18. 你的 RAG 系统的 hybrid search 是怎么融合向量搜索和关键词搜索的？RRF 的 k=60 是怎么选的？

**面试官考察点：** 对 RAG 检索融合策略的深度理解。

**期望回答：**

`hybrid_search` 实现：
1. **向量搜索：** ChromaDB cosine similarity，top_k=20
2. **关键词搜索：** ChromaDB 的 `$contains` 过滤器，匹配 query 中的关键词
3. **融合算法：** Reciprocal Rank Fusion (RRF)

RRF 公式：
```
score(d) = Σ 1 / (k + rank_i(d))
```

对每个文档 d，在每个检索结果列表中取 `1/(k + rank)`，求和。k 是平滑参数。

**k=60 的选择：**
- 原始论文（Cormack et al., 2009）推荐 k=60
- k 越大，排名靠后的文档惩罚越小，结果越平滑
- k 越小，头部文档优势越大
- 60 是大量实验的经验值，适合大多数场景

项目中：向量搜索擅长语义匹配，关键词搜索擅长精确匹配（如公司名、职位名）。RRF 融合后两者互补。

---

### 19. Query Rewrite 为什么要生成 2-3 个替代查询？直接用原始查询不行吗？

**面试官考察点：** 对 RAG query 改写价值的理解。

**期望回答：**

直接用原始查询的问题：
1. **词汇鸿沟：** 用户表述和文档表述不同（如"找工作" vs "求职" vs "就业"）
2. **意图模糊：** "面试"可能是想了解面试技巧，也可能是想模拟面试
3. **信息不足：** "薪资"缺少行业、岗位、城市等限定条件

Query Rewrite 生成 2-3 个替代查询从不同角度覆盖：
- 同义改写："怎么谈薪资" → "薪资谈判技巧" + "offer 谈判策略"
- 细化补充："前端面试" → "React 面试题" + "JavaScript 八股文"
- 多个查询分别检索后合并去重，提高召回率

**成本权衡：** 多一次 LLM 调用（query rewrite）+ 多次检索，换来召回率提升。项目通过 `RAG_ENABLE_QUERY_REWRITE` 开关控制。

---

### 20. 你为什么用文件系统存储面试模拟会话而不是数据库？

**面试官考察点：** 对存储选型权衡的理解。

**期望回答：**

`interview_sim_tool.py` 用 JSON 文件存储会话：`data/interview_sim/{user_id}/{session_id}.json`

选文件系统的理由：
1. **数据结构简单：** 会话就是消息列表 + 元数据，JSON 天然适合
2. **无额外依赖：** 不需要额外的表和迁移
3. **便于调试：** 直接打开文件查看会话内容
4. **生命周期短：** 面试模拟是临时性的，不需要长期持久化

缺点：
1. **并发问题：** 多个请求同时写同一文件会冲突（无文件锁）
2. **查询困难：** 无法高效查询"某用户的所有会话"，需要遍历目录
3. **无事务保证：** 写入中途崩溃会损坏文件
4. **扩展性差：** 分布式部署时文件不共享

如果要上生产，应该迁移到数据库或 Redis。

---

### 21. `JobAgent.full_pipeline` 中用了多层 `asyncio.gather` 并行，如果其中一步失败怎么办？

**面试官考察点：** 对异步错误处理和 partial failure 的理解。

**期望回答：**

`full_pipeline` 的并行结构：
```python
# 第一层
resume_result, jd_result = await asyncio.gather(analyze_resume, analyze_jd)
# 第二层
match_result, summary = await asyncio.gather(calculate_match, get_summary)
# 第三层
optimized, plan = await asyncio.gather(optimize_with_rag, generate_plan)
```

`asyncio.gather` 默认行为：**一个失败，全部取消**。它会抛出第一个异常，其他 task 被 cancel。

风险：
1. 如果 `analyze_jd` 失败，`analyze_resume` 的结果也丢失（虽然它可能成功了）
2. 已经完成的 LLM 调用结果白费（成本浪费）

改进方案（项目未实现）：
```python
results = await asyncio.gather(*tasks, return_exceptions=True)
# 检查每个结果是否为 Exception，部分失败时降级处理
```

---

### 22. 你的工具注册表（TOOL_MAP）为什么用模块级单例而不是每次请求创建？

**面试官考察点：** 对单例模式适用场景和 Python 模块加载机制的理解。

**期望回答：**

`registry.py` 中：
```python
TOOL_MAP: dict[str, BaseTool] = create_default_tools()
```

Python 模块是单例的——`import` 只执行一次，后续引用同一个对象。所以 `TOOL_MAP` 天然是全局单例。

为什么这样设计：
1. **工具无状态：** 所有工具继承 `BaseTool`，只有 `name` 属性和 `run` 方法，没有请求级别的状态
2. **避免重复初始化：** 工具实例化不需要数据库连接或 HTTP 客户端，但避免每次请求都创建对象
3. **共享引用：** `AgentExecutor` 和 `langgraph_nodes` 都引用同一个 `TOOL_MAP`，修改一处全局生效

潜在问题：如果工具变成有状态的（如持有数据库连接），单例模式需要改成请求级别的工厂模式。

---

### 23. 你项目中的分层架构（API → Controller → Repository → Model）各层职责边界是什么？有没有边界模糊的地方？

**面试官考察点：** 对分层架构的理解深度，是否知道边界模糊的常见陷阱。

**期望回答：**

各层职责：
- **API 层：** 路由定义、请求参数校验、依赖注入（鉴权/权限）、调用 Controller
- **Controller 层：** 业务编排、事务管理、调用多个 Repository/Service 协调
- **Repository 层：** 单表数据访问，封装 ORM 查询，不包含业务逻辑
- **Model 层：** 数据结构定义、字段约束、ORM 关系声明

边界模糊的地方：
1. **Service 和 Repository 混淆：** 项目中 `UserService` 既有业务逻辑（authenticate、reset_password）又有数据访问（直接调 repo）。这是合理的 Service 封装
2. **Business Service 是薄封装：** `todo_service`、`tracker_service` 等只是 Repository 的简单代理，没有额外逻辑。这种情况下 Service 层价值有限
3. **Repository 的 search 参数：** 接收 `Q()` 对象，调用方需要知道 ORM 查询语法，泄露了实现细节

---

### 24. 你为什么在配置管理上同时用 `.env` 文件和数据库 `sys_config` 表？

**面试官考察点：** 对配置管理分层设计的理解。

**期望回答：**

分层设计：
- **`.env` 文件：** 基础设施配置（数据库连接、密钥、CORS），部署时确定，不需要运行时修改
- **`sys_config` 表：** 业务配置（LLM 模型、温度、RAG 开关），管理员可在 UI 上修改，实时生效

`call_llm()` 的优先级：数据库值 > settings 默认值

优点：
1. AI 配置可以不重启服务就切换模型
2. 管理员在 UI 上调整参数，降低运维门槛
3. 敏感配置（SECRET_KEY、DB 密码）不在数据库中，减少泄露面

---

### 25. 你的 Agent 系统中"个性化推荐"是怎么实现的？为什么需要从历史对话中提取用户偏好？

**面试官考察点：** 对 Agent 记忆和个性化机制的理解。

**期望回答：**

`build_personalized_recommendation` 流程：
1. 读取用户最近 20 条记忆（MemoryItem）
2. 如果不足 3 条，跳过（冷启动问题）
3. 用 LLM 从历史中提取结构化偏好：行业、岗位、城市、技能、关注点
4. 用偏好构建搜索查询，查 RAG pipeline
5. 基于检索结果 + 偏好，LLM 生成个性化推荐

为什么不能直接用关键词匹配：
- 用户说"我想找互联网的工作"，偏好是"互联网"，但 RAG 文档可能写的是"IT 行业"或"科技公司"
- LLM 提取偏好能做语义泛化

**潜在问题：**
- 每次请求都调一次 LLM 提取偏好 + 一次 RAG 搜索，延迟高
- 偏好提取结果没有缓存，相同历史重复计算
- 偏好可能过时（用户换了目标行业）

---

### 26. 你的前端 Pinia store 是怎么管理 Agent Chat 的对话生命周期的？`groupedConversations` 的分组逻辑是怎样的？

**面试官考察点：** 对前端状态管理和 UX 设计的理解。

**期望回答：**

Agent Chat Store 管理：
- `messages`：当前对话的消息列表
- `conversations`：所有对话的摘要列表
- `useLlmRouter` / `useLangGraph`：路由模式开关

对话生命周期：
```
创建对话 → 发消息 → 切换对话 → 重命名 → 删除
    ↓              ↓
conversation_id 存储，后续请求携带
```

`groupedConversations` 按时间分组：
- **今天：** `created_at` 是今天的对话
- **昨天：** 昨天的
- **最近 7 天：** 过去一周的
- **更早：** 其余

这是一个 computed 属性，依赖 `conversations` 数组，自动重算。前端展示为侧边栏的分组列表。

---

### 27. 你项目里的 `BackgroundTasks` 是怎么通过 ContextVar 实现的？和 FastAPI 自带的 BackgroundTasks 有什么区别？

**面试官考察点：** 对 FastAPI 后台任务机制的深入理解。

**期望回答：**

项目自定义了 `BgTasks` 类，通过 `CTX_BG_TASKS` ContextVar 传播：

1. `BackGroundTaskMiddleware` 在请求开始时创建 `BackgroundTasks` 实例，存入 ContextVar
2. 业务代码通过 `BgTasks.add_task()` 添加任务，内部从 ContextVar 取实例
3. Middleware 在响应发送后执行所有累积的任务

vs FastAPI 自带的 `BackgroundTasks`：
- FastAPI 的需要通过 `Depends` 或 endpoint 参数注入，不是所有地方都能访问
- 自定义版本通过 ContextVar，**任何层级的代码**（Repository、Service、Tool）都能添加后台任务，不需要参数传递
- FastAPI 的 BackgroundTasks 在响应后执行，自定义的也是，但时机由 middleware 控制

---

### 28. 你为什么在 `to_dict` 里手动格式化 datetime 而不是用 Pydantic 的 JSON 序列化？

**面试官考察点：** 对 ORM 序列化方案选型的理解。

**期望回答：**

`to_dict` 手动处理：
```python
if isinstance(value, datetime):
    value = value.strftime(settings.DATETIME_FORMAT)
```

为什么不交给 Pydantic：
1. **Tortoise ORM 模型不是 Pydantic 模型：** `to_dict` 直接在 ORM 对象上调用，不经过 Pydantic
2. **格式控制：** `strftime` 精确控制输出格式（如 `2024-01-01 12:00:00`），Pydantic 默认 ISO 格式
3. **M2M 字段：** Pydantic 对 ORM 关系字段的序列化需要额外配置

缺点：
1. 手动序列化容易遗漏字段
2. 类型转换逻辑散落在 `to_dict` 中
3. 无法利用 Pydantic 的校验能力

更好的方案：用 `tortoise.contrib.pydantic` 的 Pydantic 模型自动转换。

---

### 29. 你的项目中哪些地方用了 `prefetch_related`？这和 `select_related` 有什么区别？

**面试官考察点：** 对 ORM 关联查询优化的理解。

**期望回答：**

项目中 `prefetch_related` 的使用：
- `PermissionControl.has_permission` 中加载用户角色的 API：`user.roles.all().prefetch_related("apis")`

区别（Tortoise ORM）：
| | select_related | prefetch_related |
|---|---|---|
| SQL 方式 | JOIN，一次查询 | 分别查询，Python 端合并 |
| 适用关系 | FK（多对一） | M2M（多对多）、反向 FK |
| N+1 问题 | 解决 | 解决 |
| 查询次数 | 1 次 | N+1 次（但比不用好） |

项目中 M2M 关系（User↔Role, Role↔Menu, Role↔Api）都用 `prefetch_related`，因为 M2M 无法用 JOIN 一次查完。

---

### 30. 你的 Rerank 步骤用 LLM 做而不是专门的 Rerank 模型，这有什么利弊？

**面试官考察点：** 对 RAG pipeline 优化的理解。

**期望回答：**

当前实现：给 LLM 一个 prompt，让它从检索结果中选出 top-N 最相关的。

优点：
1. **零额外依赖：** 不需要部署 cross-encoder 模型
2. **语义理解强：** LLM 能理解复杂的查询-文档相关性
3. **灵活：** 可以通过 prompt 调整排序标准

缺点：
1. **延迟高：** LLM 推理比 cross-encoder 慢 10-100 倍
2. **成本高：** 每次 rerank 消耗 token
3. **一致性差：** LLM 输出不稳定，相同输入可能得到不同排序
4. **上下文限制：** 文档数量多了放不进 context window

更好的方案：
- 用 `bge-reranker` 或 `cohere rerank` API，延迟低、成本低、效果更好
- 作为项目优化方向

---

## 三、拔高底层（15 题）

### 31. ASGI 中间件的 `receive`/`send` 包装是怎么实现的？闭包在其中起什么作用？

**面试官考察点：** 对 ASGI 协议和 Python 闭包的深度理解。

**期望回答：**

ASGI 应用的签名：`async def app(scope, receive, send)`

- `receive`：异步 callable，返回 `{"type": "http.request", "body": b"..."}`
- `send`：异步 callable，接收 `{"type": "http.response.start", ...}` 和 `{"type": "http.response.body", ...}`

审计中间件的包装：

```python
# 缓存 body
body = b""
message = await receive()
body = message.get("body", b"")

# 闭包：重复提供已缓存的 body
async def inner_receive():
    return {"type": "http.request", "body": body}

# 用 inner_receive 替代原始 receive 传给下游
await app(scope, inner_receive, send)
```

闭包的作用：`inner_receive` 捕获了外层的 `body` 变量，形成闭包。每次调用都返回相同的数据，实现了"重放"效果。

`send` 包装器同理，通过闭包捕获响应数据：
```python
async def send_wrapper(message):
    if message["type"] == "http.response.body":
        # 捕获响应 body
        response_body += message.get("body", b"")
    await send(message)
```

---

### 32. `asyncio.gather` 的异常传播机制是怎样的？`return_exceptions=True` 和默认行为有什么区别？

**面试官考察点：** 对 Python 异步编程核心机制的理解。

**期望回答：**

默认行为（`return_exceptions=False`）：
- 某个 task 抛异常时，`gather` **立即抛出该异常**
- 其他 task **被 cancel**（发送 `CancelledError`）
- 已完成的 task 结果丢失

`return_exceptions=True`：
- 所有 task 都会完成（即使抛异常）
- 异常对象作为对应位置的返回值
- `results[i]` 要么是正常值，要么是 Exception 实例

项目中 `full_pipeline` 用默认行为，意味着：
- `analyze_resume` 成功但 `analyze_jd` 失败 → 整个 pipeline 失败
- 已经消耗的 LLM token 白费

**底层原理：** `gather` 内部维护一个 `_children_tasks` 列表。当某个 task 完成时，检查是否异常。默认模式下异常直接 re-raise；`return_exceptions=True` 下把异常 append 到结果列表。

---

### 33. Python 的 `contextvars` 在 `asyncio.create_task` 时是怎么传播的？手动创建线程呢？

**面试官考察点：** 对 Python 上下文模型在并发场景下的理解。

**期望回答：**

`contextvars` 的传播规则：

1. **asyncio.create_task：** 自动 copy 当前协程的上下文到新 task。新 task 对 ContextVar 的修改**不影响**父协程
2. **asyncio.gather：** 同上，每个 task 有独立的上下文副本
3. **手动线程（threading.Thread）：** **不传播**。新线程有空的上下文，读 ContextVar 会拿到默认值
4. **线程池（loop.run_in_executor）：** Python 3.12+ 自动 copy 上下文；3.12 之前不传播

项目中的影响：
- `CTX_USER_ID` 在 `is_authed` 中设置后，`asyncio` 体系内都能读到
- 如果用了 `run_in_executor` 跑同步数据库查询（Tortoise ORM 不会这样做），需要手动 copy 上下文

---

### 34. ChromaDB 的 HNSW 索引是什么？cosine 距离和欧氏距离在你的场景下有什么区别？

**面试官考察点：** 对向量数据库底层索引的理解。

**期望回答：**

HNSW（Hierarchical Navigable Small World）：
- 多层图结构，每层是 proximity graph
- 搜索从最顶层开始，逐层贪心下降到最近邻
- 时间复杂度 O(log N)，空间复杂度 O(N * M)（M 是每个节点的邻居数）

cosine vs 欧氏距离：
- **cosine：** 衡量方向相似性，不受向量模长影响。适合文本 embedding（因为文本长度不同，模长不代表相似性）
- **欧氏距离：** 衡量绝对距离，受模长影响

项目用 cosine 是因为 DashScope 的 `text-embedding-v3` 输出的向量没有归一化，cosine 距离更稳定。

ChromaDB 默认用 cosine 时会自动归一化向量，内部用内积计算（归一化后 cosine = 内积）。

---

### 35. Tortoise ORM 的 `BigIntField(pk=True)` 和自增 ID 相比有什么优劣？为什么不用 UUID？

**面试官考察点：** 对主键选型的深度理解。

**期望回答：**

`BigIntField(pk=True)` 的特点：
- Tortoise ORM 默认用 `BIGINT` + 自增（数据库序列）
- 8 字节，范围 -2^63 到 2^63-1

vs 自增 INT：
- INT 4 字节，上限约 21 亿，大数据量可能溢出
- BigInt 更安全，几乎不会溢出

vs UUID：
| | BigInt 自增 | UUID |
|---|---|---|
| 大小 | 8 bytes | 16 bytes |
| 可读性 | 好（1, 2, 3...） | 差（随机字符串） |
| 分布式 | 需要号段或雪花算法 | 天然全局唯一 |
| 索引性能 | B+树顺序插入，性能好 | 随机插入，页分裂 |
| 信息泄露 | 可推测数量和增长 | 无 |

项目选 BigInt 因为是 **单体应用，单数据库**，不需要分布式 ID 生成。自增 ID 简单高效。

---

### 36. 你项目中 LLM 调用的 timeout 机制是怎样的？如果 LLM 服务不可用会怎样？

**面试官考察点：** 对超时控制和容错的理解。

**期望回答：**

`call_llm` 的 timeout 参数：
```python
async def call_llm(prompt, timeout=60):
    response = await asyncio.wait_for(
        async_client.chat.completions.create(...),
        timeout=timeout
    )
```

`asyncio.wait_for` 包裹了 OpenAI SDK 的异步调用，超时后抛 `TimeoutError`。

前端也有 timeout：
- `chat-core.js` 的 Axios 实例 timeout=120s（120000ms）
- 普通 API 的 Axios 实例用默认 timeout

如果 LLM 服务不可用：
1. `call_llm` 抛 `TimeoutError` 或 `openai.APIConnectionError`
2. 工具的 `run` 方法没有 catch，异常向上传播
3. `tool_executor_node` 没有 try-catch，异常会中断整个 LangGraph 执行
4. 最终返回 500 错误

**缺失的容错：**
- 没有重试机制（应该用 `tenacity` 或指数退避）
- 没有降级策略（LLM 不可用时应该返回缓存结果或友好提示）
- 没有熔断器（LLM 持续超时时应该快速失败）

---

### 37. 你的 semantic chunker 是怎么处理中文文本的？和英文分词有什么本质区别？

**面试官考察点：** 对中文 NLP 特殊性的理解。

**期望回答：**

`semantic_chunk` 的分割策略：
1. 先按 `\n\n`（段落）分割
2. 段落超 max_size 时，按中文句号 `。` 分割
3. 还超，按逗号 `，` 分割
4. 最后按固定长度截断（fallback）

中文 vs 英文分词的本质区别：
- **英文有天然空格分隔：** "Hello World" 是两个 token
- **中文没有空格：** "你好世界" 是一个整体，需要分词
- **语义边界不同：** 英文以词为单位，中文以字/词为单位

项目 chunker 的局限：
1. **没有 overlap：** 相邻 chunk 没有重叠，跨 chunk 的语义信息会丢失
2. **纯规则分割：** 不考虑语义边界，可能把一个完整的句子切开
3. **中文标点依赖：** 如果文档用了英文标点（`...`, `.`），分割会失败

更好的方案：用 `langchain.text_splitter.RecursiveCharacterTextSplitter` 配合中文分隔符。

---

### 38. 你的 embedding 批处理（batch_size=6）是怎么实现的？为什么是 6 而不是更大的数？

**面试官考察点：** 对 embedding API 限制和批处理策略的理解。

**期望回答：**

`DashScopeEmbeddingFunction` 的批处理：
```python
async def _async_embed(self, texts):
    batches = [texts[i:i+batch_size] for i in range(0, len(texts), batch_size)]
    results = []
    for batch in batches:
        response = await async_client.embeddings.create(input=batch, ...)
        results.extend(response.data)
    return results
```

为什么 batch_size=6：
1. **DashScope API 限制：** `text-embedding-v3` 单次最多处理 6 条文本（官方文档限制）
2. **token 限制：** 每条文本最长 8192 tokens，6 条合计接近模型上下文上限
3. **rate limit：** 批次越大，单次请求耗时越长，容易触发限流

vs 更大的 batch：
- 更大的 batch 减少 API 调用次数，降低延迟
- 但受 API 限制，不能超过 6
- 如果要提高吞吐，可以用异步并发多个 batch（当前是顺序执行）

---

### 39. 你的项目用了 `openai` SDK 指向 DashScope，这背后的 API 兼容性是怎么实现的？有什么坑？

**面试官考察点：** 对 API 兼容层和 vendor lock-in 的理解。

**期望回答：**

DashScope（阿里云）实现了 OpenAI 兼容 API：
```python
async_client = AsyncOpenAI(
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.DASHSCOPE_BASE_URL  # https://dashscope.aliyuncs.com/compatible-mode/v1
)
```

兼容性实现：DashScope 的服务端暴露了和 OpenAI 相同的 `/chat/completions`、`/embeddings` 等端点，请求/响应格式一致。

坑：
1. **不完全兼容：** 某些参数（如 `response_format`, `tool_choice`）DashScope 可能不支持
2. **模型名不同：** OpenAI 用 `gpt-4`，DashScope 用 `qwen-turbo`
3. **embedding 维度不同：** DashScope 的 `text-embedding-v3` 是 1024 维，OpenAI 的是 1536 维
4. **rate limit 行为不同：** DashScope 的限流策略和 OpenAI 不一样
5. **流式响应：** SSE 格式可能有细微差异

好处：如果要切换到 OpenAI 或其他兼容 API，只需改环境变量。

---

### 40. 你项目中的权限检查是"每请求检查"还是"有缓存"？高频接口的性能影响？

**面试官考察点：** 对权限缓存策略和性能优化的理解。

**期望回答：**

当前实现是 **每请求检查**：
1. 每次请求都解码 JWT（CPU 计算，快）
2. 每次都查数据库加载用户（1 次 DB 查询）
3. 每次都加载用户角色的 API（1+N 次查询，有 prefetch_related 优化为 2 次）

性能影响：
- 2 次 DB 查询 / 请求，对于中等 QPS（<1000）可以接受
- 高频接口（如聊天、Agent 调用）每次都检查，有优化空间

优化方案（项目未实现）：
1. **权限缓存：** 将 `(user_id, method, path)` → `allowed` 缓存到 Redis，TTL 5 分钟
2. **JWT 自包含权限：** 把用户角色 ID 编入 JWT，权限变更时使 token 失效
3. **本地缓存：** 用 `cachetools.TTLCache` 在进程内缓存权限集合

---

### 41. 你的 Agent 最多 3 次迭代，如果工具返回的结果不准确怎么办？有没有"自我纠错"机制？

**面试官考察点：** 对 Agent 自反思和纠错能力的理解。

**期望回答：**

当前实现：**没有自我纠错机制**。流程是单向的：意图分类 → 工具执行 → 返回结果。如果工具输出不准确，直接返回给用户。

LangGraph 的 `should_continue` 检查 `need_more` 标志，但这个标志由工具自己设置，不是 Agent 评估结果质量后决定的。

缺失的环节：
1. **结果验证节点：** 检查工具输出是否合理，不合理则重试
2. **self-reflection：** 让 LLM 评估自己的回答质量
3. **备选路径：** 一个工具失败时自动切换到其他工具

改进方向：
```python
# 在 tool_executor_node 后加一个 evaluator_node
def evaluator_node(state):
    quality = llm.evaluate(state["tool_output"], state["query"])
    if quality < threshold:
        return "tool_selector"  # 重试
    return "response_builder"
```

---

### 42. 你项目中数据库连接池是怎么配置的？Tortoise ORM 的连接管理机制是怎样的？

**面试官考察点：** 对数据库连接池和 ORM 连接管理的理解。

**期望回答：**

Tortoise ORM 配置中没有显式设置连接池参数，使用默认值。

Tortoise ORM 的连接管理：
1. 基于 `asyncpg` 的连接池，每个数据库配置一个 pool
2. 默认 pool 大小：`min_size=1, max_size=10`
3. 连接在第一次查询时创建（惰性初始化）
4. 请求结束后连接归还 pool，不关闭

项目中的连接生命周期：
```
lifespan startup → Tortoise.init() 创建 pool
    → 每个请求从 pool 取连接
    → 查询完毕归还
lifespan shutdown → Tortoise.close_connections() 关闭 pool
```

潜在问题：
1. 默认 pool 大小可能不够（高并发时连接等待）
2. 没有配置连接超时（慢查询可能占用连接很久）
3. 没有配置连接回收（长时间空闲连接可能被数据库断开）

生产建议：配置 `pool_min_size`, `pool_max_size`, `timeout` 等参数。

---

### 43. 你的 RAG pipeline 中 context compression 用 LLM 做压缩，这和传统的截断/摘要有什么区别？

**面试官考察点：** 对 RAG context window 管理策略的理解。

**期望回答：**

当检索结果超过 `max_context_chars`（6000）时，触发 context compression：

```python
# LLM 压缩
compressed = await call_llm(
    f"从以下内容中提取与问题相关的关键信息：\n问题：{query}\n内容：{context}"
)
```

vs 截断：
- 截断：直接 `context[:6000]`，可能切断关键信息
- LLM 压缩：保留相关部分，丢弃无关部分

vs 传统摘要：
- 传统摘要（如 TextRank）：基于统计的方法，不理解语义
- LLM 压缩：理解查询意图，只保留相关信息

利弊：
| | LLM 压缩 | 截断 | 传统摘要 |
|---|---|---|---|
| 质量 | 高 | 低 | 中 |
| 延迟 | 高（1次LLM调用） | 无 | 低 |
| 成本 | 高 | 无 | 低 |
| 精确度 | 好 | 差 | 一般 |

项目通过 `RAG_ENABLE_CONTEXT_COMPRESS` 开关控制，允许在质量和成本之间权衡。

---

### 44. 你的前端在 token 刷新失败后是怎么处理的？如果刷新 token 也过期了呢？

**面试官考察点：** 对 token 生命周期和异常处理链的理解。

**期望回答：**

刷新 token 的机制：
1. Access token 有效期 30 分钟
2. Refresh token 有效期 7 天
3. 收到 401 时，用 refresh token 换新 access token

刷新失败的处理：
```javascript
// interceptors.js
catch (error) {
    forceLogout()  // 清除所有 token，重置 store，跳转登录页
}
```

如果 refresh token 也过期：
1. `/base/refresh_token` 接口返回非 200（token 无效或过期）
2. 拦截器 catch，触发 `forceLogout()`
3. 用户需要重新登录

潜在问题：
1. **没有提前刷新：** 应该在 access token 过期前主动刷新，而不是等 401
2. **并发请求的 401 风暴：** 如果同时有 10 个请求都返回 401，refresh 只触发一次（已实现），但用户体验是"卡了一下然后跳登录"
3. **refresh token 轮换：** 每次用 refresh token 换新 access token 时，应该同时返回新的 refresh token（防止 refresh token 被盗用）

---

### 45. 你的项目如果要支持 WebSocket 实时推送（如 Agent 思考过程流式输出），需要改哪些地方？

**面试官考察点：** 对实时通信架构和现有架构扩展点的理解。

**期望回答：**

需要改的地方：

**后端：**
1. 新增 WebSocket endpoint：`/api/v1/chat/agent/ws`
2. Agent 执行过程中用 `websocket.send_text()` 流式推送中间状态
3. LLM 调用改为流式（`stream=True`），逐 chunk 推送
4. 需要管理 WebSocket 连接池（用户断连、重连）

**前端：**
1. Axios 请求改为 WebSocket 连接
2. 消息列表实时追加，而不是等完整响应
3. 处理断连重连、消息去重

**架构影响：**
1. 当前的无状态 API 设计被打破，WebSocket 是有状态的
2. 多实例部署时需要 Redis Pub/Sub 做消息广播
3. 审计日志 middleware 需要适配 WebSocket 协议
4. 权限检查需要在 WebSocket 握手时做一次（不能每条消息都检查）

**Agent 部分：**
1. LangGraph 的节点执行需要改为异步回调模式
2. `response_builder` 的输出需要分段推送

---

## 四、综合追问（10 题）

### 46. 如果让你重新设计这个项目的架构，你会改什么？

**面试官考察点：** 对技术债务和架构改进方向的思考能力。

**期望回答：**

会改的点：
1. **统一 Agent 路径：** 废弃 legacy `AgentExecutor`，全部用 LangGraph
2. **引入 Redis：** 权限缓存、会话存储、LLM 结果缓存、rate limiting
3. **配置管理升级：** `.env` 改用 `pydantic-settings`，支持类型校验和默认值
4. **RAG pipeline 模块化：** chunker、retriever、reranker、compressor 都抽象为可插拔接口
5. **数据库连接池：** 显式配置 pool 大小、超时、回收策略
6. **LLM 调用加 retry：** 用 `tenacity` 实现指数退避重试
7. **前端状态持久化：** Agent Chat 的消息列表应该和后端 Conversation 同步，而不是只在内存中

不会改的：
- 分层架构（API/Controller/Repository）已经够用
- Closure table 方案适合当前场景
- ChromaDB 作为本地向量数据库够用

---

### 47. 你项目中最复杂的业务流程是哪个？画一下完整链路。

**面试官考察点：** 对复杂业务流程的梳理和表达能力。

**期望回答：**

最复杂的流程：**JobAgent.full_pipeline（求职全流程）**

```
用户上传简历 + JD
    ↓
analyze_resume ──→ 解析简历结构化数据 ┐
analyze_jd ──→ 解析 JD 结构化数据    ├─ asyncio.gather 并行
    ↓                                 ┘
calculate_match ──→ 简历-JD 匹配分析  ┐
get_resume_summary ──→ 简历摘要      ├─ asyncio.gather 并行
    ↓                                 ┘
optimize_resume_with_rag:
    ├── RAG 搜索优秀简历范例
    ├── LLM 生成优化后简历
    └── 生成匹配报告
generate_plan:
    └── LLM 生成多日求职计划
    ├─ asyncio.gather 并行
    ↓
create_todos_from_plan:
    └── 将计划拆解为 TodoItem 写入数据库
    ↓
返回完整结果（匹配分数 + 优化简历 + 求职计划 + Todo 列表）
```

总共 7 个 LLM 调用 + 2 次 RAG 搜索，分 4 个并行阶段。

---

### 48. 你的项目在高并发场景下最先扛不住的是哪个环节？

**面试官考察点：** 对系统瓶颈的分析能力。

**期望回答：**

瓶颈排序：

1. **LLM 调用：** DashScope API 有 rate limit（QPS 限制），且每次调用耗时 2-10 秒。Agent 请求一次可能触发 3-7 次 LLM 调用
2. **数据库连接池：** 默认 max_size=10，超过 10 个并发请求就等待
3. **ChromaDB：** 单机版，嵌入式运行，没有分布式能力。大量并发搜索会阻塞
4. **文件 I/O：** 面试模拟、简历导出都用文件系统，无并发控制

解决方案优先级：
1. LLM：加缓存（相似查询返回缓存结果）+ 异步队列（Celery）
2. 数据库：调大连接池 + 加 Redis 缓存
3. ChromaDB：部署独立服务或切换到 Milvus/Weaviate
4. 文件 I/O：迁移到对象存储（S3/MinIO）或数据库

---

### 49. 你项目中的安全防护有哪些？如果被渗透测试，最容易找到的漏洞是什么？

**面试官考察点：** 对安全意识和 OWASP Top 10 的理解。

**期望回答：**

现有防护：
- JWT 认证 + RBAC 权限
- 密码用 argon2 哈希
- CORS 配置
- 审计日志记录所有请求
- 敏感字段掩码

最容易找到的漏洞：

1. **SQL 注入风险低但存在：** Repository 用 ORM 参数化查询，但 `_ensure_business_tables` 用了 raw SQL（虽然是硬编码，没有用户输入）
2. **JWT secret 泄露：** `.env` 文件如果被泄露（.gitignore 没配好），攻击者可以伪造任意 token
3. **无 rate limiting：** 登录接口没有暴力破解防护，可以无限尝试密码
4. **SSRF 风险：** 如果 RAG 的文档 URL 来自用户输入，可能被利用访问内网
5. **文件上传：** `upload` 接口如果没有严格校验文件类型和大小，可能被上传恶意文件
6. **XSS：** 前端如果直接渲染 LLM 输出（Markdown），可能包含恶意脚本
7. **IDOR：** 某些接口的 user_id 来自请求参数而不是 JWT，可能越权访问

---

### 50. 如果要给这个项目加上监控和可观测性，你会怎么做？

**面试官考察点：** 对可观测性（Observability）的理解。

**期望回答：**

三层可观测性：

**1. Metrics（指标）：**
- LLM 调用延迟、成功率、token 消耗
- API 响应时间 P50/P95/P99
- 数据库查询耗时
- Agent 迭代次数分布
- 工具调用频率和耗时

工具：Prometheus + Grafana，FastAPI 用 `prometheus_fastapi_instrumentator`

**2. Logging（日志）：**
- 结构化日志（JSON 格式）
- 请求链路追踪（trace_id 贯穿 API → Agent → Tool → LLM）
- LLM prompt/response 记录（调试用）

工具：structlog + ELK 或 Loki

**3. Tracing（追踪）：**
- 每个请求生成 trace_id
- Agent 执行过程的 span（intent_router → tool_executor → response_builder）
- LLM 调用的 span（包含 prompt 长度、response 长度）

工具：OpenTelemetry + Jaeger

优先级：先加 Metrics（知道系统状态）→ 再加 Logging（调试问题）→ 最后加 Tracing（定位慢请求）。

---

## 附录：追问优先级建议

| 优先级 | 题号 | 主题 | 建议准备时间 |
|--------|------|------|------------|
| P0 必问 | 1, 2, 6, 16, 21, 31 | 权限、ContextVar、ASGI、Agent、异步、闭包 | 第一天 |
| P1 高频 | 3, 5, 17, 18, 23, 32 | 泛型、token刷新、LangGraph、RRF、分层、gather | 第二天 |
| P2 加分 | 7, 20, 30, 39, 43, 46 | 闭包表、文件存储、rerank、API兼容、compression、重构 | 第三天 |

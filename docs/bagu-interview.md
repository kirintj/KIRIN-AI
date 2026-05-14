# AI 全栈开发八股文（KIRIN-AI 技术栈）

> 覆盖：Python 异步 · FastAPI · Vue3 · PostgreSQL · Redis · LangGraph/RAG · 大模型 · 系统设计 · 场景题

---

## 一、Python 异步编程（15 题）

### 1. asyncio 的事件循环（Event Loop）是什么？它是怎么工作的？

事件循环是 asyncio 的核心调度器，负责管理和执行所有异步任务。工作流程：

1. 从任务队列取出一个协程执行
2. 遇到 `await`（如 I/O 操作）时，挂起当前协程，控制权交还事件循环
3. 事件循环检查是否有就绪的回调或完成的 I/O
4. 有就绪任务则执行，没有则阻塞等待
5. 重复上述过程直到所有任务完成

Python 3.10+ 用 `asyncio.run()` 启动事件循环，内部创建 `new_event_loop` 并 `run_until_complete`。

底层基于操作系统的 I/O 多路复用：Linux 用 `epoll`，macOS 用 `kqueue`，Windows 用 `IOCP`。

### 2. 协程、线程、进程的区别？什么时候该用哪个？

| | 协程 | 线程 | 进程 |
|---|---|---|---|
| 调度方式 | 协作式（主动让出） | 抢占式（OS 调度） | 抢占式 |
| 切换开销 | 极小（函数调用级别） | 中等（上下文切换） | 大（完整切换） |
| 并发模型 | 单线程多任务 | 多线程并行 | 多进程并行 |
| 适用场景 | I/O 密集型 | I/O 密集型 | CPU 密集型 |
| 数据竞争 | 无（单线程） | 有（需要锁） | 无（独立内存） |
| GIL 影响 | 不受影响 | 受影响 | 不受影响 |

选择原则：
- **I/O 密集型**（网络请求、数据库查询）：协程 > 线程
- **CPU 密集型**（计算、图像处理）：进程（`ProcessPoolExecutor`）
- **混合型**：协程 + 进程池

### 3. `asyncio.gather`、`asyncio.wait`、`asyncio.create_task` 有什么区别？

```python
# gather：并发执行，等待全部完成，按顺序返回结果
results = await asyncio.gather(task1, task2, task3)

# wait：更灵活，可设置超时、返回完成/未完成集合
done, pending = await asyncio.wait([task1, task2], timeout=5, return_when=asyncio.FIRST_COMPLETED)

# create_task：创建任务并立即调度执行，返回 Task 对象
task = asyncio.create_task(coro())
```

关键区别：
- `gather` 高层 API，返回结果列表，异常时默认全部取消
- `wait` 底层 API，返回 Task 集合，需要手动取结果
- `create_task` 不等待，需要手动 `await task`

### 4. Python 的 GIL 是什么？它对异步编程有影响吗？

GIL（Global Interpreter Lock）是 CPython 的全局解释器锁，同一时刻只有一个线程执行 Python 字节码。

对异步编程的影响：
- **无影响：** asyncio 是单线程的协程调度，不涉及多线程竞争，GIL 不是瓶颈
- **有影响：** 如果异步代码中调用了 CPU 密集型同步函数，会阻塞整个事件循环

解决方案：
- CPU 密集型任务用 `loop.run_in_executor(None, func)` 放到进程池
- Python 3.13+ 实验性移除 GIL（`--disable-gil` 编译选项）

### 5. `async with` 和 `async for` 是什么？什么时候需要它们？

```python
# async with：异步上下文管理器，__aenter__ 和 __aenter__ 是协程
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()

# async for：异步迭代器，__aiter__ 和 __anext__ 是协程
async for chunk in response.content:
    process(chunk)
```

使用场景：
- 资源获取/释放需要异步操作时（数据库连接、HTTP 会话、文件锁）
- 迭代数据源是异步产生时（SSE 流、消息队列消费）

### 6. `await` 的底层机制是什么？挂起和恢复是怎么实现的？

`await` 表达式的执行流程：
1. 获取 awaitable 对象的 `__await__()` 迭代器
2. 通过 `yield from`（CPython 实现）将控制权交给事件循环
3. 事件循环将当前协程注册到 I/O 等待队列
4. I/O 完成后，事件循环将协程重新加入就绪队列
5. 协程从 `yield` 处恢复执行

底层是基于 **生成器（generator）** 的协程实现。`async/await` 语法糖背后是 `yield from` 的协程协议。

### 7. Python 的 `ContextVar` 和 `threading.local` 有什么区别？

| | ContextVar | threading.local |
|---|---|---|
| 隔离粒度 | 协程上下文 | 线程 |
| asyncio 兼容 | 原生支持 | 不兼容（协程在线程内切换） |
| 传播方式 | `create_task` 自动 copy | 线程不传播 |
| Python 版本 | 3.7+ | 2.4+ |

```python
import contextvars
ctx = contextvars.ContextVar('user_id')

# 在 asyncio 中：
ctx.set(123)
task = asyncio.create_task(some_coro())  # task 内可以读到 123
# task 对 ctx 的修改不影响父协程
```

### 8. 如何调试异步代码？`asyncio` 的常见陷阱有哪些？

常见陷阱：
1. **忘记 await：** 调用协程不加 await，得到 coroutine 对象而不是结果，且不会执行
2. **阻塞事件循环：** 在协程中调用同步阻塞函数（`time.sleep`、同步 HTTP 请求）
3. **异常吞没：** 未 await 的 task 抛异常时，只有 `Task exception was never retrieved` 警告
4. **死锁：** 在协程中用 `threading.Lock`（应该用 `asyncio.Lock`）

调试工具：
- `PYTHONASYNCIODEBUG=1` 环境变量开启 debug 模式
- `asyncio.all_tasks()` 查看所有活跃任务
- `loop.slow_callback_duration` 设置慢回调阈值

### 9. 什么是 `asyncio.Semaphore`？什么场景下需要它？

信号量用于限制并发数量：

```python
sem = asyncio.Semaphore(10)  # 最多 10 个并发

async def fetch(url):
    async with sem:
        return await aiohttp.get(url)

# 100 个请求，但同时只有 10 个在执行
await asyncio.gather(*[fetch(url) for url in urls])
```

场景：
- 限制对外部 API 的并发调用（避免触发 rate limit）
- 限制数据库连接数
- 限制文件并发写入

### 10. `run_in_executor` 是什么？什么时候用它？

将同步函数放到线程池/进程池执行，避免阻塞事件循环：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    ThreadPoolExecutor(),  # None 用默认线程池
    sync_blocking_function, arg1, arg2
)
```

使用场景：
- 调用不支持异步的第三方库（如 `requests`、`pillow`）
- CPU 密集型计算（用 `ProcessPoolExecutor`）
- 文件 I/O（Python 的文件操作不支持 async）

### 11. asyncio 的 `Queue` 怎么用？和 `multiprocessing.Queue` 有什么区别？

```python
queue = asyncio.Queue(maxsize=100)

async def producer():
    await queue.put(item)

async def consumer():
    item = await queue.get()
    queue.task_done()
```

区别：
- `asyncio.Queue`：协程间通信，单进程内，`put`/`get` 是协程
- `multiprocessing.Queue`：进程间通信，跨进程，基于管道+锁

### 12. Python 3.11+ 的 `TaskGroup` 和 `gather` 有什么区别？

```python
# Python 3.11+
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(coro1())
    task2 = tg.create_task(coro2())
# 退出时自动等待所有任务完成

# 如果任何一个任务抛异常，TaskGroup 会取消所有其他任务并抛 ExceptionGroup
```

vs `gather`：
- `TaskGroup` 是结构化并发，异常处理更清晰
- `gather` 的异常处理不直观（第一个异常被抛出，其他被取消但不报错）
- `TaskGroup` 的 `ExceptionGroup` 可以捕获多个异常

### 13. 什么是协程的"取消"？`task.cancel()` 是怎么工作的？

```python
task = asyncio.create_task(long_running())
task.cancel()  # 发送 CancelledError

try:
    await task
except asyncio.CancelledError:
    print("task was cancelled")
```

取消机制：
1. `cancel()` 设置任务的取消标志
2. 任务在下一个 `await` 点收到 `CancelledError`
3. 任务可以用 `try/except` 捕获并清理资源
4. `shield()` 可以防止被取消：`await asyncio.shield(critical_op())`

### 14. `asyncio` 和 `trio`/`anyio` 有什么区别？为什么 FastAPI 选择 asyncio？

`trio` 是结构化并发库，强调"所有并发必须有明确的作用域"。

FastAPI 选择 asyncio 因为：
1. 标准库，无额外依赖
2. 生态成熟（uvicorn、httpx、tortoise-orm 都基于它）
3. Starlette（FastAPI 底层）基于 asyncio 构建

`anyio` 是兼容层，可以同时支持 asyncio 和 trio。FastAPI 的 `TestClient` 内部用了 `anyio`。

### 15. 如何实现异步生成器？它和普通生成器有什么区别？

```python
async def async_generator():
    for i in range(10):
        await asyncio.sleep(0.1)
        yield i

async for item in async_generator():
    print(item)
```

区别：
- 普通生成器用 `yield`，同步迭代
- 异步生成器用 `yield`，但 `__aiter__`/`__anext__` 是协程
- 异步生成器不能 `return` 值（`StopAsyncIteration` 不携带值）

---

## 二、FastAPI（20 题）

### 1. FastAPI 的依赖注入系统是怎么工作的？

FastAPI 的依赖注入基于函数签名的类型注解：

1. 解析路径函数的参数，识别 `Depends` 声明
2. 递归解析依赖的依赖，构建依赖树
3. 按拓扑顺序执行依赖函数，将结果注入参数
4. 同一个请求内，相同依赖默认缓存（`use_cache=True`）

```python
async def get_db():
    async with Session() as session:
        yield session

async def get_user(db=Depends(get_db), token=Depends(verify_token)):
    return await db.get(User, token.user_id)

@app.get("/me")
async def me(user=Depends(get_user)):
    return user
```

### 2. FastAPI 的中间件执行顺序是怎样的？

中间件是"洋葱模型"：请求从外到内，响应从内到外。

```
请求 → CORS → BackgroundTask → AuditLog → 路由处理
响应 ← CORS ← BackgroundTask ← AuditLog ← 路由处理
```

注册顺序决定执行顺序，先注册的在外层。异常处理在中间件内层。

ASGI 中间件 vs `BaseHTTPMiddleware`：
- ASGI 直接操作 `scope`/`receive`/`send`，更底层更灵活
- `BaseHTTPMiddleware` 封装了 Request/Response 对象，但有 body 消费问题

### 3. FastAPI 的 `BackgroundTasks` 是怎么实现的？它可靠吗？

实现原理：
1. `BackgroundTasks` 对象在请求处理期间累积任务函数
2. 响应发送后，Starlette 的中间件执行所有累积的任务
3. 任务在同一个进程中执行，不是独立的 worker

可靠性问题：
- **不保证执行：** 如果进程崩溃，任务丢失
- **无重试机制：** 任务失败不会重试
- **阻塞风险：** 长时间运行的任务会占用 worker

生产建议：用 Celery/Redis Queue 替代，保证任务可靠执行。

### 4. FastAPI 的 `yield` 依赖和普通依赖有什么区别？

```python
# 普通依赖：返回值
async def get_token(token: str = Header()):
    return token

# yield 依赖：上下文管理，退出时执行清理
async def get_db():
    db = Session()
    try:
        yield db
    finally:
        await db.close()
```

yield 依赖的执行流程：
1. yield 之前的代码在请求处理前执行（获取资源）
2. yield 的值注入到路径函数
3. yield 之后的代码在响应发送后执行（释放资源）
4. 如果请求处理中发生异常，yield 之后的代码仍会执行（类似 finally）

### 5. FastAPI 的路径参数、查询参数、请求体是怎么区分的？

```python
@app.put("/items/{item_id}")
async def update(
    item_id: int,              # 路径参数：在路径中
    q: str = None,             # 查询参数：有默认值，不在路径中
    item: Item = None,         # 请求体：Pydantic 模型
    token: str = Header(),     # Header：用 Header() 声明
    cookie_val: str = Cookie() # Cookie：用 Cookie() 声明
):
```

区分规则：
- 路径中有 `{name}` → 路径参数
- 类型是 Pydantic 模型 → 请求体
- 有默认值的简单类型 → 查询参数
- 用 `Header()`/`Cookie()`/`Query()` 显式声明

### 6. FastAPI 怎么处理文件上传？

```python
from fastapi import UploadFile, File

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()  # 异步读取
    # file.filename, file.content_type, file.size
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(content)
```

`UploadFile` 是 SpooledTemporaryFile 的包装：
- 小文件存在内存中
- 大文件自动写入磁盘临时目录
- 支持异步读取（`read()`、`write()`、`seek()`）

vs `bytes`：`bytes` 直接读入内存，大文件会 OOM。

### 7. FastAPI 的异常处理机制是怎样的？

```python
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)

@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "msg": exc.msg, "data": None}
    )

# 或者用 middleware 拦截所有异常
```

异常处理链：
1. 路径函数抛异常
2. 按注册顺序匹配 exception_handler
3. 未匹配的异常被 Starlette 默认处理（500）

### 8. FastAPI 的 `Response Model` 有什么作用？

```python
@app.get("/users/{id}", response_model=UserOut)
async def get_user(id: int):
    user = await User.get(id=id)
    return user  # 自动过滤掉 password 等字段
```

作用：
1. **数据过滤：** 只返回 `UserOut` 中定义的字段
2. **文档生成：** OpenAPI schema 用 response_model
3. **数据校验：** 返回值不符合 schema 会报错

注意：`response_model=None` 可以禁用响应校验（性能考虑）。

### 9. FastAPI 的 `APIRouter` 是怎么组织路由的？

```python
router = APIRouter(prefix="/api/v1", tags=["users"])

@router.get("/users")
async def list_users():
    pass

# 在 app 中注册
app.include_router(router, dependencies=[DependPermission])
```

`APIRouter` 的作用：
1. 路径前缀分组
2. 统一标签（OpenAPI 文档分组）
3. 统一依赖（整个路由组共用鉴权/权限）
4. 嵌套路由（router 包含 router）

### 10. FastAPI 和 Flask、Django 的核心区别是什么？

| | FastAPI | Flask | Django |
|---|---|---|---|
| 异步支持 | 原生 async/await | 2.0+ 部分支持 | 3.0+ 部分支持 |
| 类型系统 | Pydantic（运行时校验） | 无内置 | Forms |
| 自动文档 | OpenAPI/Swagger | 需插件 | 需 DRF |
| 性能 | 接近 Node.js/Go | 中等 | 中等 |
| 依赖注入 | 原生支持 | 需插件 | 无 |
| WebSocket | 原生支持 | 需插件 | Channels |

FastAPI 的核心优势：类型安全 + 自动文档 + 原生异步 + 依赖注入。

### 11. FastAPI 的 `Depends` 和 `Security` 有什么区别？

```python
# Depends：通用依赖注入
async def common_dep():
    pass

# Security：声明安全方案（OAuth2、API Key 等）
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/users/me")
async def me(token: str = Security(oauth2_scheme)):
    pass
```

区别：
- `Depends` 是通用的依赖注入
- `Security` 是 `Depends` 的子类，额外标记安全方案
- `Security` 会在 OpenAPI 文档中显示安全要求

### 12. FastAPI 的 `WebSocket` 怎么用？

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass
```

WebSocket 的生命周期：
1. `accept()` 建立连接
2. `receive_text()`/`send_text()` 双向通信
3. `WebSocketDisconnect` 异常表示断开

### 13. FastAPI 怎么实现请求限流（Rate Limiting）？

FastAPI 没有内置限流，常见方案：

```python
# 方案1：中间件 + Redis
from fastapi import Request
import redis

r = redis.Redis()

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_ip = request.client.host
    key = f"rate:{client_ip}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, 60)  # 60 秒窗口
    if count > 100:
        return JSONResponse(status_code=429, content={"msg": "too many requests"})
    return await call_next(request)

# 方案2：slowapi 库
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
@app.get("/", dependencies=[Depends(limiter.limit("10/minute"))])
```

### 14. FastAPI 的 `TestClient` 是怎么工作的？

```python
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get("/api/v1/users")
assert response.status_code == 200
```

`TestClient` 基于 `httpx`：
- 启动一个 ASGI 服务器（内存中，不绑定端口）
- 同步发送请求，内部用 `anyio` 桥接异步
- 直接调用 ASGI app，不需要网络

### 15. FastAPI 的启动流程是怎样的？

1. 创建 `FastAPI()` 实例
2. 注册路由（`@app.get` 等）
3. 注册中间件（`app.add_middleware`）
4. 注册异常处理器（`app.exception_handler`）
5. `uvicorn.run(app)` 启动 ASGI 服务器
6. 触发 `lifespan` 的 startup 事件
7. 开始监听端口，接受请求

### 16. FastAPI 的 `Header()` 声明有什么特殊行为？

```python
@app.get("/")
async def read_items(user_agent: str = Header(), x_token: str = Header()):
    pass
```

特殊行为：
- HTTP header 用 `-` 分隔（`User-Agent`），Python 变量名不能有 `-`
- FastAPI 自动将 `_` 转为 `-`（`user_agent` → `User-Agent`）
- `Header()` 默认将同名 header 的多个值合并为列表

### 17. FastAPI 怎么实现 CORS？每个参数是什么意思？

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许的源
    allow_credentials=True,                    # 允许携带 cookie
    allow_methods=["*"],                       # 允许的 HTTP 方法
    allow_headers=["*"],                       # 允许的请求头
    expose_headers=["X-Custom-Header"],        # 前端可读的响应头
    max_age=600,                               # preflight 缓存时间（秒）
)
```

CORS 流程：
1. 浏览器发 OPTIONS preflight 请求
2. 服务端返回 `Access-Control-Allow-Origin` 等头
3. 浏览器检查是否允许，允许则发实际请求

### 18. FastAPI 的 `status_code` 怎么用？为什么要用 `status` 模块？

```python
from fastapi import status

@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    pass
```

用 `status` 模块而不是直接写数字的原因：
- 可读性：`status.HTTP_201_CREATED` 比 `201` 清晰
- IDE 补全和文档
- 不容易写错数字

### 19. FastAPI 的 `Body()` 中 `embed` 参数是什么意思？

```python
# 默认：直接展开
@app.post("/items")
async def create(item: Item):
    pass
# 请求体：{"name": "foo", "price": 10}

# embed=True：嵌套在字段名下
@app.post("/items")
async def create(item: Item = Body(embed=True)):
    pass
# 请求体：{"item": {"name": "foo", "price": 10}}
```

多个 Body 参数时必须用 embed，否则 JSON 无法对应多个键。

### 20. FastAPI 和 Starlette 的关系是什么？

FastAPI 是 Starlette 的上层封装：

```
FastAPI（高层）
  ├── 路径参数、查询参数的类型解析
  ├── Pydantic 请求/响应校验
  ├── 依赖注入系统
  ├── 自动 OpenAPI 文档
  └── Starlette（底层）
       ├── ASGI 路由
       ├── Request/Response 对象
       ├── WebSocket 支持
       ├── 中间件
       └── BackgroundTasks
```

FastAPI 可以直接使用 Starlette 的所有功能，因为它是 Starlette 的子类。

---

## 三、Vue 3（15 题）

### 1. Vue 3 的 Composition API 和 Options API 有什么区别？

```javascript
// Options API（Vue 2 风格）
export default {
  data() { return { count: 0 } },
  methods: { increment() { this.count++ } },
  computed: { double() { return this.count * 2 } },
  mounted() { console.log('mounted') }
}

// Composition API（Vue 3）
import { ref, computed, onMounted } from 'vue'
export default {
  setup() {
    const count = ref(0)
    const double = computed(() => count.value * 2)
    const increment = () => count.value++
    onMounted(() => console.log('mounted'))
    return { count, double, increment }
  }
}
```

核心区别：
- Options API 按选项类型组织代码（data/methods/computed 分散）
- Composition API 按逻辑关注点组织代码（相关逻辑在一起）
- Composition API 更好的类型推导、逻辑复用、Tree-shaking

### 2. `ref` 和 `reactive` 的区别？什么时候用哪个？

```javascript
import { ref, reactive } from 'vue'

const count = ref(0)           // 包装基本类型
count.value++                  // 需要 .value 访问

const state = reactive({ count: 0 })  // 包装对象
state.count++                  // 直接访问属性
```

| | ref | reactive |
|---|---|---|
| 适用类型 | 任意类型 | 只能是对象 |
| 访问方式 | `.value` | 直接访问 |
| 解构 | 不丢失响应性 | 解构丢失响应性 |
| 模板中 | 自动解包 | 直接使用 |

选择原则：
- 基本类型（string/number/boolean）必须用 `ref`
- 对象/数组可以用 `reactive`
- 需要替换整个对象时用 `ref`（`state = newObj` 不会触发 reactive 更新）

### 3. Vue 3 的 `computed` 和 `watch` 有什么区别？

```javascript
// computed：派生状态，有缓存
const double = computed(() => count.value * 2)

// watch：副作用，响应变化执行
watch(count, (newVal, oldVal) => {
  console.log(`count changed from ${oldVal} to ${newVal}`)
})

// watchEffect：自动追踪依赖
watchEffect(() => {
  console.log(count.value)  // 自动追踪 count
})
```

| | computed | watch | watchEffect |
|---|---|---|---|
| 目的 | 派生状态 | 副作用 | 副作用 |
| 缓存 | 有 | 无 | 无 |
| 返回值 | 有 | 无 | 无 |
| 惰性 | 否 | 是（默认） | 否 |

### 4. Vue 3 的响应式原理是什么？和 Vue 2 有什么区别？

Vue 3 用 `Proxy` 实现响应式：

```javascript
// 简化版
function reactive(target) {
  return new Proxy(target, {
    get(target, key, receiver) {
      track(target, key)  // 收集依赖
      return Reflect.get(target, key, receiver)
    },
    set(target, key, value, receiver) {
      const result = Reflect.set(target, key, value, receiver)
      trigger(target, key)  // 触发更新
      return result
    }
  })
}
```

vs Vue 2 的 `Object.defineProperty`：
- Proxy 可以拦截新增/删除属性，`defineProperty` 不行
- Proxy 可以拦截数组索引修改，`defineProperty` 需要 hack
- Proxy 性能更好（惰性监听，不递归初始化）

### 5. Vue 3 的 `setup()` 函数是什么？`<script setup>` 又是什么？

```javascript
// setup() 函数
export default {
  setup(props, context) {
    // props 是响应式的
    // context 包含 attrs, slots, emit
    return { /* 暴露给模板 */ }
  }
}

// <script setup> 语法糖（推荐）
<script setup>
import { ref } from 'vue'
const count = ref(0)  // 自动暴露给模板
defineProps(['title'])
defineEmits(['update'])
</script>
```

`<script setup>` 的优势：
- 更少的样板代码
- 更好的类型推导
- 编译时优化（更好的 Tree-shaking）

### 6. Vue 3 的生命周期钩子有哪些？和 Vue 2 怎么对应？

```javascript
import { onBeforeMount, onMounted, onBeforeUpdate, onUpdated, 
         onBeforeUnmount, onUnmounted } from 'vue'

// Composition API 中
onMounted(() => { /* DOM 已挂载 */ })
onUnmounted(() => { /* 清理副作用 */ })
```

对应关系：
| Options API | Composition API |
|---|---|
| beforeCreate | setup() |
| created | setup() |
| beforeMount | onBeforeMount |
| mounted | onMounted |
| beforeUpdate | onBeforeUpdate |
| updated | onUpdated |
| beforeDestroy | onBeforeUnmount |
| destroyed | onUnmounted |

### 7. Vue 3 的 `provide`/`inject` 是什么？和 props 有什么区别？

```javascript
// 祖先组件
import { provide } from 'vue'
provide('theme', 'dark')

// 后代组件
import { inject } from 'vue'
const theme = inject('theme', 'light')  // 默认值 'light'
```

vs props：
- props 是父子组件间显式传递
- provide/inject 是跨层级隐式传递
- props 有类型校验，provide/inject 没有
- provide/inject 类似 React 的 Context

### 8. Vue 3 的 `toRef` 和 `toRefs` 是什么？解决什么问题？

```javascript
import { reactive, toRef, toRefs } from 'vue'

const state = reactive({ count: 0, name: 'foo' })

// 解构会丢失响应性
const { count, name } = state  // 不是响应式的

// toRef/toRefs 保持响应性
const countRef = toRef(state, 'count')  // 单个属性
const { count, name } = toRefs(state)   // 所有属性
```

原理：`toRef` 创建一个 ref，其 `.value` 指向原始对象的属性。修改 ref 会同步修改原始对象。

### 9. Vue 3 的 `Teleport` 是什么？什么场景下需要它？

```html
<teleport to="body">
  <div class="modal">...</div>
</teleport>
```

Teleport 将组件的 DOM 渲染到指定目标位置，而不是父组件 DOM 树中。

场景：
- 模态框（Modal）：需要渲染到 body 下，避免父组件的 overflow/transform 影响
- Toast/Notification：需要脱离当前组件层级
- Tooltip：需要定位到正确的位置

### 10. Vue 3 的 `Suspense` 是什么？

```html
<suspense>
  <template #default>
    <AsyncComponent />
  </template>
  <template #fallback>
    <Loading />
  </template>
</suspense>
```

`Suspense` 处理异步组件的加载状态：
- 当异步组件的 `setup()` 中有未完成的 `await` 时，显示 `#fallback`
- 所有异步操作完成后，显示 `#default`

目前仍是实验性功能（Vue 3.5+）。

### 11. Vue Router 的 `hash` 模式和 `history` 模式有什么区别？

| | Hash 模式 | History 模式 |
|---|---|---|
| URL 格式 | `/#/path` | `/path` |
| 服务端配置 | 不需要 | 需要配置 fallback |
| SEO | 差 | 好 |
| 刷新行为 | 正常 | 可能 404 |

History 模式需要服务端配置：所有路由都返回 index.html，让前端处理。

项目中的 `buildRoutes` 同时支持两种模式，通过 `createWebHashHistory` / `createWebHistory` 切换。

### 12. Pinia 和 Vuex 有什么区别？为什么项目选 Pinia？

```javascript
// Pinia
const useCounter = defineStore('counter', () => {
  const count = ref(0)
  const double = computed(() => count.value * 2)
  const increment = () => count.value++
  return { count, double, increment }
})

// Vuex
const store = new Vuex.Store({
  state: { count: 0 },
  getters: { double: state => state.count * 2 },
  mutations: { increment: state => state.count++ },
  actions: { incrementAsync({ commit }) { commit('increment') } }
})
```

Pinia 优势：
1. 去掉了 mutations（直接修改 state）
2. 完整的 TypeScript 支持
3. 模块化设计（每个 store 独立）
4. 更小的包体积
5. Vue 官方推荐的状态管理方案

### 13. Vue 3 的 `v-model` 和 Vue 2 有什么不同？

```html
<!-- Vue 2 -->
<child :value="msg" @input="msg = $event" />
<child v-model="msg" />

<!-- Vue 3 -->
<child :modelValue="msg" @update:modelValue="msg = $event" />
<child v-model="msg" />

<!-- Vue 3 多个 v-model -->
<child v-model:title="title" v-model:content="content" />
```

Vue 3 的变化：
- prop 名从 `value` 改为 `modelValue`
- 事件名从 `input` 改为 `update:modelValue`
- 支持多个 `v-model`
- 支持自定义修饰符

### 14. Vue 3 的 `Fragment` 是什么？

Vue 3 组件可以有多个根节点：

```html
<!-- Vue 2 必须单根节点 -->
<template>
  <div>
    <header>...</header>
    <main>...</main>
  </div>
</template>

<!-- Vue 3 支持多根节点 -->
<template>
  <header>...</header>
  <main>...</main>
</template>
```

Fragment 不会渲染为 DOM 节点，减少不必要的 DOM 层级。

### 15. Vue 3 的编译器优化有哪些？

1. **静态提升（Hoist Static）：** 静态节点只创建一次，后续渲染复用
2. **Patch Flag：** 标记动态绑定的类型（文本/属性/类等），diff 时跳过静态部分
3. **Block Tree：** 将模板分为"块"，每个块维护动态节点列表，diff 时只比较动态节点
4. **缓存事件处理：** 内联事件处理器自动缓存，避免不必要的子组件更新

这些优化使得 Vue 3 的渲染性能接近手写 Virtual DOM。

---

## 四、PostgreSQL（15 题）

### 1. PostgreSQL 的 MVCC 是什么？和 MySQL 的锁机制有什么区别？

MVCC（多版本并发控制）：每行数据有多个版本，读操作读取快照版本，不阻塞写操作。

```
事务开始时获取快照 → 读操作读快照版本 → 写操作创建新版本 → 提交时标记旧版本可清理
```

vs MySQL InnoDB：
- InnoDB 也用 MVCC，但实现不同（undo log vs PostgreSQL 的多版本存储）
- PostgreSQL 的 MVCC 更彻底，读写完全不阻塞
- PostgreSQL 的 `VACUUM` 清理旧版本，InnoDB 的 purge 线程清理

### 2. PostgreSQL 的索引类型有哪些？什么时候用哪种？

| 索引类型 | 适用场景 | 原理 |
|---|---|---|
| B-tree | 等值查询、范围查询 | 平衡树，默认索引 |
| Hash | 等值查询 | 哈希表，不支持范围 |
| GiST | 几何数据、全文搜索 | 通用搜索树 |
| GIN | 数组、JSONB、全文搜索 | 倒排索引 |
| BRIN | 大表、物理有序数据 | 块范围索引，极小体积 |

项目中的选择：
- 用户表的 username → B-tree（等值查询）
- 审计日志的时间戳 → B-tree（范围查询）
- JSONB 字段（request_args）→ GIN（JSON 查询）

### 3. PostgreSQL 的 `EXPLAIN ANALYZE` 怎么看？

```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE username = 'admin';
```

关键指标：
- `Seq Scan` vs `Index Scan`：全表扫描 vs 索引扫描
- `cost`：估计成本（启动成本..总成本）
- `rows`：估计行数 vs 实际行数
- `actual time`：实际执行时间
- `Buffers`：共享缓冲区命中/读取

性能问题标志：
- `Seq Scan` 在大表上 → 缺少索引
- 估计行数和实际行数差距大 → 统计信息过时，需要 `ANALYZE`
- `Sort` 节点内存溢出 → 增加 `work_mem`

### 4. PostgreSQL 的事务隔离级别有哪些？

| 级别 | 脏读 | 不可重复读 | 幻读 |
|---|---|---|---|
| Read Uncommitted | 可能 | 可能 | 可能 |
| Read Committed | 不会 | 可能 | 可能 |
| Repeatable Read | 不会 | 不会 | 不会* |
| Serializable | 不会 | 不会 | 不会 |

PostgreSQL 的特殊之处：
- `Read Uncommitted` 实际上等同于 `Read Committed`（MVCC 保证）
- `Repeatable Read` 用快照隔离，实际不会出现幻读
- `Serializable` 用 SSI（Serializable Snapshot Isolation），性能比传统锁好

默认级别：Read Committed。

### 5. PostgreSQL 的 `VACUUM` 是什么？为什么需要它？

MVCC 的副作用：旧版本数据不会立即删除，需要 VACUUM 清理。

```sql
VACUUM users;           -- 清理死元组，不锁表
VACUUM FULL users;      -- 重写表，锁表，回收空间到 OS
ANALYZE users;          -- 更新统计信息
```

VACUUM 的作用：
1. 标记死元组的空间为可重用
2. 更新 visibility map（用于 Index-Only Scan）
3. 防止事务 ID 回卷（Transaction ID Wraparound）

Autovacuum：PostgreSQL 自动执行 VACUUM，配置参数控制频率。

### 6. PostgreSQL 的 `JSONB` 和 `JSON` 有什么区别？

| | JSON | JSONB |
|---|---|---|
| 存储格式 | 文本 | 二进制 |
| 写入速度 | 快 | 慢（需解析） |
| 读取速度 | 慢（需解析） | 快 |
| 索引支持 | 无 | GIN 索引 |
| 操作符 | 无 | 支持 |

项目中 `AuditLog.request_args` 用 JSON 存储（写入频率高，读取频率低）。

如果需要查询 JSON 内部字段，应该用 JSONB + GIN 索引。

### 7. PostgreSQL 的窗口函数是什么？举例说明。

```sql
-- 按部门排名薪资
SELECT name, dept_id, salary,
  RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) as rank
FROM employees;

-- 累计求和
SELECT date, amount,
  SUM(amount) OVER (ORDER BY date) as cumulative
FROM transactions;
```

窗口函数 vs GROUP BY：
- GROUP BY 将多行聚合为一行
- 窗口函数保留所有行，额外计算聚合值

常用窗口函数：`ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()`, `SUM() OVER`

### 8. PostgreSQL 的 CTE（Common Table Expression）是什么？递归 CTE 怎么写？

```sql
-- 普通 CTE
WITH active_users AS (
  SELECT * FROM users WHERE is_active = true
)
SELECT * FROM active_users WHERE is_superuser = true;

-- 递归 CTE（遍历树）
WITH RECURSIVE dept_tree AS (
  -- 基础查询
  SELECT id, name, parent_id, 0 as level FROM depts WHERE id = 1
  UNION ALL
  -- 递归查询
  SELECT d.id, d.name, d.parent_id, dt.level + 1
  FROM depts d JOIN dept_tree dt ON d.parent_id = dt.id
)
SELECT * FROM dept_tree;
```

项目用 closure table 替代递归 CTE，因为 closure table 查询性能 O(1) vs 递归 CTE O(depth)。

### 9. PostgreSQL 的连接池怎么配置？和应用层连接池有什么区别？

数据库层连接池（如 PgBouncer）：
- 在应用和数据库之间代理连接
- 减少数据库的连接数（多对多映射）
- 支持 transaction/session pooling 模式

应用层连接池（如 asyncpg 的 pool）：
- 在应用进程内管理连接
- 每个进程独立的连接池
- 配置 `min_size`、`max_size`、`timeout`

最佳实践：两者结合。应用层用小连接池，PgBouncer 做大池。

### 10. PostgreSQL 的 `EXPLAIN (BUFFERS, ANALYZE)` 中 shared hit 和 read 是什么？

```
Buffers: shared hit=128 read=32
```

- `shared hit`：数据在 PostgreSQL 的共享缓冲区中（内存），不需要磁盘 I/O
- `shared read`：数据不在缓冲区，需要从磁盘读取

优化目标：提高 hit 比例（增大 `shared_buffers` 配置）。

### 11. PostgreSQL 的并发控制怎么处理死锁？

PostgreSQL 自动检测死锁：
1. 事务 A 持有行 X 的锁，等待行 Y 的锁
2. 事务 B 持有行 Y 的锁，等待行 X 的锁
3. 死锁检测器发现循环等待
4. 选择一个事务作为"牺牲者"，回滚它
5. 另一个事务继续执行

避免死锁：
- 按固定顺序访问资源
- 减少事务持锁时间
- 使用 `SELECT ... FOR UPDATE SKIP LOCKED` 跳过已锁行

### 12. PostgreSQL 的 `SERIALIZABLE` 隔离级别是怎么实现的？

PostgreSQL 用 SSI（Serializable Snapshot Isolation）：
1. 事务获取快照，读操作不加锁
2. 跟踪事务间的读写依赖关系
3. 检测"危险结构"（rw-antidependency cycles）
4. 如果检测到潜在的序列化异常，回滚事务

比传统的两阶段锁（2PL）性能好很多，因为读操作完全不阻塞。

### 13. PostgreSQL 的分区表怎么用？

```sql
-- 声明式分区
CREATE TABLE audit_logs (
  id bigserial, created_at timestamp, ...
) PARTITION BY RANGE (created_at);

CREATE TABLE audit_logs_2024 PARTITION OF audit_logs
  FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

分区的好处：
- 查询时自动裁剪不相关分区（partition pruning）
- 大表维护（VACUUM、备份）可以按分区做
- 删除旧数据直接 `DROP PARTITION`

### 14. PostgreSQL 的全文搜索怎么用？和 Elasticsearch 比有什么区别？

```sql
-- 创建全文搜索索引
ALTER TABLE articles ADD COLUMN tsv tsvector;
UPDATE articles SET tsv = to_tsvector('chinese', title || content);
CREATE INDEX idx_tsv ON articles USING GIN(tsv);

-- 搜索
SELECT * FROM articles WHERE tsv @@ to_tsquery('chinese', '求职 & 简历');
```

vs Elasticsearch：
| | PostgreSQL FTS | Elasticsearch |
|---|---|---|
| 功能 | 基本全文搜索 | 完整搜索引擎 |
| 性能 | 中小规模够用 | 大规模优化 |
| 分词 | 内置或插件 | 内置多种分词器 |
| 部署 | 复杂度低 | 需要额外集群 |
| 聚合 | 有限 | 强大 |

项目选择 ChromaDB（向量搜索）而不是 PostgreSQL FTS，因为需要语义搜索。

### 15. PostgreSQL 的 `pg_stat_statements` 是什么？

扩展模块，记录所有 SQL 的执行统计：

```sql
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

可以看到：
- 最慢的 SQL
- 执行次数最多的 SQL
- 总耗时最高的 SQL

用于性能优化：找到慢查询 → 分析执行计划 → 添加索引或优化查询。

---

## 五、Redis（10 题）

### 1. Redis 的数据结构有哪些？各适合什么场景？

| 数据结构 | 适用场景 | 示例 |
|---|---|---|
| String | 缓存、计数器、分布式锁 | `SET key value` |
| Hash | 对象存储 | `HSET user:1 name "foo"` |
| List | 消息队列、最新列表 | `LPUSH/BRPOP` |
| Set | 去重、交集/并集 | 标签、共同好友 |
| Sorted Set | 排行榜、延迟队列 | `ZADD score member` |
| Bitmap | 签到、在线状态 | `SETBIT login:2024 123 1` |
| HyperLogLog | 基数统计（UV） | `PFADD page:uv user1` |
| Stream | 消息队列（持久化） | `XADD/XREAD` |

### 2. Redis 的持久化机制有哪些？RDB 和 AOF 的区别？

| | RDB | AOF |
|---|---|---|
| 方式 | 定时快照 | 追加写命令 |
| 文件大小 | 小（二进制压缩） | 大（命令文本） |
| 恢复速度 | 快 | 慢 |
| 数据安全 | 可能丢失最后一次快照后的数据 | 最多丢失 1 秒 |
| 性能影响 | fork 子进程时有短暂阻塞 | appendfsync 配置影响 |

生产建议：RDB + AOF 混合持久化（Redis 4.0+）。

### 3. Redis 的缓存穿透、缓存击穿、缓存雪崩是什么？怎么解决？

**缓存穿透：** 查询不存在的数据，缓存永远 miss，请求打到数据库。
- 布隆过滤器：不存在的数据直接拦截
- 缓存空值：不存在的数据也缓存（短 TTL）

**缓存击穿：** 热点 key 过期，大量并发请求打到数据库。
- 互斥锁：只让一个请求查数据库，其他等待
- 永不过期：热点 key 不设过期时间，后台异步更新

**缓存雪崩：** 大量 key 同时过期，或 Redis 宕机。
- 随机 TTL：过期时间加随机值，避免同时失效
- 多级缓存：本地缓存 + Redis + 数据库
- 熔断降级：Redis 不可用时直接读数据库

### 4. Redis 的分布式锁怎么实现？

```python
import redis

def acquire_lock(r, lock_name, timeout=10):
    return r.set(f"lock:{lock_name}", "1", nx=True, ex=timeout)

def release_lock(r, lock_name):
    r.delete(f"lock:{lock_name}")
```

问题和改进：
- `nx=True` 保证原子性设置
- `ex=timeout` 防止死锁（持有者崩溃不释放）
- 释放锁时需要检查是否是自己加的锁（用 Lua 脚本保证原子性）
- Redlock 算法：多个 Redis 实例，多数派获取成功才算成功

### 5. Redis 的过期策略有哪些？

1. **惰性删除：** 访问 key 时检查是否过期，过期则删除
2. **定期删除：** 每 100ms 随机检查 20 个 key，删除过期的
3. **内存淘汰策略（maxmemory）：**
   - `noeviction`：不淘汰，写入报错
   - `allkeys-lru`：所有 key 中最近最少使用的
   - `volatile-lru`：有过期时间的 key 中 LRU
   - `allkeys-random`：随机淘汰
   - `volatile-ttl`：TTL 最小的

生产建议：`allkeys-lru` 或 `volatile-lru`。

### 6. Redis 的集群方案有哪些？

| 方案 | 优点 | 缺点 |
|---|---|---|
| 主从复制 | 简单、读写分离 | 手动故障转移 |
| Sentinel | 自动故障转移 | 不支持分片 |
| Cluster | 自动分片+故障转移 | 客户端需要支持、不支持跨 slot 事务 |

Redis Cluster：
- 16384 个 slot，key 通过 CRC16(key) % 16384 分配到节点
- 每个节点负责一部分 slot
- 节点间通过 Gossip 协议通信

### 7. Redis 的 Pipeline 是什么？为什么能提高性能？

```python
pipe = redis.pipeline()
pipe.set("a", "1")
pipe.set("b", "2")
pipe.get("a")
pipe.get("b")
results = pipe.execute()  # 一次性发送所有命令
```

原理：
- 普通模式：每个命令一次 RTT（Round-Trip Time）
- Pipeline：多个命令打包成一个请求，一次 RTT
- 减少网络延迟，但不保证原子性（和事务不同）

### 8. Redis 的事务（MULTI/EXEC）和 Lua 脚本有什么区别？

```python
# 事务
pipe = redis.pipeline(transaction=True)  # MULTI/EXEC
pipe.set("a", "1")
pipe.incr("a")
pipe.execute()  # 原子执行

# Lua 脚本
lua_script = """
local val = redis.call('GET', KEYS[1])
if val == ARGV[1] then
    redis.call('DEL', KEYS[1])
    return 1
end
return 0
"""
r.eval(lua_script, 1, "lock:my_lock", "my_value")
```

区别：
- 事务：命令队列化后一起执行，但不支持条件逻辑
- Lua 脚本：支持复杂逻辑，原子执行，可以读取结果并决定后续操作
- Lua 脚本更强大，但编写和调试更复杂

### 9. Redis 的 Pub/Sub 是什么？和 Stream 有什么区别？

```python
# Pub/Sub
r.publish("channel", "message")  # 发布
pubsub = r.pubsub()
pubsub.subscribe("channel")
for message in pubsub.listen():  # 订阅
    process(message)

# Stream
r.xadd("stream", {"field": "value"})  # 生产
r.xread({"stream": last_id}, count=10, block=5000)  # 消费
```

| | Pub/Sub | Stream |
|---|---|---|
| 持久化 | 不持久化 | 持久化 |
| 消息确认 | 无 | 有（XACK） |
| 消费组 | 不支持 | 支持 |
| 回放 | 不支持 | 支持 |

Stream 是 Redis 5.0+ 的消息队列，适合需要持久化和消费确认的场景。

### 10. Redis 和 Memcached 的区别？

| | Redis | Memcached |
|---|---|---|
| 数据结构 | 丰富（String/Hash/List/Set/ZSet） | 只有 String |
| 持久化 | RDB + AOF | 无 |
| 集群 | 原生 Cluster | 客户端分片 |
| 线程模型 | 单线程（6.0+ 多线程 I/O） | 多线程 |
| 最大值 | 512MB | 1MB |

Redis 几乎在所有场景都优于 Memcached，除非只需要最简单的缓存且对内存效率要求极高。

---

## 六、LangGraph / RAG / 大模型（20 题）

### 1. RAG（检索增强生成）是什么？为什么需要它？

RAG = Retrieval-Augmented Generation，在生成回答前先检索相关文档。

为什么需要：
1. **知识截止：** LLM 训练数据有截止日期，无法回答最新信息
2. **幻觉：** LLM 可能编造事实，RAG 提供真实文档作为依据
3. **领域知识：** 通用 LLM 缺乏企业私有数据
4. **可溯源：** 答案可以引用具体文档来源

RAG 流程：
```
用户查询 → 检索相关文档 → 将文档拼入 prompt → LLM 基于文档生成回答
```

### 2. 向量检索的原理是什么？Embedding 是怎么工作的？

Embedding 将文本映射到高维向量空间，语义相似的文本向量距离近。

```
"求职" → [0.2, -0.1, 0.8, ...]  (1024维)
"找工作" → [0.21, -0.12, 0.79, ...]  (很接近)
"天气" → [0.5, 0.3, -0.2, ...]  (很远)
```

检索流程：
1. 离线：文档切块 → embedding → 存入向量数据库
2. 在线：查询 embedding → 在向量数据库中找最近邻 → 返回相关文档块

距离度量：
- cosine 距离：衡量方向相似性，不受模长影响
- 欧氏距离：衡量绝对距离
- 内积：归一化后等价于 cosine

### 3. 文档切块（Chunking）有哪些策略？各有什么优劣？

| 策略 | 优点 | 缺点 |
|---|---|---|
| 固定长度 | 简单可控 | 切断语义 |
| 按句子 | 语义完整 | 块大小不均匀 |
| 按段落 | 语义完整 | 段落可能很长 |
| 递归分割 | 先大后小，灵活 | 实现复杂 |
| 语义分割 | 语义边界最好 | 计算成本高 |

项目用的策略：先按段落 → 按中文句号 → 按逗号 → 固定长度（fallback）。

chunk 大小选择：通常 200-1000 tokens，太大检索不精确，太小缺少上下文。

### 4. 什么是 Rerank？为什么需要它？

Rerank 是对初步检索结果的重新排序。

为什么需要：
1. 向量检索的相似度分数不一定反映真实相关性
2. 初步检索通常返回 top_k=20，但用户只需要 top_5
3. 不同查询的"相关"标准不同

Rerank 方法：
1. **Cross-encoder：** 将 query 和 document 一起输入模型，输出相关性分数。精度高但慢
2. **LLM-based：** 用 LLM 判断相关性。灵活但贵
3. **ColBERT：** late interaction，折中方案

### 5. LangGraph 的核心概念是什么？和 LangChain 有什么区别？

LangGraph 核心概念：
1. **State：** 图的状态，包含所有中间结果
2. **Node：** 处理单元，执行具体逻辑
3. **Edge：** 节点间的连接，可以是条件边
4. **Graph：** 由节点和边组成的有向图

vs LangChain：
- LangChain 是线性 chain，适合简单流程
- LangGraph 是状态机图，支持循环、条件分支、多步推理
- LangGraph 更适合复杂的 Agent 场景

### 6. 什么是 Agent？和普通的 Chain 有什么区别？

Agent = LLM + 工具调用 + 决策循环。

```
Chain: 输入 → Prompt → LLM → 输出（固定流程）
Agent: 输入 → LLM → 决定调用哪个工具 → 执行工具 → LLM → 继续或结束（动态流程）
```

Agent 的关键能力：
1. **推理：** 分析问题，决定下一步
2. **工具调用：** 使用外部工具（搜索、计算、API）
3. **循环控制：** 多步推理，直到问题解决

### 7. 什么是 Function Calling / Tool Calling？

LLM 的工具调用机制：

```json
// LLM 输出
{
  "tool_calls": [{
    "function": {
      "name": "search_jobs",
      "arguments": "{\"query\": \"Python 后端\", \"city\": \"上海\"}"
    }
  }]
}
```

流程：
1. 定义工具的 schema（名称、参数、描述）
2. 用户查询 + 工具定义 发给 LLM
3. LLM 决定是否调用工具、调用哪个、传什么参数
4. 执行工具，将结果发回 LLM
5. LLM 基于工具结果生成最终回答

### 8. 什么是 Embedding 模型的维度？维度越高越好吗？

维度（dimension）是向量空间的大小。`text-embedding-v3` 输出 1024 维向量。

维度的影响：
| 低维度（384） | 高维度（1536） |
|---|---|
| 存储小 | 存储大 |
| 检索快 | 检索慢 |
| 语义表达弱 | 语义表达强 |
| 适合简单任务 | 适合复杂语义 |

不是越高越好：维度太高会"过度表达"，增加计算成本但不一定提升效果。1024 维是平衡点。

### 9. 什么是混合检索（Hybrid Search）？RRF 融合公式是什么？

混合检索 = 向量检索 + 关键词检索。

向量检索：语义相似（"找工作" 匹配 "求职"）
关键词检索：精确匹配（"Python" 只匹配 "Python"）

RRF（Reciprocal Rank Fusion）公式：
```
score(d) = Σ 1 / (k + rank_i(d))
```

- d：文档
- k：平滑参数（通常 60）
- rank_i(d)：文档 d 在第 i 个检索列表中的排名

RRF 的优势：不需要归一化分数，直接融合排名。

### 10. 什么是 Query Rewrite？为什么 RAG 需要它？

Query Rewrite 将用户原始查询改写为更适合检索的形式。

原始查询："怎么找工作"
改写结果：
1. "求职技巧和方法"
2. "2024年就业市场分析"
3. "应届毕业生求职指南"

为什么需要：
1. 用户查询通常简短、口语化
2. 文档表述通常正式、专业化
3. 多角度改写提高召回率

### 11. 什么是 Context Compression？什么时候需要它？

Context Compression 将检索到的长文档压缩为与查询相关的片段。

当检索结果超过 LLM 的 context window 时需要：
- 检索返回 10 个文档，每个 500 tokens，共 5000 tokens
- LLM 的 context window 可能只有 4096 tokens
- 需要压缩或截断

压缩方法：
1. LLM 提取关键信息（质量高但慢）
2. 基于查询的相关性截断（快但粗糙）
3. 用小模型做 extractive summarization

### 12. LLM 的 Temperature 参数是什么？不同值有什么效果？

Temperature 控制输出的随机性：
- `temperature = 0`：几乎确定性输出，每次结果一样
- `temperature = 0.7`：适度随机，平衡创造性和一致性
- `temperature = 1.0`：高度随机，创造性强但可能不连贯

数学原理：softmax(logits / temperature)，temperature 越小，概率分布越尖锐。

场景选择：
- 事实性问答：temperature = 0（需要确定性）
- 创意写作：temperature = 0.7-1.0（需要创造性）
- 代码生成：temperature = 0（需要准确性）

### 13. LLM 的 Token 是什么？中文和英文的 token 数一样吗？

Token 是 LLM 处理文本的最小单位。一个 token 可能是一个词、一个字、或一个子词。

中文 vs 英文：
- 英文："Hello World" → 2 tokens
- 中文："你好世界" → 2-4 tokens（取决于分词器）
- 通常中文消耗的 token 数比英文多 1.5-2 倍

Token 计数很重要：
- API 按 token 计费
- Context window 有 token 限制
- 中文项目要特别注意 token 成本

### 14. 什么是 Prompt Engineering？常见的技巧有哪些？

Prompt Engineering = 设计 LLM 输入提示以获得期望输出。

常见技巧：
1. **角色设定：** "你是一个专业的求职顾问..."
2. **少样本学习（Few-shot）：** 给几个示例
3. **思维链（Chain-of-Thought）：** "让我们一步一步思考"
4. **结构化输出：** "请以 JSON 格式返回"
5. **约束条件：** "只回答与求职相关的问题"
6. **输出格式：** "输出 Markdown 表格"

### 15. 什么是幻觉（Hallucination）？怎么缓解？

幻觉 = LLM 编造不存在的事实。

原因：
1. 训练数据中的错误
2. 概率采样的随机性
3. 模型倾向于"自信地回答"而非"承认不知道"

缓解方法：
1. **RAG：** 提供真实文档作为依据
2. **低 temperature：** 减少随机性
3. **约束 prompt：** "如果不确定，请说'我不知道'"
4. **事实核查：** 后处理验证答案
5. **引用来源：** 要求 LLM 引用文档

### 16. 什么是 Fine-tuning？和 RAG 有什么区别？

Fine-tuning = 在预训练模型基础上用特定数据继续训练。

| | Fine-tuning | RAG |
|---|---|---|
| 原理 | 修改模型权重 | 检索外部知识 |
| 成本 | 高（需要 GPU） | 低（只需向量数据库） |
| 更新 | 需要重新训练 | 实时更新 |
| 适用 | 特定风格/格式 | 知识库问答 |
| 数据量 | 需要大量标注数据 | 少量文档即可 |

选择原则：
- 需要改变模型行为（风格、格式）→ Fine-tuning
- 需要引入新知识 → RAG
- 两者结合效果最好

### 17. 什么是 Context Window？超出限制怎么办？

Context Window 是 LLM 一次能处理的最大 token 数。

超出限制的处理：
1. **截断：** 丢弃超出部分（简单但可能丢失关键信息）
2. **压缩：** 用 LLM 压缩上下文（质量高但慢）
3. **滑动窗口：** 只保留最近的 N 个 token
4. **摘要：** 对历史对话做摘要

项目用 context compression：超过 6000 字符时 LLM 提取关键内容。

### 18. 什么是多轮对话的记忆管理？

LLM 本身是无状态的，每次调用都是独立的。多轮对话需要外部管理记忆。

记忆类型：
1. **短期记忆：** 当前对话的消息历史
2. **长期记忆：** 跨对话的用户偏好
3. **工作记忆：** 当前任务的中间结果

管理策略：
1. **全量历史：** 简单但 token 消耗大
2. **滑动窗口：** 只保留最近 N 轮
3. **摘要：** 对早期对话做摘要
4. **向量检索：** 检索相关历史对话

项目用 MemoryItem 存储历史，每次请求加载最近 5 条。

### 19. 什么是 Agent 的 ReAct 模式？

ReAct = Reasoning + Acting。

```
Thought: 我需要搜索Python后端的招聘信息
Action: search_jobs("Python 后端")
Observation: 找到 10 条结果...
Thought: 用户还提到了薪资要求，我需要过滤
Action: filter_by_salary(results, "> 20k")
Observation: 过滤后剩 5 条...
Thought: 现在我可以给出回答了
Answer: ...
```

vs 纯推理：ReAct 让 LLM 可以"观察"工具执行结果，动态调整策略。

### 20. 什么是 RAG 的评估指标？怎么衡量 RAG 系统的效果？

核心指标：
1. **Recall@K：** 检索的 top-K 中包含正确文档的比例
2. **Precision@K：** 检索的 top-K 中相关文档的比例
3. **MRR（Mean Reciprocal Rank）：** 第一个正确结果的排名的倒数
4. **Answer Correctness：** 最终回答的正确性
5. **Faithfulness：** 回答是否忠实于检索到的文档

评估框架：RAGAS、TruLens、LangSmith。

---

## 七、系统设计（10 题）

### 1. 如何设计一个高可用的后端服务？

关键措施：
1. **多实例部署：** 至少 2 个实例，负载均衡分发
2. **健康检查：** 定期检查实例状态，自动摘除不健康实例
3. **熔断降级：** 依赖服务不可用时快速失败，返回降级结果
4. **限流：** 限制每秒请求数，防止过载
5. **优雅关闭：** 收到 SIGTERM 后等待请求处理完毕再退出
6. **蓝绿部署/金丝雀发布：** 无停机更新

### 2. 如何设计一个消息队列系统？

核心组件：
1. **Producer：** 发送消息到指定 topic
2. **Broker：** 存储和转发消息
3. **Consumer：** 从 topic 消费消息
4. **Offset 管理：** 记录消费进度

关键设计：
- 消息持久化（写磁盘）
- 消费确认（ACK 机制）
- 消费者组（负载均衡）
- 消息顺序性（partition 内有序）
- 死信队列（处理失败的消息）

### 3. 如何设计一个权限系统（RBAC）？

```
User → Role → Permission
         ↓
       Menu（前端路由）
       API（后端接口）
```

核心表：
- user_role：用户-角色关联
- role_permission：角色-权限关联
- permission：权限定义（API method + path）

关键设计：
- 超管绕过权限检查
- 前端按钮级权限（v-permission 指令）
- 后端 API 级权限（Depends 检查）
- 动态路由（从后端获取菜单生成路由）

### 4. 如何设计一个文件上传系统？

分层设计：
1. **接入层：** 文件校验（类型、大小）、分片上传
2. **存储层：** 本地磁盘 / 对象存储（S3/MinIO）
3. **元数据层：** 数据库记录文件信息（路径、大小、上传者）

关键考虑：
- 大文件分片上传 + 断点续传
- 文件类型白名单校验
- 文件名防冲突（UUID 重命名）
- 病毒扫描
- CDN 加速

### 5. 如何设计一个实时聊天系统？

架构：
1. **WebSocket 长连接：** 客户端和服务器双向通信
2. **消息存储：** 消息写入数据库（持久化）
3. **消息推送：** 在线用户通过 WebSocket 推送，离线用户存入离线消息
4. **消息确认：** ACK 机制保证消息送达

关键设计：
- 消息 ID 全局唯一（Snowflake）
- 消息顺序（每会话内单调递增）
- 多端同步（同一用户多个设备）
- 已读/未读状态

### 6. 如何设计一个缓存系统？

多级缓存架构：
```
客户端缓存 → CDN → 应用本地缓存 → Redis → 数据库
```

关键设计：
- 缓存策略：Cache-Aside / Read-Through / Write-Through / Write-Behind
- 缓存一致性：更新数据库时删除缓存（而不是更新缓存）
- 缓存预热：系统启动时加载热点数据
- 缓存降级：Redis 不可用时直接读数据库

### 7. 如何设计一个日志收集系统？

架构：
```
应用 → 日志采集（Filebeat/Fluentd）→ 消息队列（Kafka）→ 存储（Elasticsearch）→ 展示（Kibana）
```

关键设计：
- 结构化日志（JSON 格式）
- 日志分级（DEBUG/INFO/WARN/ERROR）
- 链路追踪（trace_id 贯穿请求链路）
- 日志保留策略（按时间/大小清理）

### 8. 如何设计一个分布式 ID 生成器？

方案对比：
| 方案 | 优点 | 缺点 |
|---|---|---|
| UUID | 简单、全局唯一 | 无序、占空间 |
| 数据库自增 | 简单、有序 | 单点瓶颈 |
| Snowflake | 有序、高性能 | 时钟回拨问题 |
| Leaf/美团 | 双 Buffer、高可用 | 需要额外服务 |

Snowflake 结构：
```
0 | 41位时间戳 | 10位机器ID | 12位序列号
```

### 9. 如何设计一个 API 网关？

核心功能：
1. **路由转发：** 根据路径转发到不同服务
2. **认证鉴权：** JWT 校验、API Key 校验
3. **限流熔断：** 保护后端服务
4. **日志监控：** 记录请求日志、监控指标
5. **协议转换：** HTTP → gRPC、REST → GraphQL
6. **负载均衡：** Round-Robin、加权轮询

### 10. 如何设计一个配置中心？

核心功能：
1. **配置存储：** KV 存储，支持分组/命名空间
2. **动态推送：** 配置变更实时推送到客户端
3. **版本管理：** 配置变更历史，支持回滚
4. **灰度发布：** 配置可以按实例/分组灰度生效
5. **权限控制：** 不同环境（dev/staging/prod）不同权限

项目的做法：数据库 sys_config 表 + 管理 UI，简单但有效。

---

## 八、场景题（10 题）

### 1. 系统上线后发现某个 API 响应很慢，怎么排查？

排查步骤：
1. **看监控：** P50/P95/P99 延迟，是突然变慢还是逐渐变慢
2. **看日志：** 有无错误日志、超时日志
3. **看数据库：** `EXPLAIN ANALYZE` 慢查询，检查索引、锁等待
4. **看外部依赖：** LLM 调用、Redis 连接是否正常
5. **看资源：** CPU、内存、磁盘 I/O、网络带宽
6. **看并发：** 是否有死锁、连接池耗尽

### 2. 数据库 CPU 飙到 100%，怎么处理？

紧急处理：
1. 找到占用 CPU 最多的查询：`pg_stat_activity`
2. 杀掉长时间运行的查询：`pg_terminate_backend(pid)`
3. 如果是慢查询：临时加索引

后续优化：
1. `EXPLAIN ANALYZE` 分析慢查询
2. 添加缺失索引
3. 优化查询（避免 SELECT *、减少 JOIN）
4. 读写分离，读请求走从库
5. 调整 `shared_buffers`、`work_mem` 参数

### 3. Redis 内存持续增长，怎么排查？

排查：
1. `redis-cli info memory` 查看内存使用
2. `redis-cli --bigkeys` 找大 key
3. `redis-cli monitor` 看实时命令（生产慎用）
4. 检查是否有 key 只写入没有设置过期时间

处理：
1. 大 key 拆分或清理
2. 设置合理的 TTL
3. 配置内存淘汰策略
4. 检查是否有内存泄漏（如 Pub/Sub 不取消订阅）

### 4. 用户反馈登录后还是 401，怎么排查？

排查链路：
1. **前端：** 检查 token 是否正确存储和发送
2. **后端鉴权：** 检查 JWT 解码是否成功，token 是否过期
3. **数据库：** 检查用户是否存在、is_active 是否为 true
4. **时钟同步：** JWT 有 exp 字段，服务器时钟偏差可能导致验证失败

常见原因：
- 前端 token 刷新逻辑有 bug
- 后端 JWT secret 不一致
- 用户被禁用但 token 还有效

### 5. LLM 调用频繁超时，怎么处理？

紧急处理：
1. 增加 timeout 配置
2. 降级到更小的模型（qwen-turbo → qwen-tiny）
3. 减少并发调用（加队列限流）

长期优化：
1. 缓存 LLM 结果（相似查询返回缓存）
2. 异步化：LLM 调用放到后台任务队列
3. 多供应商：DashScope 不可用时切换到 OpenAI
4. 优化 prompt：减少不必要的 token 消耗

### 6. 系统突然涌入大量请求，怎么应对？

应对策略：
1. **限流：** 限制每秒请求数，超出返回 429
2. **降级：** 关闭非核心功能，保证核心功能可用
3. **扩容：** 增加实例数量（自动伸缩）
4. **缓存：** 开启缓存，减少数据库压力
5. **排队：** 超出处理能力的请求排队等待

### 7. 如何保证数据一致性（如订单和库存）？

方案：
1. **本地事务：** 同一个数据库内的操作用事务保证
2. **分布式事务：**
   - 2PC（两阶段提交）：强一致但性能差
   - TCC（Try-Confirm-Cancel）：业务侵入大
   - Saga：长事务拆分，补偿机制
3. **最终一致性：** 消息队列 + 重试 + 补偿

项目中的做法：Tortoise ORM 的事务支持，`async with in_transaction()`。

### 8. 如何实现数据导出（如导出 Excel）？

方案选择：
- **小数据量（< 1 万行）：** 后端生成 Excel，返回文件流
- **大数据量（> 1 万行）：** 异步导出，生成文件后通知下载

技术实现：
1. 后端用 `openpyxl` 或 `python-docx` 生成文件
2. 文件存到对象存储或临时目录
3. 返回下载链接
4. 定期清理过期文件

项目中的简历导出：`resume_export_tool.py` 用 `python-docx` 生成 DOCX。

### 9. 如何实现多租户（Multi-tenant）？

方案：
1. **共享数据库，共享表：** 所有租户数据在同一张表，用 tenant_id 区分
2. **共享数据库，独立 Schema：** 每个租户一个 schema
3. **独立数据库：** 每个租户一个数据库

项目属于方案 1：所有用户数据在同一数据库，用 user_id 隔离。

关键考虑：
- 查询必须带 tenant_id 过滤（防止数据泄露）
- 数据量大时需要按 tenant 分片
- 跨租户查询需要特殊处理

### 10. 如何保证系统的安全性？

安全措施分层：
1. **网络层：** HTTPS、防火墙、DDoS 防护
2. **应用层：**
   - 输入校验（防 SQL 注入、XSS）
   - 认证鉴权（JWT、RBAC）
   - CORS 配置
   - Rate limiting
3. **数据层：**
   - 密码哈希（argon2）
   - 敏感数据加密存储
   - SQL 参数化查询
4. **运维层：**
   - 日志审计
   - 漏洞扫描
   - 依赖更新（防已知漏洞）

---

## 附录：八股背诵优先级

| 优先级 | 章节 | 预计背诵时间 |
|--------|------|------------|
| P0 | Python 异步（1-5）、FastAPI（1-5）、RAG/大模型（1-5） | 2 天 |
| P1 | Vue3（1-5）、PostgreSQL（1-5）、Redis（1-5） | 2 天 |
| P2 | 系统设计全部、场景题全部 | 1 天 |
| P3 | 剩余进阶题 | 随时补充 |

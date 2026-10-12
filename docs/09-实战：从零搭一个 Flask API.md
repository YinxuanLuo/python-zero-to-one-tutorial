# 第 09 章 · 实战：从零搭一个分层 Flask API

> 前面 8 章你学了一堆零散的"零件"：`def`、类、异常、`with`、类型注解、测试。
> 这一章把它们**拼成一件能跑的东西**——一个真正能 `POST`、`GET`、`PUT`、`DELETE` 的任务清单 REST API。
>
> 本章你需要记住的就一件事：**后端代码不是"一把梭"写在路由里，而是分成 路由层 → 服务层 → 仓储层 三层，每一层只干一件事。**

---

## 9.1 先想清楚：为什么要"分层"，而不是一把梭

你以前写 JS，一个接口大概是这样的（Express）：

```js
app.get("/tasks", async (req, res) => {
  const rows = await db.query("SELECT * FROM tasks");   // 查库
  const done = rows.map(r => ({ ...r, done: !!r.done })); // 加工
  res.json(done);                                         // 返回
});
```

一个函数里同时干了三件事：**读请求、查数据库、加工返回**。小项目这么写没事，
但项目一旦变大，你会撞上三堵墙：

1. **改数据库要动路由**。想从 MySQL 换成 sqlite，你得在每个接口里改 SQL。
2. **业务规则散落各处**。"标题不能为空"这条规则，可能写在了 5 个接口里，改一处漏四处。
3. **没法单独测试**。要测"校验逻辑"，你得先起一个 HTTP 服务、再连一个真数据库。

分层的本质，就是回答一个问题：**当需求变化时，你能不能只改一个文件？**

### 三层分别管什么

| 层 | 英文 | 它只管 | 它不管 |
|---|---|---|---|
| 路由层 | route | HTTP 进、HTTP 出：解析请求、调服务、返回 JSON | 不碰数据库、不写业务规则 |
| 服务层 | service | 业务规则：校验、组装、决定"能不能这么干" | 不管数据存哪、不管 HTTP 细节 |
| 仓储层 | repository | 数据存取：增删改查，SQL 全在这里 | 不懂任何业务规则 |

**依赖方向是单向的：路由 → 服务 → 仓储。** 下层永远不知道上层的存在。
所以将来想把 sqlite 换成 PostgreSQL，只改仓储层；想在接口前面加个鉴权，只改路由层。

本章的项目就是按这个结构写的，完整代码在 `examples/project/app.py`。
我们不是一口气把 300 行贴出来让你读，而是一层一层搭，边搭边验证。

### 分层的代价（以及什么时候别分层）

说句公道话，分层不是免费的。它要**多写类、多写文件、多绕一层函数调用**。

所以对一个"就 3 个接口、永远不会有第二个人改"的脚本，分层是**过度设计**。
但判断标准不是"代码有多少行"，而是：

> **这个项目会不会变？会不会有第二个人来改？会不会要换数据库、加鉴权、上规模？**

只要有一个答案是"会"，分层就值回票价。反过来说，**你写的是"一次性的脚本"，那就一把梭，
不要为了"看起来高级"去硬套分层**——这也是第 00 章"简单优于复杂"的哲学。

本章项目选"任务清单"这种典型 CRUD，恰恰是"最需要分层、又最简单到能一页讲清"的样本。

> 一句话记住它：**分层是为了让"变化"被关在某一层里，而不是炸遍全项目。**

---

## 9.2 装好 flask，搭好项目骨架

先装依赖。本教程只用一个第三方库 **flask**（轻量 Web 框架），其余全靠标准库。

```bash
pip install flask
```

本机实测装的是 flask 3.1.3，它会顺带装下 werkzeug、jinja2、click 这几个依赖：

```text
Successfully installed blinker-1.9.0 click-8.5.0 flask-3.1.3 itsdangerous-2.2.0
  jinja2-3.1.6 markupsafe-3.0.4 werkzeug-3.1.9
```

> 建议装在一个虚拟环境里（第 07 章讲过 `venv`）。本章为了省事直接在全局装，不影响理解。

验证装好了没有：

```python
import flask
print(flask.__version__)
```

```text
3.1.3
```

### 项目骨架

```
examples/project/
├── app.py            # 主程序：分层 API 的全部代码
├── smoke-test.py     # 端到端自测脚本（python 直跑，退出码 0 = 通过）
└── requirements.txt  # 依赖清单
```

`requirements.txt` 只有一行：

```text
flask>=3.0
```

为什么 `>=3.0` 而不是写死 `3.1.3`？因为 3.x 的 API 兼容，写范围能兼容你同事的旧环境；
而写死版本能保证"团队所有人跑出来一模一样"。教学项目选范围就够了，公司项目建议写死。

> 一句话记住它：**flask 是"微框架"——它只给你路由和请求响应，数据库、校验、鉴权都得你自己搭，而这恰恰是你要学的。**

---

## 9.3 Flask 的最小可运行：Flask 实例 + 路由 + jsonify

先跑起来一个最小的 Flask 应用，感受一下"一个 Python 对象就是一个 Web 服务"这件事。

```python
from flask import Flask, jsonify

app = Flask(__name__)   # 创建一个 Flask 应用实例

@app.route("/")         # 装饰器：把 "/" 这个路径绑定到下面的函数
def hello():
    return jsonify({"msg": "hello flask"})   # 把 dict 变成 JSON 响应

@app.route("/hello/<name>")   # 路径里的 <name> 是"变量"，会被传进函数参数
def hi(name):
    return jsonify({"hi": name})
```

这三行代码对应三个概念，先建立直觉：

- **`Flask(__name__)`**：创建一个"应用"。`__name__` 是当前模块名，Flask 用它定位静态文件、
  模板的位置。你几乎永远写 `Flask(__name__)` 就够了，不用深究。
- **`@app.route("/")`**：这是**装饰器**（第 03 章学过）。它的作用是"注册一条路由"——
  把 `"/"` 这个 URL 和 `hello` 这个函数绑在一起。以后有人访问 `/`，Flask 就调用 `hello`。
- **`jsonify(...)`**：把 Python 的 `dict`/`list` 转成 HTTP 响应，`Content-Type` 自动设成
  `application/json`。**等价于 Express 里的 `res.json()`。**

怎么验证它真的能跑？我们**不起真实端口**，用 Flask 内置的 `test_client()`（测试客户端）直接调用：

```python
c = app.test_client()
print(c.get("/").status_code)            # 200
print(c.get("/").get_data(as_text=True)) # {"msg":"hello flask"}
print(c.get("/hello/world").get_data(as_text=True))   # {"hi":"world"}
```

```text
200
{"msg":"hello flask"}
{"hi":"world"}
```

`test_client()` 是本章最重要的工具之一：它模拟 HTTP 请求，但不监听端口、不需要起服务，
**跑测试飞快且稳定**。后面 9.12 的 smoke-test 全靠它。

### `@app.route` 的等价写法

`@app.route("/")` 默认只响应 **GET** 方法。要响应多个方法，得写 `methods` 参数：

```python
@app.route("/inspect", methods=["GET", "POST"])   # 这个路由同时接受 GET 和 POST
def inspect():
    return jsonify({"ok": True})
```

Flask 2.0 之后还提供了 `@app.get`、`@app.post`、`@app.put`、`@app.delete` 这几个**快捷装饰器**，
语义更清晰（本章的 `app.py` 全用它们）：

```python
@app.get("/tasks")          # 等价于 @app.route("/tasks", methods=["GET"])
def list_tasks():
    ...
```

### Flask vs Express：一张对照表建立肌肉记忆

你脑子里已经有一套 Express 的路由模型，先把它映射过来，后面全是顺水推舟：

| 概念 | Express | Flask |
|---|---|---|
| 创建应用 | `const app = express()` | `app = Flask(__name__)` |
| 定义路由 | `app.get("/t", handler)` | `@app.get("/t")` |
| 路径参数 | `/tasks/:id` | `/tasks/<int:task_id>` |
| 请求对象 | `req`（函数参数） | `request`（全局代理） |
| 响应 JSON | `res.json(obj)` | `jsonify(obj)` |
| 状态码 | `res.status(201).json(x)` | `jsonify(x), 201` |
| 拿查询参数 | `req.query.page` | `request.args.get("page")` |
| 拿 JSON 体 | `req.body` | `request.get_json()` |
| 错误处理 | 中间件 `(err, req, res, next)` | `@app.errorhandler` |

最大的心理差异是：**Flask 不用传 `req`/`res`，用装饰器 + 全局 `request` + `jsonify`**。
习惯了之后你会觉得它更省事——函数签名干净，只有业务相关的参数。

### 路由匹配的细节：多段路径和尾斜杠

URL 变量可以出现在路径的任意位置，可以有多个：

```python
@app.get("/users/<int:user_id>/tasks/<int:task_id>")
def get_user_task(user_id, task_id):
    return jsonify({"user": user_id, "task": task_id})
```

访问 `/users/7/tasks/3` → `{"user": 7, "task": 3}`。

一个常被忽略的细节：**尾斜杠**。默认情况下，`@app.get("/tasks")` **不**匹配 `/tasks/`。
如果你想让两个都匹配，路由末尾要写 `/tasks/`，Flask 会做 308 重定向。对 API 来说，
**建议统一不带尾斜杠**，避免前端把 `/tasks` 和 `/tasks/` 当成两个接口。

### 第一个真实报错：路由必须在"第一次请求前"注册完

新手最容易踩的一个坑，是**发过一次请求之后，又去加路由**：

```python
app = Flask(__name__)

@app.route("/")
def hello():
    return "hi"

app.test_client().get("/")      # 第一次请求已经发出

@app.route("/later")           # 这时再加路由 → 直接炸
def later():
    return "too late"
```

运行会看到真实报错：

```text
AssertionError: The setup method 'route' can no longer be called on the application.
It has already handled its first request, any changes will not be applied consistently.
Make sure all imports, decorators, functions, etc. needed to set up the application are
done before running it.
```

**原因**：Flask 在第一次处理请求时，会把所有路由"固化"（setup finished），之后再注册就晚了。
**结论**：所有 `@app.route` / `@app.get` 必须写在"启动之前"——这正好解释了为什么后面我们用
"应用工厂 `create_app()`"把所有路由包在一个函数里，一次注册完。

> 一句话记住它：**`Flask(__name__)` 造应用，`@app.route` 绑路由，`jsonify` 出 JSON，而 `test_client()` 让你不起端口就能测。**

---

## 9.4 REST 设计：URL、动词、状态码

在写任何代码之前，先把"这个 API 长什么样"定下来。REST 不是神秘学，它的核心就一句话：

> **用 URL 表示"资源"，用 HTTP 动词表示"对资源的操作"，用状态码表示"结果"。**

### 我们设计出的接口表

| 方法 | URL | 含义 | 成功状态码 |
|---|---|---|---|
| `GET` | `/tasks` | 列出所有任务 | 200 |
| `GET` | `/tasks/<id>` | 查单个任务 | 200 |
| `POST` | `/tasks` | 新建任务 | 201 |
| `PUT` | `/tasks/<id>` | 整体更新任务 | 200 |
| `DELETE` | `/tasks/<id>` | 删除任务 | 200 |

几个和 JS 后端的对应，帮你快速迁移：

- **`/tasks/<id>`** 里的 `<id>`，等价于 Express 的 `/tasks/:id`。
- **`POST /tasks` 返回 201** 而不是 200——201 = "Created"，告诉客户端"我新建了一个资源"。
  这是 REST 的约定，很多前端会靠状态码判断行为。
- **`DELETE` 返回 200**（带一个 `{"deleted": id}`），不是 204。204 表示"无内容"，
  但返回一点信息对前端更友好。两个都合法，本项目选 200。

### URL 变量的类型转换：`<int:id>` vs `<id>`

Flask 的 URL 变量**默认是字符串**，但你可以在尖括号里指定类型。这也是它比"手写正则"舒服的地方：

```python
@app.get("/tasks/<int:task_id>")   # 只有纯数字才匹配，且 task_id 是 int
def get_task(task_id):
    return jsonify({"id": task_id, "type": type(task_id).__name__})

@app.get("/hello/<name>")          # 不写类型，默认是 str
def hi(name):
    return jsonify({"name": name, "type": type(name).__name__})
```

```text
GET /tasks/42     → {"id": 42, "type": "int"}
GET /hello/abc    → {"name": "abc", "type": "str"}
GET /tasks/abc    → 404   （因为 "abc" 不是 int，这条路由根本不匹配）
```

注意最后一行：`/tasks/abc` 会直接 **404**，因为 `<int:task_id>` 匹配不上。
这是好事——你不用再在函数里写 `if not task_id.isdigit()` 这种防御代码，Flask 帮你拦了。

### 两个动词的性质：幂等 与 安全

REST 面试高频题，也是设计接口时的实际考量。先记住两个词：

- **幂等（idempotent）**：同一个请求发 N 次，结果和发 1 次一样。
- **安全（safe）**：请求不改变服务器状态（只读）。

对照我们的动词：

| 动词 | 幂等？ | 安全？ | 说明 |
|---|---|---|---|
| `GET` | 是 | 是 | 只读，发几次都无害 |
| `POST` | **否** | 否 | 每次调用都新建一条，发 10 次建 10 条 |
| `PUT` | 是 | 否 | 整体替换，发几次结果都一样 |
| `DELETE` | 是 | 否 | 删完再删，结果一样（资源还是"不存在"） |

**`POST` 不幂等**是最容易踩的：用户狂点"提交"按钮，就会建出 10 条重复任务。
所以真实项目里，提交类接口常要做"幂等键"（给每次提交发个唯一 id，重复提交被丢弃）。
本章项目保持简单，不处理幂等，但你要知道这是 POST 的固有性质。

**`GET` 必须安全**也是硬约束：**绝不能让 `GET /tasks` 有副作用**（比如顺手删个数据）。
爬虫、浏览器预加载、重试机制都会大量发 GET，如果 GET 能改数据，就是灾难。

### 状态码：什么时候该用什么

REST 新手常犯的错是"所有错误都返回 200，把错误信息塞进 body"。
**状态码是给 HTTP 层看的，body 是给人看的，两者缺一不可。**

| 状态码 | 含义 | 本项目什么时候用 |
|---|---|---|
| 200 | OK | 查询成功、更新成功、删除成功 |
| 201 | Created | 新建成功 |
| 404 | Not Found | 资源不存在、路由不存在 |
| 405 | Method Not Allowed | 对某个 URL 用了没定义的动词 |
| 422 | Unprocessable Entity | 请求体 JSON 合法，但字段校验不过 |
| 500 | Internal Server Error | 程序自己崩了（意料之外的错误） |

为什么校验错误用 **422** 而不是 400？400 是"请求语法都错了"（比如 JSON 都解析不了），
422 是"语法对、语义不对"（JSON 合法，但 `title` 是空的）。分工更细，前端也好区分。
（本项目简化处理，把"非法 JSON"和"校验不过"都归到 422，正文里会说明。）

> 一句话记住它：**URL 是名词（资源），动词是动作，状态码是结果——三者对齐，接口才叫"RESTful"。**

---

## 9.5 请求对象 request：读查询参数、读 JSON

Flask 的 `request` 是一个**全局代理对象**（不用你传参，直接 `from flask import request` 就能用），
它装着"这一次请求"的所有信息。**等价于 Express 里的 `req`。**

### 读查询参数：request.args

`GET /tasks?page=2&size=10` 这种问号后面的键值对，在 `request.args` 里：

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.get("/inspect")
def inspect():
    return jsonify({
        "args": dict(request.args),              # 所有查询参数
        "method": request.method,                # 本次请求的动词
        "path": request.path,                    # 路径
        "ua": request.headers.get("User-Agent"), # 某个请求头
    })

c = app.test_client()
print(c.get("/inspect?page=2&size=10").get_data(as_text=True))
```

```text
{"args":{"page":"2","size":"10"},"ua":"Werkzeug/3.1.9","method":"GET","path":"/inspect"}
```

看到没：`request.args` 里 `page` 的值是字符串 `"2"`，不是数字 2。**查询参数永远是字符串**，
需要数字得自己 `int(request.args.get("page"))`——这跟 JS 里 `req.query.page` 一样要自己转。

### request 常用属性速查（对应 Express 的 req）

| Flask 写法 | Express 对应 | 含义 |
|---|---|---|
| `request.method` | `req.method` | 请求动词（"GET"/"POST"...） |
| `request.path` | `req.path` | 路径（不含查询串） |
| `request.args` | `req.query` | 查询参数 dict（值全是字符串） |
| `request.get_json()` | `req.body` | 解析后的 JSON 体（dict/list） |
| `request.headers` | `req.headers` | 请求头，`.get("X")` 取单个 |
| `request.form` | `req.body`（表单时） | 表单数据（`Content-Type: multipart/form-data`） |

`request` 是**每个请求独立**的"当前请求快照"，你不用手动传参，Flask 通过"上下文"
（context）把它和当前请求绑定。这个机制（`request` 全局可用）是 Flask 最巧妙也最容易
被误用的地方——后面 9.9 讲错误处理时会再遇到"上下文"这个概念。

### 读 JSON 请求体：request.get_json()

前端发 `POST` 时，body 里通常是一段 JSON。用 `request.get_json()` 解析成 `dict`：

```python
@app.post("/echo")
def echo():
    data = request.get_json(silent=True)   # silent=True：解析失败不抛异常，而是返回 None
    return jsonify({"type": type(data).__name__, "value": data})

c = app.test_client()
print(c.post("/echo", json={"a": 1}).get_data(as_text=True))
# 合法 JSON → dict
```

```text
{"type":"dict","value":{"a":1}}
```

关键在 `silent=True` 这个参数。对比两种情况：

| 写法 | 请求体不是合法 JSON 时 |
|---|---|
| `request.get_json()` | **抛异常**，请求直接 500 |
| `request.get_json(silent=True)` | 静默返回 `None`，你自己决定怎么处理 |

我们项目选择 `silent=True`，因为"请求体不是 JSON"是我们**预期内**的情况，应该返回一个
可读的 422，而不是让用户看到 500 堆栈：

```python
data = request.get_json(silent=True)
if data is None:
    raise ValidationError("请求体必须是合法的 JSON")
```

> `request.get_json()` 只认 `Content-Type: application/json` 的请求。如果前端忘了设这个头，
> 你拿到的是 `None`。这也是为什么"非 JSON 请求返回 422"这个测试必须存在。

> 一句话记住它：**`request.args` 读查询参数（全是字符串），`request.get_json(silent=True)` 读 JSON 体（失败返回 None，别让它炸成 500）。**

---

## 9.6 仓储层：用 sqlite3 把数据存下来

现在开始搭第一层——**仓储层（repository）**。它只负责一件事：**把数据存进去、取出来**。
用标准库 `sqlite3`，零额外依赖，最稳。

### 为什么是 sqlite3，不是 MySQL/PostgreSQL

三个理由：

1. **零依赖**。`sqlite3` 是标准库，不用装任何东西，也不用起一个数据库服务。
2. **一个文件就是一个数据库**。`todo.db` 就是个普通文件，拷走即备份，删掉即清空。
3. **API 足够教分层**。它和 MySQL 一样要"连接 → 执行 SQL → 提交 → 关闭"，
   学会了它，换 MySQL 只是换连接方式。

### sqlite3 的基本操作

先单独感受 sqlite3 怎么用，再封装进仓储层：

```python
import sqlite3

conn = sqlite3.connect("todo.db")      # 打开连接（文件不存在会自动创建）
conn.execute(
    "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)"
)
conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("写周报", 0))
conn.commit()                          # 提交，写入才真正生效

row = conn.execute("SELECT * FROM tasks").fetchone()
print(row)       # (1, '写周报', 0)
print(row[1])    # '写周报'
conn.close()
```

```text
(1, '写周报', 0)
写周报
```

几个要点：

- **`?` 占位符**：SQL 里的 `?` 会被后面元组里的值替换。**永远不要用字符串拼接 SQL**，
  否则会 SQL 注入（用户传 `'; DROP TABLE tasks;--` 就能删库）。占位符是参数化查询，天然安全。
- **`commit()`**：sqlite3 默认不自动提交，忘了 `commit` 你的插入会"看起来成功，重启就没了"。
- **`row` 是元组**：`(1, '写周报', 0)`，用下标 `row[1]` 取。但下标可读性差，
  后面我们用 `row_factory` 让它支持按列名访问。

### SQL 注入到底有多严重：一个真实演示

"为什么必须用 `?` 占位符"不是教条，是因为**不用的代价是致命的**。看一个登录场景：

```python
import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (name TEXT, password TEXT)")
conn.execute("INSERT INTO users VALUES ('alice', '123456')")

name = "alice"
password = "' OR '1'='1"              # 攻击者输入的"密码"
sql = f"SELECT * FROM users WHERE name = '{name}' AND password = '{password}'"
print(sql)
row = conn.execute(sql).fetchone()
print("登录结果:", row)               # 密码明明是错的，却查到了 alice
```

```text
SELECT * FROM users WHERE name = 'alice' AND password = '' OR '1'='1'
登录结果: ('alice', '123456')
```

**发生了什么**：攻击者输入的 `' OR '1'='1` 被拼进 SQL 后，`WHERE` 条件变成了
`password = '' OR '1'='1'`。因为 `'1'='1'` 永远为真，整个 `WHERE` 永远成立，
**于是绕过了密码验证，直接登录成功**。这就是 SQL 注入（SQL Injection），OWASP 十大安全漏洞榜首。

用 `?` 占位符，同样的输入就只是一段普通字符串，查不到任何东西：

```python
row = conn.execute(
    "SELECT * FROM users WHERE name = ? AND password = ?", (name, password)
).fetchone()
print(row)   # None，登录失败
```

```text
None
```

**一个容易踩的误区**：有人以为"Python 的 sqlite3 会拦截分号多语句，所以安全了"。确实，
`conn.execute("SELECT * FROM users; DROP TABLE users")` 会报错：

```text
sqlite3.ProgrammingError: You can only execute one statement at a time.
```

但这个拦截**只防住了"多语句"这一种注入**，`OR '1'='1` 这种**单语句内**的注入照样能绕过。
**所以结论不变：永远用占位符，别自己拼 SQL。** 这是本章唯一一条"没有例外"的规则。

### 把连接封装成上下文管理器

仓储层的每个方法都要"开连接 → 干活 → 提交 → 关闭"，这套样板代码正好用第 05 章的
`contextmanager` 收起来：

```python
from contextlib import contextmanager

class TaskRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row    # 让结果能按列名访问：row["title"]
        try:
            yield conn
            conn.commit()                 # 正常走完 → 提交
        except Exception:
            conn.rollback()               # 出错了 → 回滚
            raise
        finally:
            conn.close()                  # 无论如何 → 关闭

    def _init_db(self):
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
```

`row_factory = sqlite3.Row` 这一行很关键：它把查询结果的元组换成 `Row` 对象，
可以 `row["title"]` 按列名访问，之后转成 `dict` 也顺理成章。

### 两个容易忽略的细节：row_factory 和 lastrowid

**`row_factory` 决定"查询结果长什么样"**。默认返回元组，只能 `row[1]` 下标访问，
代码里到处都是魔法数字 `1`、`2`，可读性差。设置 `row_factory = sqlite3.Row` 后，
结果是 `Row` 对象，可以按列名访问：

```python
conn = sqlite3.connect("todo.db")
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT id, title FROM tasks").fetchone()
print(row["title"])   # 按列名访问，而不是 row[1]
```

`Row` 对象还有一个好处：`dict(row)` 能直接转成字典，仓储层返回给服务层的 `dict` 就是这么来的。

**`lastrowid` 拿到自增主键**。插入后，数据库分配的自增 id 在游标的 `lastrowid` 属性里：

```python
cur = conn.execute("INSERT INTO tasks (title, done, created_at) VALUES (?, ?, ?)", (...))
task_id = cur.lastrowid   # 刚插入那行的自增 id
```

这就是 `insert` 方法能"插入完立刻返回完整对象"的关键——不用再写一条"查最大的 id"的 SQL。

### 完整的仓储层

```python
class TaskRepository:
    # ... __init__ / _connection / _init_db 同上 ...

    @staticmethod
    def _to_dict(row):
        task = dict(row)
        task["done"] = bool(task["done"])   # sqlite 里是 0/1，转成布尔再返回
        return task

    def list_all(self):
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id, title, done, created_at FROM tasks ORDER BY id DESC"
            ).fetchall()
        return [self._to_dict(r) for r in rows]

    def find_by_id(self, task_id):
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return self._to_dict(row) if row else None

    def insert(self, title, done, created_at):
        with self._connection() as conn:
            cur = conn.execute(
                "INSERT INTO tasks (title, done, created_at) VALUES (?, ?, ?)",
                (title, done, created_at),
            )
            task_id = cur.lastrowid                    # 拿到自增 id
            row = conn.execute(
                "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return self._to_dict(row)

    def update(self, task_id, title, done):
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
                (title, done, task_id),
            )
            if cur.rowcount == 0:                      # 没更新到任何行 → id 不存在
                return None
            row = conn.execute(
                "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return self._to_dict(row)

    def delete(self, task_id):
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cur.rowcount > 0
```

注意几个**设计上的"为什么"**：

- **`insert`/`update` 返回完整的 task 对象**，而不是只返回 `True`。因为路由层要立刻把新数据
  `jsonify` 给前端，返回完整对象省得前端再 `GET` 一次。
- **`update` 用 `cur.rowcount == 0` 判断"没这行"**。`UPDATE` 一个不存在的 id 不会报错，
  只是影响 0 行，所以必须靠 `rowcount` 检测。
- **`done` 存的是整数 0/1**（sqlite 没有原生布尔），`_to_dict` 里 `bool()` 转成 `true/false`。
  这是"存储格式"和"API 输出格式"分离的体现——前端只看到干净的布尔。

仓储层可以独立测试，不依赖 Flask：

```python
import tempfile, os
repo = TaskRepository(os.path.join(tempfile.mkdtemp(), "t.db"))
t = repo.insert("写周报", False, "2026-01-01T00:00:00+00:00")
print(t)                       # {'id': 1, 'title': '写周报', 'done': False, ...}
print(repo.find_by_id(1))      # 同样的 dict
print(repo.find_by_id(999))    # None（不存在）
```

```text
{'id': 1, 'title': '写周报', 'done': False, 'created_at': '2026-01-01T00:00:00+00:00'}
{'id': 1, 'title': '写周报', 'done': False, 'created_at': '2026-01-01T00:00:00+00:00'}
None
```

> 一句话记住它：**仓储层是所有 SQL 唯一的家，`?` 占位符防注入，`contextmanager` 保证"提交或回滚、用完必关"。**

---

## 9.7 服务层：业务规则 + 手写校验

仓储层"傻乎乎"地存数据，那"什么数据能存、什么不能存"由谁定？——**服务层**。
它夹在路由和仓储中间，是**业务逻辑唯一的家**。

### 校验：先讲一个真实的布尔坑

假设我们要校验 `done` 这个字段。它来自 JSON，可能是 `true`/`false`（布尔），
也可能是 `"true"`（字符串，前端传错了）。新手很容易这么写：

```python
done = bool(data.get("done", False))
```

这一行的坑，看真实输出：

```python
print(bool("false"))   # ?
print(bool("0"))       # ?
print(bool(0))         # ?
print(bool(1))         # ?
```

```text
True
True
False
True
```

**`bool("false")` 是 `True`！** 因为 `bool()` 对非空字符串永远返回 `True`，
它看的是"有没有内容"，不是"内容是不是 false"。所以前端传 `"false"` 字符串时，
你的任务会被错误地标记成"已完成"。

这就是为什么我们要**手写一个 `_parse_done`**，把各种输入严格映射成布尔：

```python
@staticmethod
def _parse_done(value):
    # 注意顺序：bool 是 int 的子类，必须先判断 bool，否则 isinstance(value, int) 会抢先命中
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in ("true", "1"):
        return True
    if isinstance(value, str) and value.strip().lower() in ("false", "0"):
        return False
    raise ValidationError("done 必须是布尔值（true/false）")
```

那个注释是关键坑点：**`isinstance(True, int)` 的结果是 `True`**（因为布尔是整数的子类）。

```python
print(isinstance(True, int))   # True
```

```text
True
```

所以如果你先写 `if isinstance(value, int)`，`True`/`False` 会先进这一支，被 `bool(value)`
正确地转回布尔（碰巧没错）；但反过来如果顺序错了，字符串判断就永远轮不到布尔。写这种
"按类型分派"的代码，**判断顺序就是正确性本身**。

### 标题校验

```python
@staticmethod
def _validate_title(title):
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("title 不能为空")
    if len(title.strip()) > 120:
        raise ValidationError("title 不能超过 120 个字符")
```

`title.strip()` 把首尾空格去掉再判断——所以 `"   "`（纯空格）也会被判为"空"。
这也呼应了第 05 章的哲学：**在边界处（用户输入）校验，别信前端说"我检查过了"。**

### 完整的服务层

```python
class TaskService:
    def __init__(self, repository):
        self.repository = repository          # 依赖注入：服务不自己 new 仓储

    def list_tasks(self):
        return self.repository.list_all()

    def get_task(self, task_id):
        task = self.repository.find_by_id(task_id)
        if task is None:
            raise NotFoundError(f"任务 {task_id} 不存在")
        return task

    def create_task(self, data):
        title = data.get("title")
        self._validate_title(title)                 # 校验不过会抛 ValidationError
        done = self._parse_done(data.get("done", False))
        created_at = datetime.now(timezone.utc).isoformat()
        return self.repository.insert(title.strip(), done, created_at)

    def update_task(self, task_id, data):
        self.get_task(task_id)                      # 不存在 → 抛 404
        title = data.get("title")
        self._validate_title(title)
        done = self._parse_done(data.get("done", False))
        return self.repository.update(task_id, title.strip(), done)

    def delete_task(self, task_id):
        self.get_task(task_id)                      # 不存在 → 抛 404
        self.repository.delete(task_id)
```

服务层的三个特征，就是"分层"的收益所在：

1. **业务规则集中**。`_validate_title`、`_parse_done` 只在这里，改规则只改这一个文件。
2. **抛异常而不是返回错误码**。`get_task` 找不到就 `raise NotFoundError`，而不是返回 `None`
   让上层自己判断。这样路由层代码极简，错误统一交给 9.9 的 errorhandler 处理。
3. **依赖注入**。`TaskService(repository)` 由外面把仓储传进来，而不是服务自己 `new`。
   好处是测试时能塞一个"假仓储"，不碰真数据库。

关于 `created_at`：用 `datetime.now(timezone.utc).isoformat()` 生成带时区的 UTC 时间字符串，
存进 `TEXT` 列。用 UTC 是因为**时间戳要存成无歧义的标准时间**，展示时再转本地时区。

### 为什么抛异常，而不是返回 None 或错误码

新手写服务层，很容易写成这样（"返回 None 表示失败"）：

```python
def get_task(self, task_id):
    task = self.repository.find_by_id(task_id)
    if task is None:
        return None          # ❌ 用 None 表示"找不到"
    return task
```

然后路由层就得这样处理：

```python
task = service.get_task(task_id)
if task is None:
    return jsonify({"error": "not found"}), 404   # ❌ 每个路由都要写一遍
return jsonify(task)
```

**问题在于**：错误处理逻辑被**摊薄到了每一个调用点**。有 10 个接口要查任务，你就写 10 遍
`if task is None`。哪天忘了写，接口就静默返回 `null`，前端拿到一个 200 但 body 是空，
排查半天。

用**异常**（第 05 章）的写法，错误处理被**收拢到一个地方**：

```python
def get_task(self, task_id):
    task = self.repository.find_by_id(task_id)
    if task is None:
        raise NotFoundError(f"任务 {task_id} 不存在")   # ✅ 抛异常
    return task
```

路由层就不用管了——异常会"冒泡"上去，被 9.9 的 `errorhandler` 统一接住。

**对比一下两种方式的区别**：

| | 返回 None / 错误码 | 抛异常 |
|---|---|---|
| 错误处理位置 | 每个调用点 | 一处（errorhandler） |
| 漏处理的风险 | 高（静默失败） | 无（异常不处理就 500，很显眼） |
| 调用点代码 | 臃肿（一堆 if） | 极简 |
| 适合场景 | 正常业务流程 | 预期内的错误 |

**核心原则**：**"找不到资源"这类"预期内的错误"，用异常；"正常返回空列表"用返回值。**
比如 `list_tasks` 查不到任何任务，返回 `[]`（空列表）而不是抛异常——因为"列表为空"
是正常状态，不是错误。而 `get_task(999)` 是"你问的东西不存在"，是错误，要抛异常。

> 一句话记住它：**服务层是业务规则唯一的家；`bool("false")` 是 `True`，布尔字段必须手写解析，别用 `bool()` 一刀切。**

---

## 9.8 路由层 + 应用工厂：把三层拼起来

前两层都不依赖 Flask，现在写第三层——**路由层**，把它们接上 HTTP。

### 应用工厂 create_app()

```python
def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)      # 加载配置类（9.10 讲）
    if config:
        app.config.update(config)       # 测试时可以覆盖配置

    app.json.sort_keys = False          # JSON 字段顺序 = 定义顺序，读起来顺
    app.json.ensure_ascii = False       # 不把中文转义成 \uXXXX

    repository = TaskRepository(app.config["DATABASE"])
    service = TaskService(repository)   # 组装：仓储 → 服务

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/tasks")
    def list_tasks():
        return jsonify(service.list_tasks())

    @app.get("/tasks/<int:task_id>")
    def get_task(task_id):
        return jsonify(service.get_task(task_id))

    @app.post("/tasks")
    def create_task():
        data = _parse_json_body()
        task = service.create_task(data)
        return jsonify(task), 201       # 注意：201，不是 200

    @app.put("/tasks/<int:task_id>")
    def update_task(task_id):
        data = _parse_json_body()
        task = service.update_task(task_id, data)
        return jsonify(task)

    @app.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        service.delete_task(task_id)
        return jsonify({"deleted": task_id})

    # 错误处理（9.9 讲）
    ...

    return app
```

**为什么要包在 `create_app()` 里，而不是直接写一个全局 `app`？**

这叫**应用工厂模式（Application Factory）**。好处有三个：

1. **可以造多个实例**。测试时 `create_app({"DATABASE": "test.db"})` 造一个测库，
   生产 `create_app()` 造一个真库，互不污染。
2. **配置可控**。`config` 参数让每个实例能用不同配置。
3. **避免"模块一 import 就执行副作用"**。全局 `app` 在 `import` 时就会建库、读环境变量，
   这在测试和部署时都很麻烦。

### 路由层有多薄？

看 `get_task` 这个接口，从进来到出去就三行：

```python
@app.get("/tasks/<int:task_id>")
def get_task(task_id):
    return jsonify(service.get_task(task_id))
```

**路由层不写任何 if 判断**。找不到任务怎么办？服务层抛 `NotFoundError`，
9.9 的 errorhandler 会自动接住转成 404。这就是分层后路由层的理想状态：
**它只做"翻译"——把 HTTP 请求翻译成服务层调用，把服务层结果翻译成 JSON。**

### 统一解析请求体的小工具

`create_task` 和 `update_task` 都要解析 JSON，抽成一个函数：

```python
def _parse_json_body():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("请求体必须是合法的 JSON")
    return data
```

最后，模块底部留一个"直接运行"的入口：

```python
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

这个 `if __name__ == "__main__"` 是 Python 的经典判断（第 01 章讲过）：只有 `python app.py`
直接运行时才成立，`import app` 时不会执行 `app.run`——所以 smoke-test 里 `from app import create_app`
不会把服务跑起来。

### 依赖注入：为什么服务不自己 new 仓储

看服务层的构造：

```python
class TaskService:
    def __init__(self, repository):   # 仓储从外面传进来
        self.repository = repository
```

而不是：

```python
class TaskService:
    def __init__(self):
        self.repository = TaskRepository("todo.db")   # ❌ 自己 new，写死路径
```

后者的坏处是：`todo.db` 这个路径被**焊死**在服务层里，测试时想换成临时库都换不了。
前者的做法叫**依赖注入（Dependency Injection）**：**依赖由外部传入，而不是自己创建。**

好处一句话讲清：**服务层不需要知道仓储"从哪来、连的哪个库"，只需要知道"有一个仓储能用"。**
这样测试时可以塞一个假的仓储：

```python
class FakeRepo:
    def list_all(self):
        return [{"id": 1, "title": "假数据", "done": False}]

service = TaskService(FakeRepo())   # 不碰数据库也能测服务逻辑
```

依赖注入听着玄，其实就是"**把 new 提到外面去**"这一件事。本章在 `create_app()` 里组装：

```python
repository = TaskRepository(app.config["DATABASE"])   # 外面 new
service = TaskService(repository)                     # 传进去
```

> 一句话记住它：**路由层只做"翻译"，不写 if；用 `create_app()` 工厂让"测试实例"和"生产实例"各走各的配置。**

---

## 9.9 统一错误处理：自定义异常 + errorhandler

前面服务层一直在 `raise NotFoundError`、`raise ValidationError`，但没人接这些异常。
如果现在就这么跑，Flask 会返回一个**默认的 HTML 错误页**。先看 Flask 默认的 404 长什么样：

```text
<!doctype html>
<html lang=en>
<title>404 Not Found</title>
<h1>Not Found</h1>
<p>The requested URL was not found on the server. If you entered the URL manually
please check your spelling and try again.</p>
```

**问题**：这是给浏览器看的 HTML，而你的前端要的是 JSON。所以我们要把错误响应也统一成 JSON。

### 第一步：自定义异常，携带状态码和错误码

```python
class ApiError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message, status_code=None, code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class NotFoundError(ApiError):
    status_code = 404
    code = "not_found"


class ValidationError(ApiError):
    status_code = 422
    code = "validation_error"
```

为什么要两个"码"？

- **`status_code`** 是 HTTP 状态码（404/422），给 HTTP 层和浏览器看。
- **`code`** 是**机器可读的业务错误码**（`not_found`/`validation_error`），给前端代码看。

前端可以 `switch (error.code)` 来精确处理，而不是去解析人类可读的 `message` 字符串。
`message` 是给人看的，`code` 是给机器判断的——**这两个职责不能混**。

### 第二步：用 @app.errorhandler 注册处理器

Flask 的 `errorhandler` 装饰器能"接住"特定异常或状态码，返回统一格式：

```python
@app.errorhandler(ApiError)
def handle_api_error(err):
    return (
        jsonify({"error": {"code": err.code, "message": err.message}}),
        err.status_code,
    )

@app.errorhandler(404)
def handle_not_found(err):
    return (
        jsonify({"error": {"code": "not_found", "message": "路由不存在"}}),
        404,
    )

@app.errorhandler(405)
def handle_method_not_allowed(err):
    return (
        jsonify({"error": {"code": "method_not_allowed", "message": "请求方法不允许"}}),
        405,
    )

@app.errorhandler(500)
def handle_internal_error(err):
    return (
        jsonify({"error": {"code": "internal_error", "message": "服务器内部错误"}}),
        500,
    )
```

关键点：**`@app.errorhandler(ApiError)` 一个处理器接住了所有业务异常**。
因为 `NotFoundError` 和 `ValidationError` 都继承自 `ApiError`，Flask 会顺着继承链找到
最匹配的处理器。以后再新增业务异常（比如 `ConflictError`），只要继承 `ApiError`，错误响应
自动就是统一格式，一行路由都不用改。

而 `404` / `405` / `500` 这些是"框架层面的错误"（不是你自己抛的），要**按状态码**注册：
访问不存在的路由 → Flask 自动抛 404 → 走 `handle_not_found`。

### 统一格式后，错误长这样

```text
GET /tasks/999        → 404  {"error":{"code":"not_found","message":"任务 999 不存在"}}
POST /tasks {}        → 422  {"error":{"code":"validation_error","message":"title 不能为空"}}
POST /tasks "非JSON"  → 422  {"error":{"code":"validation_error","message":"请求体必须是合法的 JSON"}}
GET  /no-such-route   → 404  {"error":{"code":"not_found","message":"路由不存在"}}
DELETE /tasks         → 405  {"error":{"code":"method_not_allowed","message":"请求方法不允许"}}
```

**所有错误响应都是同一个形状**：`{"error": {"code": ..., "message": ...}}`。
前端写一次错误处理，就能吃掉所有接口的错误——这就是"统一错误处理"的价值。

### 一次"找不到任务"的完整旅程

把前面的层串起来，看 `GET /tasks/999` 这个请求从进来到出去，异常是怎么流动的：

```
1. 请求进来            GET /tasks/999
2. 路由层              匹配到 @app.get("/tasks/<int:task_id>")，task_id = 999
3. 路由层              调用 service.get_task(999)
4. 服务层              调用 repository.find_by_id(999) → 返回 None
5. 服务层              发现 None → raise NotFoundError("任务 999 不存在")
                        ↑ 异常从这里抛出来
6. 异常冒泡            穿过服务层、路由层（谁都不接）
7. errorhandler        Flask 捕获 NotFoundError，发现它继承自 ApiError
                        → 交给 handle_api_error
8. handle_api_error    读 err.status_code(404) 和 err.code("not_found")
                        → 组装成 {"error": {...}}，返回 404
```

**关键在第 6、7 步**：异常一路上没有任何一层"接住"它，一直冒泡到 Flask 的 errorhandler。
这靠的是第 05 章讲的异常机制——**你不 `try/except`，异常就自动向上传播**。
所以路由层才能那么薄：它压根不写 `try`，异常自然有人兜底。

这也是为什么 `errorhandler(ApiError)` 能一个顶所有：**多态**。`NotFoundError` 和
`ValidationError` 都是 `ApiError` 的实例，Flask 按"是不是这个类型（或其子类）"来匹配处理器。

> 一句话记住它：**自定义异常继承 `ApiError` 携带状态码和错误码，一个 `@app.errorhandler(ApiError)` 统一收口，前端只需认一个错误形状。**

---

## 9.10 配置管理：环境变量 + 配置类

一个服务跑在不同环境（开发 / 测试 / 生产），配置一定不一样：数据库路径不同、调试开关不同、
密钥不同。**硬编码配置 = 上线事故的温床。**

### 配置类：默认值集中一处

```python
import os

class Config:
    DATABASE = os.environ.get("TODO_DB_PATH", "todo.db")
```

这一行的意思：读环境变量 `TODO_DB_PATH`，读不到就用默认值 `"todo.db"`。
所以开发时什么都不用管，默认 `todo.db`；部署时设个环境变量就能换库：

```bash
# Windows（PowerShell）
$env:TODO_DB_PATH = "D:/data/prod.db"

# mac / Linux
export TODO_DB_PATH=/data/prod.db
```

### 加载配置：from_object + update

```python
def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)   # 把 Config 类里的所有大写属性读进 app.config
    if config:
        app.config.update(config)    # 允许调用方用 dict 覆盖
```

之后任何地方都能 `app.config["DATABASE"]` 拿到配置。`from_object(Config)` 是 Flask 内置方法，
它会把类里**所有大写开头的属性**（`DATABASE`）当作配置项读进来——所以配置项约定用全大写。

### 测试怎么用配置：传入临时库

这就是应用工厂 + 配置类联手的好处。smoke-test 里这样写：

```python
import tempfile, os
tmpdir = tempfile.mkdtemp()
app = create_app({"DATABASE": os.path.join(tmpdir, "test.db"), "TESTING": True})
```

- **`DATABASE`** 指向临时目录里的库，测试跑完整个目录删掉，**不碰真实的 `todo.db`**。
- **`TESTING = True`** 是 Flask 的开关，开启后错误信息更详细、测试工具更友好。

### 更完整的做法：配置继承

真实项目通常有多个环境，用**配置继承**让各环境"只写差异部分"：

```python
class Config:
    """基础配置：所有环境共有的默认值。"""
    DATABASE = os.environ.get("TODO_DB_PATH", "todo.db")

class DevelopmentConfig(Config):
    DEBUG = True              # 开发环境开调试

class ProductionConfig(Config):
    DEBUG = False             # 生产关调试
    # 生产库路径，不设默认值，强制部署时显式指定
    DATABASE = os.environ["TODO_DB_PATH"]

class TestingConfig(Config):
    TESTING = True            # 测试环境
    DATABASE = ":memory:"     # 但注意：sqlite 内存库每次连接都清空，慎用
```

然后根据环境变量决定加载哪个：

```python
import os

def create_app(config=None):
    app = Flask(__name__)
    env = os.environ.get("FLASK_ENV", "development")
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    app.config.from_object(config_map[env])
    if config:
        app.config.update(config)
    ...
```

本章项目为了可读性只保留了一个 `Config`，但你要知道**多环境配置的标准姿势是"继承 + 按环境选择"**。

（一个小坑：`ProductionConfig` 里用 `os.environ["TODO_DB_PATH"]` 而不是 `.get()`，
是为了让"忘了设环境变量"这件事**在启动时就报错**，而不是跑到一半才发现连错库——
`KeyError` 在部署时立刻暴露，比静默用错库好得多。）

> 一句话记住它：**配置走"环境变量覆盖默认值"，配合应用工厂的 `config` 参数，测试和生产的差异被一个参数隔离。**

---

## 9.11 把服务真正跑起来：app.run 与真实请求

到目前为止你都是靠 `test_client()` 在"模拟"请求。现在真的启动它，用浏览器或 `curl` 打它。

```bash
cd examples/project
python app.py
```

真实启动日志：

```text
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

然后另开一个终端，用 `curl`（Windows 10+ 自带，或 Git Bash 里有）发真实请求：

```bash
curl http://127.0.0.1:5000/health
curl -X POST http://127.0.0.1:5000/tasks -H "Content-Type: application/json" -d "{\"title\":\"真实请求\"}"
curl http://127.0.0.1:5000/tasks/1
```

```text
{"status":"ok"}

{"id":1,"title":"真实请求","done":false,"created_at":"2026-10-12T14:51:08.917684+00:00"}

{"id":1,"title":"真实请求","done":false,"created_at":"2026-10-12T14:51:08.917684+00:00"}
```

服务端控制台会打印访问日志：

```text
127.0.0.1 - - [12/Oct/2026 22:51:08] "GET /health HTTP/1.1" 200 -
127.0.0.1 - - [12/Oct/2026 22:51:08] "POST /tasks HTTP/1.1" 201 -
127.0.0.1 - - [12/Oct/2026 22:51:08] "GET /tasks/1 HTTP/1.1" 200 -
```

### 没有 curl 怎么办（Windows 用户）

Windows 自带的 `curl.exe` 对单引号支持不好，上面那行带 `-d "{\"title\":...}"` 的命令
在 CMD 里容易转义出错。两个更省心的替代：

**方案一：PowerShell 的 `Invoke-RestMethod`（Windows 自带，无需安装）：**

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
Invoke-RestMethod -Method Post http://127.0.0.1:5000/tasks `
  -ContentType "application/json" -Body '{"title":"真实请求"}'
```

**方案二：直接写一段 Python（反正你环境里一定有 Python）：**

```python
import urllib.request

req = urllib.request.Request(
    "http://127.0.0.1:5000/tasks",
    data=b'{"title": "真实请求"}',
    headers={"Content-Type": "application/json"},
    method="POST",
)
print(urllib.request.urlopen(req).read().decode())
```

```text
{"id":1,"title":"真实请求","done":false,"created_at":"2026-10-12T14:51:08.917684+00:00"}
```

本教程第九章的所有"真实 HTTP 输出"就是这么抓的——用一个线程起服务，用 `urllib` 发请求。
**你不需要装 Postman 也能调接口。**

### 两个必须知道的坑

**坑一：`debug=True` 在 Windows 下会"打印两遍"。** `debug=True` 会启动一个 reloader
（改代码自动重启），它在 Windows 下靠子进程实现，所以启动日志会打印两次、`print` 也输出两次。
这是**正常现象，不是 bug**。所以本项目的 `app.py` 里 `debug=True` 只是方便开发，
测试脚本从不用它。

**坑二：`app.run` 是开发服务器，不能用于生产。** 启动日志里那句 WARNING 不是吓唬你：
Werkzeug 的开发服务器是单线程、性能差、安全弱，生产要用 Gunicorn / uWSGI 等 WSGI 服务器。
这条边界你在面试里说得出，就是加分项。

> 一句话记住它：**`app.run` 只能开发用；`debug=True` 的 Windows 双份输出是 reloader 的正常现象，生产换 WSGI 服务器。**

---

## 9.12 端到端自测：test_client 一次测穿三层

前面每一层都能单独测，但**层与层拼起来之后会不会出问题**，得靠端到端测试。
本项目用标准库 `unittest` + `test_client`，一个脚本测穿 HTTP → 服务 → 仓储 → sqlite 四层。

### 为什么不用 pytest

第 08 章教过 pytest（功能更强），但这里故意用 **标准库 `unittest`**，原因就一条：
**`python examples/project/smoke-test.py` 一行直跑，退出码 0，零额外依赖。**
smoke-test 的意义是"装完 flask 立刻能验证环境没问题"，多一个 pytest 就多一个安装步骤。

### 测试怎么隔离数据

```python
import os, shutil, tempfile, unittest
from app import create_app

class TaskApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp()                     # 造临时目录
        db_path = os.path.join(cls._tmpdir, "test.db")
        cls.app = create_app({"DATABASE": db_path, "TESTING": True})
        cls.client = cls.app.test_client()                   # 关键：内置测试客户端

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmpdir, ignore_errors=True)       # 跑完删库
```

`test_client()` 就是 9.3 那个工具：它模拟 HTTP 请求但不起端口，**每个测试独立、飞快**。

### 覆盖五类场景

**创建 + 查询：**

```python
def test_create_and_get(self):
    r = self.client.post("/tasks", json={"title": "写周报"})
    self.assertEqual(r.status_code, 201)          # 创建返回 201
    task = r.get_json()
    self.assertEqual(task["title"], "写周报")
    self.assertFalse(task["done"])                # 布尔 False，不是 0
    self.assertIn("id", task)
    self.assertIn("created_at", task)

    r2 = self.client.get(f"/tasks/{task['id']}")
    self.assertEqual(r2.status_code, 200)
    self.assertEqual(r2.get_json()["title"], "写周报")
```

**更新：**

```python
def test_update(self):
    task_id = self.client.post("/tasks", json={"title": "旧标题"}).get_json()["id"]
    r = self.client.put(f"/tasks/{task_id}", json={"title": "新标题", "done": True})
    self.assertEqual(r.status_code, 200)
    body = r.get_json()
    self.assertEqual(body["title"], "新标题")
    self.assertTrue(body["done"])                 # 布尔 True
```

**删除（删完再查应是 404）：**

```python
def test_delete(self):
    task_id = self.client.post("/tasks", json={"title": "要删的任务"}).get_json()["id"]
    self.assertEqual(self.client.delete(f"/tasks/{task_id}").status_code, 200)
    self.assertEqual(self.client.get(f"/tasks/{task_id}").status_code, 404)
```

**错误处理（404 / 422 / 405）：**

```python
def test_get_missing_404(self):
    r = self.client.get("/tasks/999999")
    self.assertEqual(r.status_code, 404)
    self.assertEqual(r.get_json()["error"]["code"], "not_found")

def test_create_empty_title_422(self):
    r = self.client.post("/tasks", json={"title": ""})
    self.assertEqual(r.status_code, 422)
    self.assertEqual(r.get_json()["error"]["code"], "validation_error")

def test_method_not_allowed(self):
    r = self.client.delete("/tasks")              # /tasks 只有 GET/POST
    self.assertEqual(r.status_code, 405)
```

**错误响应形状统一：**

```python
def test_error_shape(self):
    body = self.client.get("/tasks/999999").get_json()
    self.assertIn("error", body)
    self.assertIn("code", body["error"])
    self.assertIn("message", body["error"])
```

### 跑起来

```bash
python examples/project/smoke-test.py
```

```text
Ran 15 tests in 0.367s

OK
```

退出码 0。15 个测试、30 多条断言，覆盖创建、查询、更新、删除、404、422、405、
错误格式统一这八大类。**这就是"端到端"的含义：一个脚本把四层全打了一遍。**

### 端到端测试的三条设计原则

这个 smoke-test 看起来简单，但藏着三条测试设计原则（第 08 章讲过，这里落地）：

1. **测行为，不测实现。** 测试里没有一句 SQL、没有碰 `repository` 对象，全是从 HTTP 层打进去，
   断言的是"状态码 + JSON 形状"。将来你把 sqlite 换成 MySQL，测试一行不用改。
2. **断言写成"包含关系"，不写"相等关系"。** 因为测试共享一个数据库，你永远不知道前面
   已经插了多少条数据。`assertIn(new_id, ids)` 稳，`assertEqual(len(data), 1)` 脆。
3. **错误也要测。** 一半的测试用例是"传错数据、访问不存在的资源、用错方法"。
   **只测 happy path（成功路径）的测试，等于没测**——线上出问题的地方从来不是成功路径。

### 跑起来

> 一句话记住它：**`test_client` 不起端口就能测穿全栈，`unittest` 零依赖直跑退出码 0，smoke-test 的意义是"装完就能验环境"。**

---

## 9.13 本章常见坑速查

| 坑 | 现象 | 原因 | 正确做法 |
|---|---|---|---|
| `bool("false")` | 传字符串 `"false"` 被当成"已完成" | `bool()` 对非空字符串永远返回 `True` | 手写 `_parse_done`，严格映射布尔 |
| `isinstance(True, int)` | 布尔分支判断错乱 | 布尔是 `int` 的子类 | 分类型判断时，`bool` 分支放最前面 |
| 忘 `commit()` | 数据"插入成功"但重启就没了 | sqlite3 不自动提交 | 用 `contextmanager` 统一 commit/rollback |
| SQL 字符串拼接 | 一传 `'; DROP TABLE` 就删库 | 拼接的 SQL 会被注入 | 一律用 `?` 占位符 + 参数元组 |
| 路由注册太晚 | `AssertionError: The setup method 'route' can no longer be called...` | 发过一次请求后，路由已固化 | 所有路由写在 `create_app()` 里，启动前注册完 |
| `request.get_json()` 不 silent | 非 JSON 请求直接 500 | 解析失败抛异常 | `get_json(silent=True)`，`None` 时返回 422 |
| `update` 不存在的 id | 返回成功却不报错 | `UPDATE` 影响 0 行不抛异常 | 用 `cur.rowcount == 0` 判断，抛 404 |
| 查询参数当数字用 | `request.args.get("page")` 是字符串 | URL 查询参数永远是字符串 | 自己 `int()` 转换并捕获异常 |
| 所有错误返回 200 | 前端分不清成败 | 状态码和 body 职责混淆 | 201/404/405/422/500 各归其位 |
| `app.run` 上生产 | 单线程、性能差、有安全警告 | 开发服务器 ≠ 生产服务器 | 生产用 Gunicorn/uWSGI |
| `debug=True` 打印两遍 | Windows 下启动日志/print 重复 | reloader 用子进程实现 | 正常现象；测试脚本别开 debug |
| 直接改全局 `app` | 测试污染真实 `todo.db` | 全局实例 import 即执行副作用 | 用 `create_app(config)` 工厂传临时库 |

---

## 9.14 本章小结

- **分层**：路由层（HTTP 进出）→ 服务层（业务规则）→ 仓储层（SQL 存取），依赖单向，变化被关在单层内。
- **Flask 最小三件套**：`Flask(__name__)` 造应用、`@app.route`/`@app.get` 绑路由、`jsonify` 出 JSON。
- **REST**：URL 是资源名词，GET/POST/PUT/DELETE 是动词，201/404/405/422 是结果，缺一不可。
- **`request`**：`request.args` 读查询参数（全是字符串），`request.get_json(silent=True)` 读 JSON 体。
- **仓储层**：sqlite3 + `?` 占位符防注入 + `contextmanager` 自动提交/回滚/关闭。
- **服务层**：业务规则集中一处，抛 `ApiError` 子类异常而不是返回错误码。
- **路由层**：只做翻译，不写 if；用 `create_app()` 应用工厂支持多实例和配置隔离。
- **统一错误**：异常携带 `status_code`（给 HTTP）+ `code`（给前端），一个 `errorhandler(ApiError)` 收口。
- **配置**：`Config` 类 + `os.environ.get` 默认值，测试用 `create_app({"DATABASE": ...})` 传临时库。
- **测试**：`unittest` + `test_client` 零依赖直跑，退出码 0，一次测穿四层。

---

## 9.15 动手练习

1. **加一个"统计"接口**：`GET /stats` 返回 `{"total": N, "done": M}`（已完成数量和总数）。
   想一想：这个逻辑应该放在哪一层？为什么不能放在路由层直接查库？

   <details><summary>参考答案</summary>

   逻辑放服务层，SQL 放仓储层。路由层只翻译：

   ```python
   # 服务层
   def stats(self):
       tasks = self.repository.list_all()
       return {"total": len(tasks), "done": sum(1 for t in tasks if t["done"])}

   # 路由层
   @app.get("/stats")
   def stats():
       return jsonify(service.stats())
   ```

   之所以不能放路由层：路由层一旦直接查库，就打破了"分层"——将来换数据库要改路由。
   </details>

2. **给 `title` 加"去重"规则**：创建任务时，如果已存在同 `title` 的任务，返回 409。
   提示：新建一个继承 `ApiError` 的 `ConflictError`，状态码 409。

   <details><summary>参考答案</summary>

   ```python
   class ConflictError(ApiError):
       status_code = 409
       code = "conflict"

   # 服务层 create_task 开头加：
   for t in self.repository.list_all():
       if t["title"] == title.strip():
           raise ConflictError("已存在同名任务")
   ```

   因为它继承了 `ApiError`，`errorhandler(ApiError)` 会自动接住它，响应格式无需改动。
   </details>

3. **给 `PUT` 改成"部分更新"（PATCH）**：只更新传入的字段，没传的字段保持原样。
   观察现在 `PUT` 的语义（`title` 必填）和 PATCH 语义的差别。

   <details><summary>参考答案</summary>

   ```python
   # 服务层
   def patch_task(self, task_id, data):
       task = self.get_task(task_id)
       title = data.get("title", task["title"])   # 没传就用原值
       self._validate_title(title)
       done = self._parse_done(data.get("done", task["done"]))
       return self.repository.update(task_id, title.strip(), done)
   ```

   差别：PUT 是"整体替换"（缺字段=删掉），PATCH 是"部分更新"（缺字段=不动）。
   </details>

4. **写一个"幂等删除"**：删除一个不存在的任务时，是返回 404 好，还是返回 200 好？
   说出理由，并实现你选择的那一种（当前实现是 404）。

   <details><summary>参考答案</summary>

   两种都常见。404 语义更清晰（"没这东西"）；200 更"幂等"（删两次结果一样）。
   本项目选 404 是为了让客户端明确知道"你删的东西本来就不在"。若选 200，改 `delete_task`：

   ```python
   def delete_task(self, task_id):
       if self.repository.find_by_id(task_id) is None:
           return False          # 不存在，静默成功
       self.repository.delete(task_id)
       return True
   ```

   关键是"想清楚语义再实现"，而不是随手写。
   </details>

5. **给 smoke-test 补一个测试**：验证"创建后立刻列表能看到这条任务"这条链路。
   注意测试之间共享数据库，断言别依赖"列表里只有这一条"。

   <details><summary>参考答案</summary>

   ```python
   def test_create_then_list_contains(self):
       r = self.client.post("/tasks", json={"title": "链路验证"})
       new_id = r.get_json()["id"]
       ids = [t["id"] for t in self.client.get("/tasks").get_json()]
       self.assertIn(new_id, ids)   # 只断言"包含"，不假设"只有它"
   ```

   共享数据库时，断言要写成"包含关系"而非"相等关系"，才不会被其他测试干扰。
   </details>

---

> 📖 **本章的配套代码**：`examples/project/app.py`、`examples/project/smoke-test.py`
> 🧪 **自测一条命令**：`python examples/project/smoke-test.py`（退出码 0 = 通过）
> 🚀 **下一章**：[第 10 章 · 测试题与答案](10-测试题与答案.md)，用五关题检验前 9 章。

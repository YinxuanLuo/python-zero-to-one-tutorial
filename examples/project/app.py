# 第 09 章配套示例：从零搭一个分层 Flask API（任务清单）
# 依赖：flask（需先 pip install flask）
# 运行：python examples/project/app.py

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from flask import Flask, jsonify, request


# ==================== 配置层 ====================
# 配置集中放在一个类里，环境变量可以覆盖默认值。
# 好处：测试时能传一个临时数据库路径，不污染真实数据。


class Config:
    """应用配置。优先读环境变量 TODO_DB_PATH，没设置就用 todo.db。"""

    DATABASE = os.environ.get("TODO_DB_PATH", "todo.db")


# ==================== 自定义异常（统一错误处理的基石） ====================
# 所有「预期内的错误」都从 ApiError 派生，错误响应格式因此能统一。


class ApiError(Exception):
    """业务异常基类。携带 HTTP 状态码和机器可读的错误码。"""

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
    """要的资源不存在，对应 HTTP 404。"""

    status_code = 404
    code = "not_found"

    def __init__(self, message="资源不存在"):
        super().__init__(message)


class ValidationError(ApiError):
    """请求数据不合法，对应 HTTP 422（Unprocessable Entity）。"""

    status_code = 422
    code = "validation_error"

    def __init__(self, message="数据校验失败"):
        super().__init__(message)


# ==================== 仓储层（repository） ====================
# 只负责「数据怎么存、怎么取」，不懂任何业务规则。
# 用标准库 sqlite3 持久化，零额外依赖。
# 好处：将来想换成 MySQL/PostgreSQL，只改这一层，服务和路由都不动。


class TaskRepository:
    """任务数据的存取。字段：id / title / done / created_at。"""

    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connection(self):
        """提供自动提交/回滚/关闭的数据库连接（呼应第 05 章的上下文管理器）。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 让查询结果能按列名访问，如 row["title"]
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

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

    @staticmethod
    def _to_dict(row):
        task = dict(row)
        # sqlite 里 done 是 0/1 整数，转成布尔再返回，API 输出才是 true/false
        task["done"] = bool(task["done"])
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
            task_id = cur.lastrowid
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
            if cur.rowcount == 0:
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


# ==================== 服务层（service） ====================
# 只关心「业务规则」，不关心数据存在哪、也不关心 HTTP 细节。
# 好处：业务逻辑和 HTTP 解耦，能脱离 Flask 单独测试。


class TaskService:
    def __init__(self, repository):
        self.repository = repository

    def list_tasks(self):
        return self.repository.list_all()

    def get_task(self, task_id):
        task = self.repository.find_by_id(task_id)
        if task is None:
            raise NotFoundError(f"任务 {task_id} 不存在")
        return task

    def create_task(self, data):
        title = data.get("title")
        self._validate_title(title)
        done = self._parse_done(data.get("done", False))
        created_at = datetime.now(timezone.utc).isoformat()
        return self.repository.insert(title.strip(), done, created_at)

    def update_task(self, task_id, data):
        # 先确认存在，不存在直接抛 404
        self.get_task(task_id)
        title = data.get("title")
        self._validate_title(title)
        done = self._parse_done(data.get("done", False))
        return self.repository.update(task_id, title.strip(), done)

    def delete_task(self, task_id):
        self.get_task(task_id)  # 不存在抛 404
        self.repository.delete(task_id)

    @staticmethod
    def _validate_title(title):
        if not isinstance(title, str) or not title.strip():
            raise ValidationError("title 不能为空")
        if len(title.strip()) > 120:
            raise ValidationError("title 不能超过 120 个字符")

    @staticmethod
    def _parse_done(value):
        # bool 是 int 的子类，所以必须先判断 bool，否则 isinstance(value, int) 会抢先命中
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        if isinstance(value, str) and value.strip().lower() in ("true", "1"):
            return True
        if isinstance(value, str) and value.strip().lower() in ("false", "0"):
            return False
        raise ValidationError("done 必须是布尔值（true/false）")


# ==================== 路由层（route）+ 应用工厂 ====================
# 只负责「HTTP 进、HTTP 出」，不碰数据库、不写业务逻辑。


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)
    # Flask 3.x 的 jsonify 默认按字母序重排 JSON 字段，
    # 关掉它让输出顺序 = SELECT 里的列顺序（id/title/done/created_at），读起来更顺。
    app.json.sort_keys = False
    # 默认会把中文转义成 \uXXXX，关掉后直接输出中文，演示和调试都更直观。
    app.json.ensure_ascii = False

    # 依赖注入：把仓储、服务组装起来，路由只认识 service
    repository = TaskRepository(app.config["DATABASE"])
    service = TaskService(repository)

    # ---- 健康检查：部署时探活用 ----
    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    # ---- 列出所有任务 ----
    @app.get("/tasks")
    def list_tasks():
        return jsonify(service.list_tasks())

    # ---- 查单个任务 ----
    @app.get("/tasks/<int:task_id>")
    def get_task(task_id):
        return jsonify(service.get_task(task_id))

    # ---- 创建任务 ----
    @app.post("/tasks")
    def create_task():
        data = _parse_json_body()
        task = service.create_task(data)
        return jsonify(task), 201

    # ---- 更新任务（整体替换） ----
    @app.put("/tasks/<int:task_id>")
    def update_task(task_id):
        data = _parse_json_body()
        task = service.update_task(task_id, data)
        return jsonify(task)

    # ---- 删除任务 ----
    @app.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        service.delete_task(task_id)
        return jsonify({"deleted": task_id})

    # ---- 统一错误处理：所有 ApiError 都走这里，响应格式一致 ----
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

    return app


def _parse_json_body():
    """统一解析请求体：不是合法 JSON 就抛 422。"""
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("请求体必须是合法的 JSON")
    return data


# 模块级 app 实例：`flask run` 或 `python app.py` 直接可用的入口
app = create_app()

if __name__ == "__main__":
    # debug=True 会启动 reloader（改代码自动重启），
    # Windows 下 reloader 会起子进程，输出会重复两次，这是正常现象。
    app.run(debug=True, port=5000)

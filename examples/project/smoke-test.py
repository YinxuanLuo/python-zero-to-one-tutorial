# 第 09 章配套自测：smoke-test.py
# 运行：python examples/project/smoke-test.py
# 退出码 0 = 全部通过。用 Flask 内置 test_client，不起真实端口，零联网。

import os
import shutil
import tempfile
import unittest

from app import create_app


class TaskApiTest(unittest.TestCase):
    """端到端测试：从 HTTP 打到 sqlite，覆盖创建/查询/更新/删除/错误处理。"""

    @classmethod
    def setUpClass(cls):
        # 每个测试类用独立的临时数据库，跑完就删，不污染真实数据
        cls._tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(cls._tmpdir, "test.db")
        cls.app = create_app({"DATABASE": db_path, "TESTING": True})
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    # ---- 健康检查 ----
    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    # ---- 创建 + 查询单个 ----
    def test_create_and_get(self):
        r = self.client.post("/tasks", json={"title": "写周报"})
        self.assertEqual(r.status_code, 201)
        task = r.get_json()
        self.assertEqual(task["title"], "写周报")
        self.assertFalse(task["done"])  # done 默认应是布尔 False，不是 0
        self.assertIn("id", task)
        self.assertIn("created_at", task)

        task_id = task["id"]
        r2 = self.client.get(f"/tasks/{task_id}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["title"], "写周报")
        self.assertEqual(r2.get_json()["id"], task_id)

    # ---- 列表 ----
    def test_list(self):
        self.client.post("/tasks", json={"title": "列表测试任务"})
        r = self.client.get("/tasks")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    # ---- 更新 ----
    def test_update(self):
        task_id = self.client.post("/tasks", json={"title": "旧标题"}).get_json()["id"]
        r = self.client.put(
            f"/tasks/{task_id}", json={"title": "新标题", "done": True}
        )
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["title"], "新标题")
        self.assertTrue(body["done"])  # 布尔 True

    # ---- 删除 ----
    def test_delete(self):
        task_id = self.client.post("/tasks", json={"title": "要删的任务"}).get_json()["id"]
        r = self.client.delete(f"/tasks/{task_id}")
        self.assertEqual(r.status_code, 200)
        # 删完再查应 404
        r2 = self.client.get(f"/tasks/{task_id}")
        self.assertEqual(r2.status_code, 404)

    # ---- 错误处理：404 ----
    def test_get_missing_404(self):
        r = self.client.get("/tasks/999999")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["error"]["code"], "not_found")

    def test_update_missing_404(self):
        r = self.client.put("/tasks/999999", json={"title": "x"})
        self.assertEqual(r.status_code, 404)

    def test_delete_missing_404(self):
        r = self.client.delete("/tasks/999999")
        self.assertEqual(r.status_code, 404)

    # ---- 错误处理：校验 422 ----
    def test_create_empty_title_422(self):
        r = self.client.post("/tasks", json={"title": ""})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.get_json()["error"]["code"], "validation_error")

    def test_create_missing_title_422(self):
        r = self.client.post("/tasks", json={})
        self.assertEqual(r.status_code, 422)

    def test_update_invalid_done_422(self):
        task_id = self.client.post("/tasks", json={"title": "x"}).get_json()["id"]
        r = self.client.put(f"/tasks/{task_id}", json={"title": "x", "done": "maybe"})
        self.assertEqual(r.status_code, 422)

    # ---- 错误处理：请求体不是 JSON ----
    def test_create_non_json_422(self):
        r = self.client.post("/tasks", data="not json", content_type="text/plain")
        self.assertEqual(r.status_code, 422)

    # ---- 错误处理：路由不存在 / 方法不允许 ----
    def test_route_not_found(self):
        r = self.client.get("/no-such-route")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["error"]["code"], "not_found")

    def test_method_not_allowed(self):
        r = self.client.delete("/tasks")  # /tasks 只有 GET/POST
        self.assertEqual(r.status_code, 405)
        self.assertEqual(r.get_json()["error"]["code"], "method_not_allowed")

    # ---- 错误响应格式统一 ----
    def test_error_shape(self):
        r = self.client.get("/tasks/999999")
        body = r.get_json()
        self.assertIn("error", body)
        self.assertIn("code", body["error"])
        self.assertIn("message", body["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

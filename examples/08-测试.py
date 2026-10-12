# 第 08 章配套示例：测试
# 运行方式（二选一，结果一样）：
#   pytest examples/08-测试.py
#   python examples/08-测试.py
# 依赖：pip install pytest（mock 部分用标准库 unittest.mock，零额外依赖）

from unittest.mock import MagicMock

import pytest

# ────────────────────────── 被测代码（业务逻辑） ──────────────────────────


def add(a, b):
    return a + b


def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("除数不能为 0")
    return a / b


def average(nums):
    if not nums:
        raise ValueError("列表不能为空")
    return sum(nums) / len(nums)


class UserService:
    """业务代码：依赖一个外部 client（真实场景里会去查数据库/调 API）。"""

    def __init__(self, client):
        self.client = client

    def get_user_name(self, user_id):
        user = self.client.fetch(user_id)
        return user["name"]


# ────────────────────────── 8.2 基本断言 ──────────────────────────


def test_add_basic():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0


def test_average():
    assert average([2, 4, 6]) == 4
    assert average([5]) == 5


# ────────────────────────── 8.3 测试异常：pytest.raises ──────────────────────────


def test_divide_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)


def test_divide_by_zero_message():
    with pytest.raises(ZeroDivisionError, match="除数不能为 0"):
        divide(1, 0)


def test_average_empty_raises():
    with pytest.raises(ValueError):
        average([])


# ────────────────────────── 8.4 fixture：准备与复用 ──────────────────────────


@pytest.fixture
def sample_numbers():
    """返回一组测试数据，多个测试函数共用。"""
    return [1, 2, 3, 4, 5]


def test_fixture_len(sample_numbers):
    assert len(sample_numbers) == 5


def test_fixture_sum(sample_numbers):
    assert sum(sample_numbers) == 15


# ────────────────────────── 8.5 参数化：一份逻辑跑多组数据 ──────────────────────────


@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (5, 5, 10),
    (-1, -1, -2),
    (100, 1, 101),
])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected


@pytest.mark.parametrize("nums, expected", [
    ([2, 4, 6], 4),
    ([1, 2, 3, 4], 2.5),
    ([10], 10),
])
def test_average_parametrized(nums, expected):
    assert average(nums) == expected


# ────────────────────────── 8.8 mock：隔离外部依赖 ──────────────────────────


def test_get_user_name_with_magicmock():
    client = MagicMock()
    client.fetch.return_value = {"name": "alice"}
    service = UserService(client)

    assert service.get_user_name(1) == "alice"
    # 还能验证"到底被怎么调用了"
    client.fetch.assert_called_once_with(1)


def test_get_user_name_called_with_wrong_id():
    client = MagicMock()
    client.fetch.return_value = {"name": "bob"}
    service = UserService(client)

    service.get_user_name(42)
    client.fetch.assert_called_once_with(42)


# ────────────────────────── 直接运行入口 ──────────────────────────
# 用 pytest 跑时，pytest 会收集上面的 test_ 函数；
# 用 python examples/08-测试.py 跑时，走下面这行，效果一样。
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

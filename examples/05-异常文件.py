# 第 05 章配套示例：异常与文件 I/O
# 运行：python examples/05-异常文件.py
# 标准库零依赖，退出码 0

import json
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

# ── 5.4 try/except/else/finally 完整语义 ──
def divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        print(f"{a} / {b} → 除数为 0！")
    else:
        print(f"{a} / {b} = {result}")
    finally:
        print("  (finally 一定会执行)")


divide(10, 2)
divide(10, 0)

# ── 5.5 捕获多个异常 + as e ──
def to_int(s):
    try:
        return int(s)
    except (ValueError, TypeError) as e:
        print(f"  转 int 失败：{type(e).__name__}: {e}")
        return None


print("to_int('abc') =", to_int("abc"))
print("to_int(None)  =", to_int(None))

# ── 5.7 异常链 raise ... from ... ──
def load_config():
    raise FileNotFoundError("config.json 不存在")

def boot():
    try:
        load_config()
    except FileNotFoundError as e:
        raise RuntimeError("启动失败：配置缺失") from e

try:
    boot()
except RuntimeError as e:
    print(f"主异常: {type(e).__name__}: {e}")
    print(f"原因:   {type(e.__cause__).__name__}: {e.__cause__}")

# ── 5.8 自定义异常 ──
class InsufficientBalanceError(Exception):
    def __init__(self, balance, amount):
        self.balance = balance
        self.amount = amount
        super().__init__(f"余额 {balance} 不足，无法扣款 {amount}")

try:
    raise InsufficientBalanceError(100, 500)
except InsufficientBalanceError as e:
    print(f"捕获自定义异常: {e}")

# ── 5.9 文件读写 + 5.10 with ──
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "notes.txt"

    # 写入
    with open(path, "w", encoding="utf-8") as f:
        f.write("第一行\n第二行\n第三行\n")

    # read / readline / readlines / 迭代
    with open(path, "r", encoding="utf-8") as f:
        print("read() 一次性读全部:", repr(f.read()))

    with open(path, "r", encoding="utf-8") as f:
        first = f.readline()
        rest = f.readlines()
        print("readline() 读一行:", repr(first))
        print("readlines() 读剩余:", rest)

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            print("迭代文件对象:", repr(line))

# ── 5.10 自定义上下文管理器（__enter__ / __exit__）──
class Managed:
    def __enter__(self):
        print("__enter__ 被调用")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"__exit__ 被调用，exc_type = {exc_type}")
        return False  # 不吞异常


with Managed():
    print("with 块内部")

# ── 5.10 contextlib.contextmanager ──
@contextmanager
def timer(name):
    print(f"{name} 开始")
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    print(f"{name} 结束，耗时 {end - start:.4f}s")


with timer("计时器"):
    time.sleep(0.001)

# ── 5.11 json 读写 ──
data = {"name": "张三", "age": 30, "hobbies": ["读书", "游泳"], "active": True}
s = json.dumps(data, ensure_ascii=False, indent=2)
print("json.dumps 结果:")
print(s)
back = json.loads(s)
print("json.loads 回来:", back)

# ── 5.12 pathlib 现代路径处理 ──
p = Path("data") / "users" / "info.json"
print("路径:", p)
print("父目录:", p.parent)
print("后缀:", p.suffix)
print("文件名:", p.name)

print("\n05 章示例全部跑完，退出码 0")

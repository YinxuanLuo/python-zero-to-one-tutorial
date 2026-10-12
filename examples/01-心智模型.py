# 第 01 章配套示例：环境与心智模型
# 运行：python examples/01-心智模型.py

import sys

# ── 1.1 Python 到底是什么：语言 + 解释器 + 标准库 ──
print("当前解释器:", sys.version.split()[0])          # 3.13.14
print("解释器路径:", sys.executable)                   # python.exe 的绝对路径
print("平台:", sys.platform)                          # win32 / darwin / linux

# 标准库自带，不需要 pip install
import json
import math
print("标准库开箱即用: json.dumps({1, 2}) ->", json.dumps([1, 2]))
print("标准库开箱即用: math.sqrt(16) ->", math.sqrt(16))

# ── 1.6 编码：源码 UTF-8，控制台可能是 GBK ──
print("当前 stdout 编码:", sys.stdout.encoding)        # Windows 控制台常是 utf-8 或 cp936
print("系统默认编码:", __import__("locale").getencoding())  # 简体中文 Windows 是 cp936(GBK)

# 输出中文时，如果控制台是 GBK 而你是 UTF-8，可能乱码/报错。
# 解法：显式重配置 stdout 为 UTF-8（在 GBK 控制台下才需要，这里演示写法）
sys.stdout.reconfigure(encoding="utf-8")
print("reconfigure 后 stdout 编码:", sys.stdout.encoding)
print("中文输出测试：你好，世界")

# ── 1.7 if __name__ == "__main__" ──
# 这个文件被直接运行，__name__ 就是 "__main__"
print("本文件作为主程序运行时 __name__ =", repr(__name__))


def add(a, b):
    return a + b


def main():
    # 真正的"入口"逻辑放在 main() 里，而不是裸露在模块顶层
    print("main() 里调用 add(1, 2) =", add(1, 2))


if __name__ == "__main__":
    # 只有当本文件被"直接运行"时才进入这里；
    # 如果被 `import` 到别的文件里，这段代码不会执行。
    main()

# ── 1.8 和 JS 的差异：显式优于隐式 ──
# Python 不做隐式类型转换，想拼字符串必须显式 str()
name = "world"
try:
    print("hello" + 1)          # 故意触发报错
except TypeError as e:
    print("Python 拒绝隐式转换 ->", type(e).__name__ + ":", e)

print("显式转换后 ->", "hello" + str(1))

# ── 1.1 包管理提示：venv / pip 无法在脚本里演示，见正文 ──
print("\n=== 第 01 章示例运行完毕，退出码 0 ===")

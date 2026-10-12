# Python 速通版 · 2 小时上手

> 写给**有 JS 基础、但没正经写过 Python**的人。
> 目标是让你**今天就能写接口**，不求讲透，只求能跑。
>
> 想搞懂"为什么"，看 [`docs/`](docs/) 完整版（15~20 小时）。
> 本文件每个小节末尾都有 `→ 深入：第 XX 章` 的路标。

---

## 目录

- [0. 先建立心智模型（5 分钟）](#0-先建立心智模型5-分钟)
- [1. 环境与文件：把代码跑起来（20 分钟）](#1-环境与文件把代码跑起来20-分钟)
- [2. 数据结构与控制流 ★最重要（35 分钟）](#2-数据结构与控制流-最重要35-分钟)
- [3. 函数与装饰器（30 分钟）](#3-函数与装饰器30-分钟)
- [4. 面向对象：够用就行（15 分钟）](#4-面向对象够用就行15-分钟)
- [5. 异常与文件（10 分钟）](#5-异常与文件10-分钟)
- [6. 十二个必踩的坑（15 分钟）](#6-十二个必踩的坑15-分钟)
- [7. 一页速查表（5 分钟）](#7-一页速查表5-分钟)
- [8. 自测 20 题（15 分钟）](#8-自测-20-题15-分钟)
- [下一步](#下一步)

---

## 0. 先建立心智模型（5 分钟）

### 三句话

**第一句：Python 是语言 + 解释器 + 标准库 + 生态的合体。**

JS 靠浏览器或 Node 才能跑；Python 靠 `CPython`（最常见的解释器）跑。
`import os`、`import json` 这些都是**标准库**，自带的，不用装。

**第二句：Python 的核心是"用可读性换速度"。**

它比 C 慢 50~100 倍，但开发效率高 3 倍。绝大多数后端瓶颈是 **I/O**（等数据库、等网络），
不是 CPU。所以"慢"在日常场景里几乎感觉不到。

**第三句：所以缩进是语法，不是风格。**

Python 用缩进代替 `{}`。你少缩进一格，直接 `IndentationError`。
这是"用剥夺排版自由，换所见即所执行"的刻意设计。

### 三条推论，能解释你 90% 的困惑

| 你看到的 | 背后的原因 |
|---|---|
| 缩进错了报 `IndentationError` | 缩进是语法，替代 `{}` 表达层次 |
| `list` 和 `tuple` 是两个东西 | 一个是可变的、一个是不可变的（可哈希） |
| `with open(...)` 能自动关文件 | 上下文管理器协议，帮你管资源 |

### 一个必须背下来的事实

> **Python 里，可变对象（list/dict/set）作默认参数、作赋值，都是"引用"而非"拷贝"。**

```python
def add(item, cart=[]):   # ❌ 坑：[] 只在定义时创建一次
    cart.append(item)
    return cart

print(add("apple"))   # ['apple']
print(add("banana"))  # ['apple', 'banana']  ← 你以为只有 banana
```

### 判断"该写多少代码"的两个原则

1. **先问"这段代码够不够可读？"** 可读性是 Python 的宪法级原则，宁可多写两行也要清晰。
2. **能用标准库就别引第三方。** Python 标准库极丰富，`json`/`os`/`urllib`/`sqlite3` 都能直接上。

> → 深入：第 [00](docs/00-设计哲学.md) 章、第 [02](docs/02-数据结构与控制流.md) 章

---

## 1. 环境与文件：把代码跑起来（20 分钟）

### 1.1 `python` 和 `py` 是两个东西

Windows 上装 Python 会带一个 **Python launcher**，命令是 `py`：

```bash
python --version   # 可能指向某个版本
py --version       # launcher，能列出所有已装版本
py -3.13           # 显式指定用 3.13
```

**多个版本共存时，用 `py` 更稳。** 本教程基于 Python 3.13 实测。

### 1.2 `venv`：每个项目一个独立环境（必须会）

Python 的包是全局装的，不同项目要的版本可能冲突。`venv` 就是"每个项目一个隔离的包环境"：

```bash
# 创建虚拟环境（一次）
python -m venv .venv

# 激活它（Windows）
.venv\Scripts\activate

# 激活后，pip 装的包都只进这个项目
pip install requests
```

激活后命令行前面会出现 `(.venv)` 前缀。**永远在虚拟环境里装包，别污染全局。**

### 1.3 编码坑：Windows 控制台默认 GBK

Python 3 源码默认 UTF-8，但 Windows 控制台默认 GBK，中文可能乱码或报错：

```text
UnicodeDecodeError: 'gbk' codec can't decode byte 0x80 in position 0
```

**解法**：读文件时显式写 `encoding="utf-8"`。输出中文乱码时，在文件头加：

```python
import sys
sys.stdout.reconfigure(encoding="utf-8")
```

> → 深入：第 [01](docs/01-环境与心智模型.md) 章

---

## 2. 数据结构与控制流 ★最重要（35 分钟）

### 2.1 四个核心容器，一张表记住

| 类型 | 写法 | 可变 | 有序 | 可哈希 | 用在哪 |
|---|---|---|---|---|---|
| `list` | `[1, 2, 3]` | ✅ | ✅ | ❌ | 顺序集合，最常用 |
| `tuple` | `(1, 2, 3)` | ❌ | ✅ | ✅ | 固定记录、作字典键 |
| `dict` | `{"a": 1}` | ✅ | ✅(3.7+) | ❌ | 键值映射 |
| `set` | `{1, 2, 3}` | ✅ | ❌ | ❌ | 去重、集合运算 |

**关键**：`list` 可变、`tuple` 不可变。不可变才能作字典键、才能进 set。

### 2.2 切片：Python 最优雅的特性之一

```python
s = "hello world"
nums = [0, 1, 2, 3, 4, 5]

s[0:5]        # 'hello'    左闭右开
s[-1]         # 'd'        负数从右数
nums[::2]     # [0, 2, 4]  步长 2
nums[::-1]    # [5,4,3,2,1,0]  反转
```

`[::-1]` 反转列表、`[::2]` 隔一个取一个，面试常考。

### 2.3 推导式：一行顶 JS 三行

```python
nums = [1, 2, 3, 4, 5]

squares = [n * 2 for n in nums]              # [2, 4, 6, 8, 10]
evens = [n for n in nums if n % 2 == 0]      # [2, 4]
d = {n: n * n for n in nums}                 # {1:1, 2:4, ...}
```

### 2.4 解包：多值赋值一行搞定

```python
a, b = 1, 2          # 同时赋两个
a, b = b, a          # 交换，不用临时变量！
first, *rest = [1, 2, 3, 4]   # first=1, rest=[2,3,4]
```

> → 深入：第 [02](docs/02-数据结构与控制流.md) 章

---

## 3. 函数与装饰器（30 分钟）

### 3.1 `*args` 和 `**kwargs`

```python
def f(a, *args, **kwargs):
    print(a)         # 位置参数
    print(args)      # 多余的位置参数 → 元组
    print(kwargs)    # 关键字参数 → 字典

f(1, 2, 3, name="alice", age=30)
# 1
# (2, 3)
# {'name': 'alice', 'age': 30}
```

### 3.2 作用域：`LEGB` 规则

```python
x = "global"

def f():
    # 读外层变量可以，改必须声明
    print(x)          # 读得到

def g():
    x = "local"       # 这其实是新建局部变量，不是改全局
    print(x)

def h():
    global x          # 声明要改全局
    x = "changed"
```

读变量按 **L（局部）→ E（闭包）→ G（全局）→ B（内建）** 顺序找。
改外层变量要用 `global`（全局）或 `nonlocal`（闭包）。

### 3.3 装饰器：把函数"包装"一下

装饰器就是一个"接收函数、返回函数"的高阶函数，用 `@` 语法糖：

```python
def log(func):
    def wrapper(*args, **kwargs):
        print(f"调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log
def add(a, b):
    return a + b

print(add(1, 2))
# 调用 add
# 3
```

**装饰器在面试里几乎必考**，理解它 = 理解"函数是一等公民"。

> → 深入：第 [03](docs/03-函数与闭包.md) 章

---

## 4. 面向对象：够用就行（15 分钟）

### 4.1 `self` 是什么

```python
class Dog:
    def __init__(self, name):   # 构造函数
        self.name = name        # self 就是"当前这个实例"

    def bark(self):
        return f"{self.name} 汪汪"

d = Dog("旺财")
print(d.bark())   # 旺财 汪汪
```

`self` 相当于 JS 里的 `this`，但要**显式写在每个方法的第一个参数**（这是"显式优于隐式"）。

### 4.2 继承和 `super()`

```python
class Animal:
    def __init__(self, name):
        self.name = name

class Cat(Animal):
    def __init__(self, name):
        super().__init__(name)   # 调用父类构造
```

### 4.3 鸭子类型：不看类型，看行为

```python
def make_sound(thing):
    return thing.sound()   # 只要有 .sound() 就能用，不管它是什么类
```

> → 深入：第 [04](docs/04-面向对象.md) 章

---

## 5. 异常与文件（10 分钟）

### 5.1 `try/except` 抓异常

```python
try:
    x = 1 / 0
except ZeroDivisionError as e:
    print(f"出错了: {e}")   # 出错了: division by zero
finally:
    print("总是执行")
```

抓**具体**异常类型，别用裸 `except:`（会把 `KeyboardInterrupt` 都吞掉）。

### 5.2 `with` 自动关文件

```python
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()
# 出了 with 块，文件自动关闭，不用手写 finally
```

> → 深入：第 [05](docs/05-异常与文件IO.md) 章

---

## 6. 十二个必踩的坑（15 分钟）

| # | 坑 | 现象 | 正确做法 |
|---|---|---|---|
| 1 | 缩进混用 Tab/空格 | `IndentationError` | 统一 4 空格 |
| 2 | 可变默认参数 | 两次调用共享同一个 `[]` | 用 `None` + 内部判空 |
| 3 | `is` 当 `==` 用 | 数字/短字符串之外结果不对 | 比值用 `==`，比身份才用 `is` |
| 4 | 浅拷贝误当深拷贝 | 改副本影响原对象 | 用 `copy.deepcopy` |
| 5 | 循环里改列表 | 漏元素或越界 | 遍历副本 `for x in list[:]` |
| 6 | 裸 `except:` | 吞掉所有异常 | 抓具体类型 |
| 7 | 忘记 `encoding="utf-8"` | Windows 下乱码/报错 | 显式写编码 |
| 8 | 全局污染 | 不激活 venv 就 pip | 每项目一个 venv |
| 9 | `lambda` 闭包晚绑定 | 循环里的 lambda 全用最后值 | 用默认参数捕获 |
| 10 | 字符串拼接用 `+` 循环 | O(n²) 慢 | 用 `"".join()` |
| 11 | `1 / 2` 当整除 | 得到 `0.5` 不是 `0` | 整除用 `//` |
| 12 | 忘了 `if __name__ == "__main__"` | import 时误执行 | 入口加判断 |

> 每个坑的完整展开在完整版对应章节的「本章常见坑速查」里。

---

## 7. 一页速查表（5 分钟）

| 需求 | Python 写法 |
|---|---|
| 遍历带下标 | `for i, x in enumerate(xs)` |
| 同时遍历两个 | `for a, b in zip(xs, ys)` |
| 条件三目 | `a if cond else b` |
| 判断空 | `if not xs:`（空 list/dict/str 都是 falsy） |
| 列表去重 | `list(set(xs))` |
| 字符串格式化 | `f"hello {name}"` |
| 读取 JSON | `import json; json.loads(s)` |
| 生成随机数 | `import random; random.randint(1, 10)` |
| 执行命令 | `import subprocess; subprocess.run([...])` |
| 日期时间 | `from datetime import datetime; datetime.now()` |

---

## 8. 自测 20 题（15 分钟）

判断对错，答案在下方折叠区。

1. Python 的缩进只是风格，写错了不影响运行。
2. `list` 可变，`tuple` 不可变。
3. `is` 和 `==` 完全等价。
4. `[n for n in range(10) if n % 2 == 0]` 会得到 `[0,2,4,6,8]`。
5. `def f(x, lst=[]):` 是安全的默认参数写法。
6. `with open(...)` 能自动关闭文件。
7. `1 / 2` 在 Python 里结果是 `0`。
8. `@decorator` 是语法糖，等价于 `func = decorator(func)`。
9. 函数默认可以修改全局变量，不用声明 `global`。
10. `set` 里的元素可以重复。
11. Python 是编译型语言。
12. `pip install` 前应该先激活虚拟环境。
13. `"".join(["a", "b"])` 结果是 `"ab"`。
14. 字符串是不可变对象。
15. `a, b = b, a` 可以交换两个变量的值。
16. GIL 让 Python 多线程永远无法并行。
17. `enumerate([...])` 返回下标和元素的组合。
18. `f-string` 是 Python 3.6+ 才有的。
19. 裸 `except:` 是推荐的最佳实践。
20. `match/case` 需要 Python 3.10+。

<details>
<summary>查看答案</summary>

| # | 答案 | 解析 |
|---|---|---|
| 1 | 错 | 缩进是语法，写错报 `IndentationError` |
| 2 | 对 | list 可增删改，tuple 创建后不能改 |
| 3 | 错 | `is` 比对象身份，`==` 比值相等 |
| 4 | 对 | 推导式：过滤 + 映射 |
| 5 | 错 | 可变默认参数是经典坑，两次调用共享一个 `[]` |
| 6 | 对 | 上下文管理器协议自动清理资源 |
| 7 | 错 | `1/2` 是 `0.5`，整除要用 `//` |
| 8 | 对 | `@decorator` 就是 `func = decorator(func)` |
| 9 | 错 | 改全局变量必须 `global` 声明，否则是新建局部变量 |
| 10 | 错 | set 元素唯一，重复的会被去重 |
| 11 | 错 | Python 是解释型（严格说是"解释执行"） |
| 12 | 对 | venv 隔离项目依赖 |
| 13 | 对 | `join` 用空串连接 |
| 14 | 对 | str 是不可变对象 |
| 15 | 对 | 解包交换 |
| 16 | 错 | GIL 限制多线程 CPU 并行，但多进程/asyncio 能绕开 |
| 17 | 对 | `enumerate` 返回 `(下标, 元素)` |
| 18 | 对 | f-string 3.6 引入 |
| 19 | 错 | 裸 except 会吞掉所有异常，应抓具体类型 |
| 20 | 对 | 结构匹配 3.10 引入 |

</details>

---

## 下一步

- 想搞懂"为什么这么设计" → 从 [第 00 章](docs/00-设计哲学.md) 读起。
- 想直接干项目 → [第 09 章实战](docs/09-实战：从零搭一个 Flask API.md)。
- 面试前突击 → [第 11 章面试速查表](docs/11-面试速查表.md)。

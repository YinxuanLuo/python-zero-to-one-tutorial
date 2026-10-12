# 第 03 章配套示例：函数与闭包
# 运行：python examples/03-函数.py
# 风格：4 空格缩进、双引号、snake_case（PEP 8）

from functools import reduce

# ── 3.1 函数定义：位置参数 + 关键字参数 + 默认参数 ──
def greet(name, greeting="hello"):
    return f"{greeting}, {name}"

print(greet("alice"))                    # hello, alice
print(greet("bob", greeting="hi"))       # hi, bob
print(greet(greeting="yo", name="carol"))  # yo, carol

# ── 3.2 可变默认参数的坑：正确做法是 None ──
def add_item(item, cart=None):
    if cart is None:
        cart = []        # 每次调用都新建一个空列表
    cart.append(item)
    return cart

print(add_item("apple"))                  # ['apple']
print(add_item("banana"))                 # ['banana']  这才是你想要的

# ── 3.3 *args 和 **kwargs：收集任意个参数 ──
def collect(*args, **kwargs):
    return args, kwargs

print(collect(1, 2, 3, name="alice", age=20))
# ((1, 2, 3), {'name': 'alice', 'age': 20})

# ── 3.4 参数解包：用 * 和 ** 把容器拆开传 ──
def add3(a, b, c):
    return a + b + c

nums = [1, 2, 3]
print(add3(*nums))                        # 6

info = {"a": 1, "b": 2, "c": 3}
print(add3(**info))                       # 6

# ── 3.5 只位置参数 / 和只关键字参数 * ──
def configure(host, /, port=80, *, debug=False):
    return host, port, debug

print(configure("localhost"))             # ('localhost', 80, False)
print(configure("localhost", 8080, debug=True))  # ('localhost', 8080, True)

# ── 3.6 作用域 LEGB + global ──
total = 0

def bump():
    global total          # 不写这句，下一行会报 UnboundLocalError
    total += 1
    return total

print(bump(), bump())                     # 1 2

# ── 3.7 nonlocal：改闭包外层变量 ──
def make_counter():
    count = 0
    def inc():
        nonlocal count    # 改的是 make_counter 里的 count，不是全局
        count += 1
        return count
    return inc

counter = make_counter()
print(counter(), counter(), counter())    # 1 2 3

# ── 3.8 闭包：函数记住了出生地的变量 ──
def make_multiplier(n):
    def multiply(x):
        return x * n      # n 来自外层函数，被"记住"了
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)
print(double(10), triple(10))             # 20 30

# ── 3.9 闭包晚绑定陷阱：默认参数捕获当前值 ──
funcs_bad = [lambda: i for i in range(3)]
print([f() for f in funcs_bad])           # [2, 2, 2]  都是最后一个 i

funcs_good = [lambda i=i: i for i in range(3)]
print([f() for f in funcs_good])          # [0, 1, 2]  各自记住自己的 i

# ── 3.10 装饰器：接收函数返回函数 ──
def log_call(fn):
    def wrapper(*args, **kwargs):
        print(f"调用 {fn.__name__}{args}")
        result = fn(*args, **kwargs)
        print(f"返回 {result}")
        return result
    return wrapper

@log_call
def add(a, b):
    return a + b

add(2, 3)
# 调用 add(2, 3)
# 返回 5

# ── 3.11 带参数的装饰器：三层嵌套 ──
def repeat(times):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            return [fn(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorator

@repeat(3)
def say():
    return "hi"

print(say())                              # ['hi', 'hi', 'hi']

# ── 3.12 functools.wraps：保住原函数的元信息 ──
import functools

def my_decorator(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

@my_decorator
def documented():
    """这份文档不能丢。"""
    return "ok"

print(documented.__name__, documented.__doc__)   # documented 这份文档不能丢。

# ── 3.13 lambda：一行匿名函数 ──
square = lambda x: x * x
print(square(9))                          # 81

# ── 3.14 map / filter / reduce ──
nums = [1, 2, 3, 4, 5]
print(list(map(lambda x: x * 2, nums)))   # [2, 4, 6, 8, 10]
print(list(filter(lambda x: x % 2 == 0, nums)))  # [2, 4]
print(reduce(lambda a, b: a + b, nums))   # 15

# ── 3.15 sorted 的 key：按规则排序 ──
words = ["banana", "apple", "Cherry"]
print(sorted(words))                      # ['Cherry', 'apple', 'banana']  按码点
print(sorted(words, key=str.lower))       # ['apple', 'banana', 'Cherry']  忽略大小写

# ── 3.16 生成器 yield / yield from ──
def count_up(n):
    i = 0
    while i < n:
        yield i       # 每次停在这，下次从这继续
        i += 1

def chained():
    yield "start"
    yield from count_up(3)   # 把另一个生成器"接"进来
    yield "end"

print(list(chained()))                    # ['start', 0, 1, 2, 'end']

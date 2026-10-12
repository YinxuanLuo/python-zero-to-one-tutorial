# 第 02 章配套示例：数据结构与控制流
# 运行：python examples/02-数据结构.py

import copy

# ── 2.1 四个容器：list / tuple / dict / set ──
names = ["alice", "bob", "carol"]        # list：可变、有序
point = (3, 4)                            # tuple：不可变、有序
user = {"name": "alice", "age": 30}       # dict：键值映射
tags = {"python", "js", "python"}         # set：去重、无序

print("list:", names)
print("tuple:", point)
print("dict:", user)
print("set(自动去重):", tags)

# ── 2.2 list 常用方法 ──
nums = [3, 1, 2]
nums.append(4)                 # 尾部追加
nums.sort()                    # 原地排序
nums.insert(0, 99)             # 指定位置插入
last = nums.pop()              # 弹出尾部
nums.remove(99)                # 按值删除
print("list 操作后:", nums, "| 弹出的:", last)

# ── 2.6 可变 vs 不可变 ──
a = [1, 2, 3]
b = a                          # b 和 a 是同一个对象（引用）
b.append(4)
print("b 改了 a 也变:", a)      # [1, 2, 3, 4]

s = "abc"
try:
    s[0] = "x"                 # str 不可变，故意报错
except TypeError as e:
    print("str 不可变 ->", type(e).__name__ + ":", e)

# ── 2.7 切片 ──
text = "hello world"
seq = [0, 1, 2, 3, 4, 5]
print("text[0:5] =", text[0:5])
print("text[-1]  =", text[-1])
print("seq[::2]  =", seq[::2])
print("seq[::-1] =", seq[::-1])   # 反转

# ── 2.8 推导式与生成器表达式 ──
squares = [n * n for n in range(6)]
evens = [n for n in range(10) if n % 2 == 0]
d = {n: n * n for n in range(5)}
s2 = {n % 3 for n in range(10)}
gen = (n * n for n in range(3))   # 生成器表达式，惰性
print("列表推导:", squares)
print("带过滤推导:", evens)
print("字典推导:", d)
print("集合推导:", s2)
print("生成器表达式:", gen, "->", list(gen))

# ── 2.9 解包 / enumerate / zip ──
a, b = 1, 2
a, b = b, a                      # 交换，无需临时变量
print("交换后 a, b =", a, b)

first, *rest = [1, 2, 3, 4]
print("first, rest =", first, rest)

for i, v in enumerate(["a", "b", "c"]):
    print("enumerate:", i, v)

print("zip:", list(zip([1, 2, 3], ["a", "b", "c"])))

# ── 2.10 控制流 ──
for n in range(5):
    if n == 2:
        continue                # 跳过本次
    if n == 4:
        break                   # 终止循环
    print("for 循环 n =", n)

count = 0
while count < 3:
    print("while count =", count)
    count += 1

# match/case（Python 3.10+）
def describe(x):
    match x:
        case 0:
            return "零"
        case int() as n if n > 0:
            return f"正整数 {n}"
        case str():
            return f"字符串 {x}"
        case _:
            return "其他类型"

print("match 0:", describe(0))
print("match 5:", describe(5))
print("match hi:", describe("hi"))
print("match 1.5:", describe(1.5))

# ── 2.11 深浅拷贝 ──
orig = [[1, 2], [3, 4]]
shallow = copy.copy(orig)
deep = copy.deepcopy(orig)
orig[0].append(99)
print("改原对象后 shallow[0] =", shallow[0])   # 被影响（共享内层）
print("改原对象后 deep[0]    =", deep[0])      # 不受影响（完整复制）

print("\n=== 第 02 章示例运行完毕，退出码 0 ===")

# 第 00 章配套示例：设计哲学
# 运行：python examples/00-设计哲学.py

# ── 0.5 可读性：for 直接遍历 ──
names = ["alice", "bob", "carol"]
for name in names:
    print(name)
# alice / bob / carol

# ── 0.7 万物皆对象：函数也是对象 ──
def greet():
    print("hi")

f = greet          # 函数赋值给变量
f()                # hi
print(type(greet)) # <class 'function'>

# ── 0.7 鸭子类型 ──
class Duck:
    def quack(self):
        return "嘎"

class Person:
    def quack(self):
        return "我在模仿鸭子"

def quack(thing):
    return thing.quack()   # 不看类型，只看有没有 .quack()

print(quack(Duck()))       # 嘎
print(quack(Person()))     # 我在模仿鸭子

# ── 0.6 显式优于隐式：print 是函数 ──
old_print = print
print = lambda *a, **k: old_print("【前缀】", *a, **k)
print("hello")             # 【前缀】 hello

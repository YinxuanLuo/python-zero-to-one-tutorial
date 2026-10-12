# 第 04 章配套示例：面向对象
# 运行：python examples/04-面向对象.py
# 风格：4 空格缩进、双引号、snake_case（PEP 8）

# ── 4.1 class / __init__ / self ──
class Dog:
    def __init__(self, name):
        self.name = name        # self 相当于 JS 的 this，但必须显式写

    def bark(self):
        return f"{self.name} 说：汪"

d = Dog("旺财")
print(d.bark())                     # 旺财 说：汪

# ── 4.2 实例属性 vs 类属性 ──
class Cat:
    species = "猫科"              # 类属性：所有实例共享

    def __init__(self, name):
        self.name = name          # 实例属性：各自独立

c1 = Cat("咪咪")
c2 = Cat("球球")
print(c1.species, c2.species)     # 猫科 猫科  都读到了类属性
print(c1.name, c2.name)           # 咪咪 球球  实例属性互不影响

# ── 4.3 类属性共享的坑：用实例属性绕开 ──
class Toy:
    def __init__(self):
        self.parts = []           # 每个实例一份，不共享

t1 = Toy()
t2 = Toy()
t1.parts.append("轮子")
print(t1.parts, t2.parts)         # ['轮子'] []

# ── 4.4 继承 + super ──
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "……"

class Bird(Animal):
    def __init__(self, name, can_fly):
        super().__init__(name)    # 调用父类的 __init__
        self.can_fly = can_fly

    def speak(self):
        return "啾啾"

b = Bird("小黄", can_fly=True)
print(b.name, b.speak(), b.can_fly)   # 小黄 啾啾 True

# ── 4.5 MRO：多继承的方法解析顺序 ──
class A:
    def who(self):
        return "A"

class B(A):
    def who(self):
        return "B>" + super().who()

class C(A):
    def who(self):
        return "C>" + super().who()

class D(B, C):
    def who(self):
        return "D>" + super().who()

print([c.__name__ for c in D.mro()])   # ['D', 'B', 'C', 'A', 'object']
print(D().who())                       # D>B>C>A   super 按 MRO 一路走

# ── 4.6 @property / @setter ──
class Circle:
    def __init__(self, radius):
        self.radius = radius

    @property
    def area(self):
        return 3.14159 * self.radius ** 2   # 看起来像属性，其实是方法

c = Circle(2)
print(round(c.area, 2))              # 12.57

class Temperature:
    def __init__(self):
        self._celsius = 0

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("低于绝对零度")
        self._celsius = value

t = Temperature()
t.celsius = 25                      # 走 setter，做校验
print(t.celsius)                    # 25

# ── 4.7 @classmethod / @staticmethod ──
class Config:
    default_port = 8080

    @classmethod
    def get_port(cls):              # 第一个参数是类本身
        return cls.default_port

    @staticmethod
    def is_valid(value):            # 不需要 self / cls
        return 0 <= value <= 65535

print(Config.get_port())            # 8080
print(Config.is_valid(8080), Config.is_valid(99999))   # True False

# ── 4.8 魔术方法 ──
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):             # 给开发者看 / 容器里显示
        return f"Vector({self.x}, {self.y})"

    def __str__(self):              # 给用户看 / print
        return f"({self.x}, {self.y})"

    def __eq__(self, other):        # ==
        return (self.x, self.y) == (other.x, other.y)

    def __lt__(self, other):        # < 按长度比较
        return self.len() < other.len()

    def __len__(self):              # len()
        return 2

    def __getitem__(self, index):   # v[i]
        return (self.x, self.y)[index]

    def len(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

v = Vector(3, 4)
print(str(v), repr(v))              # (3, 4) Vector(3, 4)
print(v == Vector(3, 4))            # True
print(v < Vector(5, 5))             # True  长度 5 < 7.07
print(len(v), v[0], v[1])           # 2 3 4
print([v, Vector(1, 1)])            # [Vector(3, 4), Vector(1, 1)]  容器走 __repr__

# ── 4.9 鸭子类型：不看类型看行为 ──
class Duck:
    def quack(self):
        return "嘎"

class Person:
    def quack(self):
        return "我在模仿鸭子"

def make_quack(thing):
    return thing.quack()            # 不检查类型，只要有 .quack() 就能用

print(make_quack(Duck()))           # 嘎
print(make_quack(Person()))         # 我在模仿鸭子

# ── 4.10 __slots__：省内存 + 禁止乱加属性 ──
class Point:
    __slots__ = ("x", "y")          # 只能有 x、y 两个属性

    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
print(p.x, p.y)                     # 1 2
print(hasattr(p, "__dict__"))       # False  __slots__ 类没有实例字典

# 第 07 章配套示例：工程化与类型标注
# 运行：python examples/07-类型标注.py
# 说明：类型注解在运行时几乎不做事，真正干活的是静态检查器 mypy。
#       本文件聚焦"注解长什么样、能表达什么"，全部可运行。

from dataclasses import dataclass, field
from typing import Callable, Generic, Protocol, TypedDict, TypeVar

# ── 7.2 函数注解与变量注解 ──

def add(a: int, b: int) -> int:
    return a + b


def greet(name: str) -> str:
    return f"hello, {name}"


name: str = "alice"
age: int = 30
score: float = 98.5
is_active: bool = True

print(add(1, 2))            # 3
print(greet("world"))       # hello, world
print(name, age, score, is_active)   # alice 30 98.5 True

# ── 7.2 泛型容器：list[int] / dict[str, int]（3.9+） ──

nums: list[int] = [1, 2, 3]
scores: dict[str, int] = {"alice": 90, "bob": 80}
matrix: list[list[int]] = [[1, 2], [3, 4]]

print(nums)                 # [1, 2, 3]
print(scores)               # {'alice': 90, 'bob': 80}
print(matrix)               # [[1, 2], [3, 4]]

# ── 7.2 Optional / Union：这个值可能是 None ──

def find_user(user_id: int) -> str | None:
    # 3.10+ 的 | 写法；老版本用 Optional[str]
    users = {1: "alice", 2: "bob"}
    return users.get(user_id)


result = find_user(1)
print(result)               # alice
print(find_user(99))        # None

# 类型别名：把复杂类型起个名字
UserId = int
UserDict = dict[int, str]

u: UserDict = {1: "alice"}
print(u)                    # {1: 'alice'}

# ── 7.6 dataclass：自动生成 __init__/__repr__/__eq__ ──

@dataclass
class Point:
    x: int
    y: int


@dataclass
class User:
    name: str
    age: int = 18                 # 有默认值的字段
    tags: list[str] = field(default_factory=list)  # 可变默认值必须用 default_factory


p1 = Point(1, 2)
p2 = Point(1, 2)
p3 = Point(3, 4)
print(p1)                        # Point(x=1, y=2)   ← __repr__ 自动生成
print(p1 == p2)                  # True               ← __eq__ 按字段值比较
print(p1 == p3)                  # False

u1 = User("alice")
u2 = User("bob", tags=["vip"])
u1.tags.append("new")            # 每个实例的 tags 是独立列表
print(u1)                        # User(name='alice', age=18, tags=['new'])
print(u2)                        # User(name='bob', age=18, tags=['vip'])

# ── 7.5 TypedDict：给字典的"形状"做注解 ──

class Movie(TypedDict):
    title: str
    year: int


movie: Movie = {"title": "The Matrix", "year": 1999}
print(movie)                     # {'title': 'The Matrix', 'year': 1999}
print(movie["title"])            # The Matrix

# ── 7.5 TypeVar + Generic：让函数/类保留类型关系 ──

T = TypeVar("T")


def first(items: list[T]) -> T | None:
    return items[0] if items else None


print(first([1, 2, 3]))          # 1
print(first(["a", "b"]))         # a


class Box(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value


int_box = Box(42)
str_box = Box("hi")
print(int_box.get())             # 42
print(str_box.get())             # hi

# ── 7.5 Protocol：把鸭子类型"显式化" ──

class HasArea(Protocol):
    def area(self) -> float: ...


class Square:
    def __init__(self, side: float) -> None:
        self.side = side

    def area(self) -> float:
        return self.side * self.side


class Circle:
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return 3.14 * self.radius * self.radius


def total_area(shapes: list[HasArea]) -> float:
    return sum(s.area() for s in shapes)


# 运行时仍走鸭子类型：只要对象有 area() 就能传
print(total_area([Square(2), Circle(3)]))   # 32.26 (4 + 28.26)

# ── 7.5 Callable：注解"一个函数" ──

def apply_twice(f: Callable[[int], int], x: int) -> int:
    return f(f(x))


def plus_one(n: int) -> int:
    return n + 1


print(apply_twice(plus_one, 10))   # 12

# ── 7.3 注解在运行时"不执法"：这段能跑，但 mypy 会报错 ──

def fake_typed(x: int) -> int:
    return x


# 传个字符串进去，运行时完全不拦你
print(fake_typed("not a number"))   # not a number

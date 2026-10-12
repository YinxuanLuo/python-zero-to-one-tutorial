"""第五关 · 第 2 题：记忆化装饰器

实现 @memoize：用字典缓存函数结果，相同参数第二次调用直接返回缓存。
必须用 functools.wraps 保留原函数元数据。

运行：python a2-memoize.py
"""
from functools import wraps


def memoize(func):
    cache = {}

    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return wrapper


@memoize
def fib(n):
    """返回第 n 个斐波那契数（n 从 0 开始）。"""
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


if __name__ == "__main__":
    print(fib(30))          # 832040，加 @memoize 后瞬间算出
    print(fib.__name__)     # fib（@wraps 保留了函数名）
    print(fib.__doc__.strip()[:20])   # 文档字符串也被保留

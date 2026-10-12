"""第五关 · 第 1 题：LRU 缓存

用 collections.OrderedDict 实现 LRU（Least Recently Used）缓存：
- get：键存在返回值并标记为最近使用；不存在返回 -1
- put：写入键值，超容量时淘汰最久未使用的项

运行：python a1-lru-cache.py
"""
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = OrderedDict()

    def get(self, key):
        if key not in self.data:
            return -1
        # 被访问过，移到末尾表示"最近使用"
        self.data.move_to_end(key)
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data.move_to_end(key)
        self.data[key] = value
        # 超容量时弹出最前面的（最久未使用）
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put(1, "a")
    cache.put(2, "b")
    print(cache.get(1))   # a（1 变成最近使用）
    cache.put(3, "c")     # 淘汰最久未用的 2
    print(cache.get(2))   # -1（2 已被淘汰）
    print(cache.get(3))   # c
    print(cache.get(1))   # a（1 刚被访问过，还在）

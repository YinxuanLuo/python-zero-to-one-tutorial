"""第五关 · 第 4 题：递归深拷贝

不借助 copy.deepcopy，自己写 deep_copy(obj)，能复制嵌套的
list / dict / tuple / set 以及普通不可变对象。

运行：python a4-deep-copy.py
"""


def deep_copy(obj):
    if isinstance(obj, list):
        return [deep_copy(x) for x in obj]
    if isinstance(obj, dict):
        return {deep_copy(k): deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return tuple(deep_copy(x) for x in obj)
    if isinstance(obj, set):
        return {deep_copy(x) for x in obj}
    # int / str / float / bool / None 等不可变对象，直接返回
    return obj


if __name__ == "__main__":
    original = {
        "nums": [1, 2, [3, 4]],
        "point": (5, 6),
        "tags": {7, 8},
        "name": "deep",
    }

    copied = deep_copy(original)
    copied["nums"][2].append(99)

    print(original["nums"])   # [1, 2, [3, 4]]  原对象不受影响
    print(copied["nums"])     # [1, 2, [3, 4, 99]]
    print(original["nums"] is copied["nums"])        # False（外层列表独立）
    print(original["nums"][2] is copied["nums"][2])  # False（内层也独立）

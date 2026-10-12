"""第五关 · 第 3 题：数据校验（鸭子类型版）

写 validate_user(data)，只要求 data 支持 .get()（不检查类型）：
- name：非空字符串
- age：0~120 之间的整数

返回 (是否通过, 错误列表)。

运行：python a3-validate-user.py
"""


def validate_user(data):
    errors = []

    name = data.get("name")
    age = data.get("age")

    if not isinstance(name, str) or name == "":
        errors.append("name 必须是非空字符串")
    if not isinstance(age, int) or isinstance(age, bool) or not (0 <= age <= 120):
        errors.append("age 必须是 0~120 之间的整数")

    return (len(errors) == 0, errors)


class MyDict:
    """一个只实现 .get() 的自定义对象，用于验证鸭子类型。"""

    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        return self._data.get(key, default)


if __name__ == "__main__":
    # 普通 dict：两条错误
    print(validate_user({"name": "", "age": "x"}))
    # (False, ['name 必须是非空字符串', 'age 必须是 0~120 之间的整数'])

    # 自定义对象（鸭子类型）：通过
    print(validate_user(MyDict({"name": "Tom", "age": 18})))
    # (True, [])

    # 越界年龄：报错
    print(validate_user({"name": "Jerry", "age": 200}))
    # (False, ['age 必须是 0~120 之间的整数'])

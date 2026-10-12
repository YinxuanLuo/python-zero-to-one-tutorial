"""第五关 · 第 5 题：asyncio 并发任务

用 asyncio 写 run_all(tasks)，并发执行多个模拟耗时任务（sleep），
按"完成先后"返回结果。总耗时应明显小于所有任务串行之和。

运行：python a5-async-tasks.py
"""
import asyncio
import time


async def task(name, delay):
    """模拟一个耗时 I/O 任务（比如等网络响应）。"""
    await asyncio.sleep(delay)
    return f"{name}（睡 {delay}s）"


async def run_all(tasks):
    """并发执行多个协程，按完成顺序收集结果。"""
    results = []
    for coro in asyncio.as_completed(tasks):
        results.append(await coro)
    return results


async def main():
    start = time.time()

    results = await run_all([
        task("A", 0.3),
        task("B", 0.1),
        task("C", 0.2),
    ])

    elapsed = time.time() - start
    print(results)
    # 按完成顺序：B(0.1) -> C(0.2) -> A(0.3)
    print(f"总耗时 {elapsed:.2f}s（串行约需 0.6s）")
    assert elapsed < 0.5, "并发应明显快于串行"


if __name__ == "__main__":
    asyncio.run(main())

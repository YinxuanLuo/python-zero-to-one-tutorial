# 第 06 章配套示例：并发与异步
# 运行：python examples/06-并发.py
# 标准库零依赖，退出码 0
# 注意：Windows 下 multiprocessing 用 spawn，所以 CPU 密集任务、
#       进程入口函数必须是「模块顶层函数」，且顶层代码要放在
#       if __name__ == "__main__" 守卫里（否则子进程会重新导入本文件）。

import time
import threading
import multiprocessing
import asyncio
import concurrent.futures


def cpu_task(n):
    """CPU 密集任务：纯计算（平方累加），没有任何 I/O。"""
    total = 0
    for i in range(n):
        total += i * i
    return total


def square_worker(queue, x):
    """供 multiprocessing.Process 使用的顶层函数（必须可被 pickle）。"""
    queue.put(x * x)


N = 30_000_000  # 每跑一次约 1 秒，足够测出差异


def main():
    print("=== 6.5 GIL 实测：CPU 密集任务，线程 vs 进程 ===")

    start = time.perf_counter()
    for _ in range(4):
        cpu_task(N)
    serial = time.perf_counter() - start
    print(f"单线程串行跑 4 次 CPU 任务: {serial:.3f}s")

    def run_threads():
        threads = [threading.Thread(target=cpu_task, args=(N,)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    start = time.perf_counter()
    run_threads()
    threads_time = time.perf_counter() - start
    print(f"4 线程跑 4 次 CPU 任务:    {threads_time:.3f}s  ← 没变快（GIL 锁死）")

    start = time.perf_counter()
    with multiprocessing.Pool(processes=4) as pool:
        pool.map(cpu_task, [N] * 4)
    processes_time = time.perf_counter() - start
    print(f"4 进程跑 4 次 CPU 任务:    {processes_time:.3f}s  ← 真并行，明显变快")

    print()
    print("=== 6.4 I/O 密集：threading 并发等待 ===")

    def io_task(name, seconds):
        time.sleep(seconds)
        print(f"  {name} 完成")

    start = time.perf_counter()
    threads = [threading.Thread(target=io_task, args=(f"任务{i}", 1)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    io_time = time.perf_counter() - start
    print(f"4 个线程并发 sleep(1): {io_time:.3f}s（串行要 4s）")

    print()
    print("=== 6.6 multiprocessing：进程间通信 Queue ===")
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=square_worker, args=(q, 9))
    p.start()
    p.join()
    print("子进程通过 Queue 传回:", q.get())

    print()
    print("=== 6.8 asyncio 协程 ===")

    async def fetch(name, seconds):
        await asyncio.sleep(seconds)
        print(f"  {name} 完成")
        return f"{name}-result"

    async def async_main():
        results = await asyncio.gather(
            fetch("A", 1),
            fetch("B", 1),
            fetch("C", 1),
        )
        print("gather 返回:", results)

    start = time.perf_counter()
    asyncio.run(async_main())
    asyncio_time = time.perf_counter() - start
    print(f"asyncio 并发 3 个 sleep(1): {asyncio_time:.3f}s（串行要 3s）")

    print()
    print("=== 6.10 concurrent.futures ThreadPoolExecutor ===")

    def square(x):
        time.sleep(0.5)
        return x * x

    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(square, [1, 2, 3, 4]))
    print("ThreadPoolExecutor.map 结果:", results)
    print(f"4 个 sleep(0.5) 任务耗时: {time.perf_counter() - start:.3f}s")

    print("\n06 章示例全部跑完，退出码 0")


if __name__ == "__main__":
    main()

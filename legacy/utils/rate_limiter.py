import asyncio
import time
from collections import deque

class RateLimiter:
    def __init__(self, rate=1, per=2):
        """初始化速率限制器
        
        Args:
            rate (int): 允许的请求数
            per (float): 时间窗口(秒)
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self.tokens = deque()  # 用于记录请求时间戳
        
    async def wait(self):
        """等待令牌（兼容旧方法名）"""
        await self.acquire()
        
    async def acquire(self):
        """获取令牌，必要时等待"""
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        
        # 更新令牌数
        self.allowance += time_passed * (self.rate / self.per)
        if self.allowance > self.rate:
            self.allowance = self.rate
            
        # 清理过期的时间戳
        while self.tokens and current - self.tokens[0] > self.per:
            self.tokens.popleft()
            
        if self.allowance < 1:
            # 需要等待
            wait_time = (1 - self.allowance) * self.per / self.rate
            await asyncio.sleep(wait_time)
            self.allowance = 0
        else:
            self.allowance -= 1
            
        # 记录当前请求
        self.tokens.append(current)
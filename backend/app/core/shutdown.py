# app/core/shutdown.py

import signal
import sys
import asyncio
import threading
from typing import Callable, List
from app.core.logging import logger

class GracefulShutdown:
    def __init__(self):
        self.shutdown_handlers: List[Callable] = []
        self.is_shutting_down = False
        self.background_tasks: List[asyncio.Task] = []
        
        # 註冊信號處理器
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
    
    def add_shutdown_handler(self, handler: Callable):
        """添加退出時需要執行的處理器"""
        self.shutdown_handlers.append(handler)
    
    def _handle_signal(self, signum, frame):
        """處理終止信號"""
        if self.is_shutting_down:
            logger.warning("Forced shutdown initiated...")
            # 強制結束所有後台任務
            for task in self.background_tasks:
                task.cancel()
            sys.exit(1)
            
        logger.info(f"Received signal {signum}. Starting graceful shutdown...")
        self.is_shutting_down = True
        
        # 在新的事件循環中執行關閉處理
        if threading.current_thread() is threading.main_thread():
            asyncio.get_event_loop().create_task(self._run_shutdown_handlers())
        else:
            # 如果在子線程中,創建新的事件循環
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_shutdown_handlers())
    
    async def _run_shutdown_handlers(self):
        """運行所有退出處理器"""
        try:
            # 設置超時時間
            shutdown_timeout = 30  # 30秒超時
            
            # 創建所有處理器的任務
            tasks = []
            for handler in self.shutdown_handlers:
                if asyncio.iscoroutinefunction(handler):
                    task = asyncio.create_task(handler())
                else:
                    # 將同步處理器包裝為異步任務
                    task = asyncio.create_task(
                        asyncio.to_thread(handler)
                    )
                tasks.append(task)
            
            # 等待所有任務完成或超時
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks),
                    timeout=shutdown_timeout
                )
            except asyncio.TimeoutError:
                logger.error("Shutdown handlers timed out")
                # 取消未完成的任務
                for task in tasks:
                    if not task.done():
                        task.cancel()
            
            # 確保所有後台任務都已停止
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            logger.info("Graceful shutdown completed")
            
            # 強制退出進程
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            sys.exit(1)
    
    def register_background_task(self, task: asyncio.Task):
        """註冊後台任務以便在關閉時處理"""
        self.background_tasks.append(task)
    
    def remove_background_task(self, task: asyncio.Task):
        """移除已完成的後台任務"""
        if task in self.background_tasks:
            self.background_tasks.remove(task)

# 創建全局實例
graceful_shutdown = GracefulShutdown()
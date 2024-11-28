# app/core/queue.py

import asyncio
import json
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime, timedelta
import uuid

from redis import Redis
from redis.exceptions import RedisError
from app.core.config import settings
from app.core.logging import logger

class TaskQueue:
    """異步任務隊列管理器"""
    
    def __init__(self):
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.task_handlers: Dict[str, Callable] = {}
        self.queue_prefix = "tasks:"
        self.result_prefix = "results:"
        self.running = False
    
    def register_handler(self, task_type: str, handler: Callable):
        """註冊任務處理器"""
        self.task_handlers[task_type] = handler
    
    async def enqueue(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: int = 1,
        delay: Optional[int] = None
    ) -> str:
        """將任務加入隊列"""
        try:
            task_id = str(uuid.uuid4())
            task = {
                'id': task_id,
                'type': task_type,
                'payload': payload,
                'priority': priority,
                'created_at': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            # 使用優先級隊列
            queue_key = f"{self.queue_prefix}{priority}"
            
            if delay:
                # 延遲任務使用sorted set
                score = datetime.now().timestamp() + delay
                await self.redis.zadd(
                    f"{self.queue_prefix}delayed",
                    {json.dumps(task): score}
                )
            else:
                # 普通任務使用list
                await self.redis.lpush(queue_key, json.dumps(task))
            
            logger.info(f"Task {task_id} enqueued with priority {priority}")
            return task_id
            
        except RedisError as e:
            logger.error(f"Error enqueueing task: {e}")
            raise
    
    async def process_tasks(self):
        """處理任務隊列"""
        self.running = True
        logger.info("Task processor started")
        
        try:
            while self.running:
                # 首先處理延遲任務
                await self._process_delayed_tasks()
                
                # 按優先級順序處理任務
                for priority in range(1, 6):  # 1最高優先級,5最低優先級
                    queue_key = f"{self.queue_prefix}{priority}"
                    
                    # 使用阻塞彈出以減少CPU使用
                    task_data = await self.redis.brpop(
                        queue_key,
                        timeout=1
                    )
                    
                    if task_data:
                        await self._handle_task(json.loads(task_data[1]))
                        
                await asyncio.sleep(0.1)  # 避免CPU過載
                
        except Exception as e:
            logger.error(f"Error in task processor: {e}")
            raise
        finally:
            self.running = False
            
    async def _process_delayed_tasks(self):
        """處理延遲任務"""
        try:
            now = datetime.now().timestamp()
            delayed_key = f"{self.queue_prefix}delayed"
            
            # 獲取已到期的任務
            tasks = await self.redis.zrangebyscore(
                delayed_key,
                0,
                now
            )
            
            for task_data in tasks:
                task = json.loads(task_data)
                # 移到普通隊列
                queue_key = f"{self.queue_prefix}{task['priority']}"
                await self.redis.lpush(queue_key, task_data)
                # 從延遲隊列中移除
                await self.redis.zrem(delayed_key, task_data)
                
        except RedisError as e:
            logger.error(f"Error processing delayed tasks: {e}")
    
    async def _handle_task(self, task: Dict[str, Any]):
        """處理單個任務"""
        task_id = task['id']
        task_type = task['type']
        
        try:
            if task_type not in self.task_handlers:
                raise ValueError(f"No handler for task type: {task_type}")
            
            # 更新任務狀態
            await self._update_task_status(task_id, 'processing')
            
            # 執行任務
            handler = self.task_handlers[task_type]
            result = await handler(task['payload'])
            
            # 保存結果
            await self._save_task_result(task_id, result)
            await self._update_task_status(task_id, 'completed')
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            await self._update_task_status(task_id, 'failed', str(e))
            # 重試邏輯可以在這裡添加
    
    async def _update_task_status(
        self,
        task_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """更新任務狀態"""
        try:
            status_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            if error:
                status_data['error'] = error
                
            await self.redis.hset(
                f"{self.queue_prefix}status:{task_id}",
                mapping=status_data
            )
        except RedisError as e:
            logger.error(f"Error updating task status: {e}")
    
    async def _save_task_result(self, task_id: str, result: Any):
        """保存任務結果"""
        try:
            await self.redis.setex(
                f"{self.result_prefix}{task_id}",
                timedelta(hours=24),  # 結果保存24小時
                json.dumps(result)
            )
        except RedisError as e:
            logger.error(f"Error saving task result: {e}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """獲取任務狀態"""
        try:
            status_data = await self.redis.hgetall(
                f"{self.queue_prefix}status:{task_id}"
            )
            if not status_data:
                return {'status': 'unknown'}
            return status_data
        except RedisError as e:
            logger.error(f"Error getting task status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """獲取任務結果"""
        try:
            result = await self.redis.get(f"{self.result_prefix}{task_id}")
            return json.loads(result) if result else None
        except RedisError as e:
            logger.error(f"Error getting task result: {e}")
            return None
            
    def stop(self):
        """停止任務處理器"""
        self.running = False
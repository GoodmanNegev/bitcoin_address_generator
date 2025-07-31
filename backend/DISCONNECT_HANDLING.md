# 前端断联处理机制

## 功能概述

当前端与后端的WebSocket连接断开时，后端会自动停止计算任务并清除缓存，以节省系统资源和避免无用的计算。

## 实现机制

### 1. WebSocket断开检测

- **即时检测**: 在WebSocket的`except WebSocketDisconnect`块中捕获断开事件
- **周期性检测**: 每30秒运行一次后台清理任务，检查断开的连接
- **发送失败检测**: 在发送进度更新时，如果发送失败则认为连接已断开

### 2. 任务停止机制

#### 批处理任务停止
- 在每个批次处理前检查任务状态
- 在发送进度更新时检查连接状态
- 如果检测到断开，立即停止当前批次处理

#### 多进程任务停止
- 在多进程任务的监控循环中检查连接状态
- 使用`future.cancel()`取消正在运行的进程
- 设置超时机制强制终止无响应的进程

### 3. 缓存清理

```python
def clear_cache(self):
    """清除所有缓存的哈希对象以释放内存"""
    self._ripemd160_cache.clear()
    self._sha256_cache.clear()
    print("Generator cache cleared")
```

### 4. 任务管理

- **任务跟踪**: 每个WebSocket连接都有唯一的task_id
- **状态管理**: 跟踪任务的cancelled、paused状态
- **WebSocket引用**: 存储WebSocket对象用于连接状态检查
- **自动清理**: 定期清理已断开连接的任务

## 关键代码位置

### WebSocket处理 (main.py:129-226)
```python
@app.websocket("/ws/generate")
async def websocket_generate(websocket: WebSocket):
    # ... 连接处理逻辑
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for task {task_id}")
        # 停止计算并清除缓存
        if task_id and task_id in active_tasks:
            active_tasks[task_id]["cancelled"] = True
        if generation_task and not generation_task.done():
            generation_task.cancel()
        generator.clear_cache()
```

### 批处理任务检查 (main.py:329-378)
```python
# 检查任务是否被取消或WebSocket是否断开
if (task_id not in active_tasks or 
    active_tasks[task_id]["cancelled"] or
    not hasattr(active_tasks[task_id].get("websocket"), "client_state")):
    print(f"Stopping batch processing for task {task_id}")
    break
```

### 多进程任务检查 (main.py:258-310)
```python
# 检查任务是否被取消或WebSocket是否断开
if (task_id not in active_tasks or 
    active_tasks[task_id]["cancelled"] or
    not hasattr(active_tasks[task_id].get("websocket"), "client_state")):
    print(f"Cancelling multiprocess task {task_id}")
    future.cancel()
    return
```

### 定期清理任务 (main.py:402-408)
```python
async def periodic_cleanup():
    """定期清理断开连接的任务"""
    while True:
        await asyncio.sleep(30)  # 每30秒检查一次
        cleanup_disconnected_tasks()
```

## 测试验证

使用`test_disconnect.py`脚本可以验证断联处理功能:

```bash
python test_disconnect.py
```

测试流程:
1. 连接到WebSocket服务器
2. 发送生成请求开始计算任务
3. 接收几条进度消息
4. 主动断开连接
5. 观察后端日志确认清理操作

## 预期行为

当前端断开连接时，后端应该:
1. 立即检测到WebSocket断开
2. 标记相关任务为已取消
3. 停止正在进行的计算
4. 清除生成器缓存
5. 清理任务记录
6. 在日志中输出相应信息

## 日志示例

```
WebSocket disconnected for task task_0
Marked task task_0 as cancelled due to disconnect
Cancelled generation task for task_0
Generator cache cleared
Cleaned up task task_0
```

这确保了即使前端意外断开连接，后端也不会继续进行无用的计算，有效节省了系统资源。
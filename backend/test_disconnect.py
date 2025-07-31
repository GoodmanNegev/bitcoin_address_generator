#!/usr/bin/env python3
"""
测试前端断联时后端的行为
"""

import asyncio
import websockets
import json
import time

async def test_disconnect_behavior():
    """测试WebSocket断开连接时的行为"""
    uri = "ws://localhost:8000/ws/generate"
    
    try:
        print("连接到WebSocket服务器...")
        async with websockets.connect(uri) as websocket:
            print("连接成功！")
            
            # 发送开始生成请求
            request = {
                "action": "start",
                "address_type": "p2pkh",
                "pattern": "abc",  # 使用一个需要一些时间的模式
                "position": "start"
            }
            
            print(f"发送生成请求: {request}")
            await websocket.send(json.dumps(request))
            
            # 接收几条消息
            message_count = 0
            while message_count < 3:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"收到消息 {message_count + 1}: {data['type']} - {data.get('message', data.get('attempts', 'N/A'))}")
                    message_count += 1
                    
                    if data['type'] == 'success':
                        print("生成成功，提前结束测试")
                        break
                        
                except asyncio.TimeoutError:
                    print("等待消息超时")
                    break
            
            print("\n模拟前端断开连接...")
            # 直接关闭连接，模拟前端断联
            
    except Exception as e:
        print(f"连接错误: {e}")
    
    print("连接已断开，等待后端清理...")
    await asyncio.sleep(5)  # 等待后端检测到断开并清理
    print("测试完成")

if __name__ == "__main__":
    print("=== 前端断联测试 ===")
    print("此测试将连接到后端，开始生成任务，然后断开连接")
    print("检查后端是否正确停止计算并清理缓存\n")
    
    asyncio.run(test_disconnect_behavior())
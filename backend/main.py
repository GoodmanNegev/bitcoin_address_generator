from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import uvicorn
import json
# Try to import the full version first, fall back to simple version
try:
    from btc_generator import BitcoinAddressGenerator
except ImportError:
    from btc_generator_simple import BitcoinAddressGenerator
    print("Using simplified Bitcoin address generator (educational version)")

app = FastAPI(title="Bitcoin Address Generator", description="Educational Bitcoin address generator")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerationRequest(BaseModel):
    address_type: str  # "p2pkh", "p2sh-p2wpkh", "p2wpkh", "p2tr"
    pattern: str = ""
    position: str = "start"  # "start", "middle", "end"

class GenerationResponse(BaseModel):
    address: str
    private_key: str
    attempts: int
    success: bool

# Store active generation tasks
active_tasks: Dict[str, Dict[str, Any]] = {}

generator = BitcoinAddressGenerator()

# Task cleanup function
def cleanup_disconnected_tasks():
    """Clean up tasks for disconnected clients"""
    tasks_to_remove = []
    for task_id, task_info in active_tasks.items():
        websocket = task_info.get("websocket")
        if websocket and not hasattr(websocket, "client_state"):
            tasks_to_remove.append(task_id)
    
    for task_id in tasks_to_remove:
        active_tasks[task_id]["cancelled"] = True
        del active_tasks[task_id]
        print(f"Cleaned up disconnected task: {task_id}")
    
    if tasks_to_remove:
        generator.clear_cache()
        print(f"Cleaned up {len(tasks_to_remove)} disconnected tasks")

@app.get("/")
async def root():
    return {"message": "Bitcoin Address Generator API"}

@app.get("/address-types")
async def get_address_types():
    return {
        "types": [
            {"value": "p2pkh", "label": "传统地址 (P2PKH)", "description": "以 '1' 开头的传统比特币地址"},
            {"value": "p2sh-p2wpkh", "label": "嵌套隔离见证 (P2SH-P2WPKH)", "description": "P2SH包装的隔离见证地址，以 '3' 开头"},
            {"value": "p2wpkh", "label": "原生隔离见证 (P2WPKH)", "description": "原生隔离见证地址，以 'bc1q' 开头"},
            {"value": "p2tr", "label": "Taproot (P2TR)", "description": "最新的Taproot地址，以 'bc1p' 开头"}
        ]
    }

@app.post("/generate")
async def generate_single_address(request: GenerationRequest):
    """Generate a single address without pattern matching"""
    try:
        address, private_key = generator.generate_address(request.address_type)
        return GenerationResponse(
            address=address,
            private_key=private_key,
            attempts=1,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-batch")
async def generate_batch_addresses(request: GenerationRequest, batch_size: int = 10):
    """Generate multiple addresses in batch for better performance"""
    try:
        if batch_size > 100:
            raise HTTPException(status_code=400, detail="批量大小不能超过100")
        
        batch = generator.generate_batch(request.address_type, batch_size)
        return {
            "addresses": [
                {
                    "address": addr,
                    "private_key": pk
                } for addr, pk in batch
            ],
            "count": len(batch),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/find-pattern")
async def find_pattern_address(request: GenerationRequest, max_attempts: int = None):
    """Find address matching pattern using optimized methods"""
    try:
        if not request.pattern:
            raise HTTPException(status_code=400, detail="需要提供搜索模式")
        
        # Use appropriate method based on pattern complexity
        if len(request.pattern) >= 4:
            result = generator.find_pattern_multiprocess(
                request.address_type, request.pattern, request.position, max_attempts
            )
        else:
            result = generator.find_pattern_batch(
                request.address_type, request.pattern, request.position, 1000, max_attempts
            )
        
        if result:
            address, private_key, attempts = result
            return GenerationResponse(
                address=address,
                private_key=private_key,
                attempts=attempts,
                success=True
            )
        else:
            return GenerationResponse(
                address="",
                private_key="",
                attempts=max_attempts if max_attempts else 0,
                success=False
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/ws/generate")
async def websocket_generate(websocket: WebSocket):
    await websocket.accept()
    task_id = None
    generation_task = None
    
    try:
        while True:
            # Receive generation request
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            if request_data.get("action") == "start":
                # Start new generation task
                if task_id and task_id in active_tasks:
                    active_tasks[task_id]["cancelled"] = True
                    # Cancel previous generation task if exists
                    if generation_task and not generation_task.done():
                        generation_task.cancel()
                
                task_id = f"task_{len(active_tasks)}"
                active_tasks[task_id] = {
                    "cancelled": False,
                    "paused": False,
                    "websocket": websocket  # Store websocket reference for cleanup
                }
                
                # Start generation in background
                generation_task = asyncio.create_task(
                    generate_with_pattern(
                        websocket, 
                        task_id,
                        request_data["address_type"],
                        request_data.get("pattern", ""),
                        request_data.get("position", "start")
                    )
                )
                
            elif request_data.get("action") == "pause":
                if task_id and task_id in active_tasks:
                    active_tasks[task_id]["paused"] = True
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "message": "生成已暂停"
                    }))
                    
            elif request_data.get("action") == "resume":
                if task_id and task_id in active_tasks:
                    active_tasks[task_id]["paused"] = False
                    await websocket.send_text(json.dumps({
                        "type": "status", 
                        "message": "生成已恢复"
                    }))
                    
            elif request_data.get("action") == "stop":
                if task_id and task_id in active_tasks:
                    active_tasks[task_id]["cancelled"] = True
                    # Cancel generation task
                    if generation_task and not generation_task.done():
                        generation_task.cancel()
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "message": "生成已停止"
                    }))
                    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for task {task_id}")
        # Frontend disconnected, stop computation and clear cache
        if task_id and task_id in active_tasks:
            active_tasks[task_id]["cancelled"] = True
            print(f"Marked task {task_id} as cancelled due to disconnect")
        
        # Cancel the generation task
        if generation_task and not generation_task.done():
            generation_task.cancel()
            print(f"Cancelled generation task for {task_id}")
        
        # Clear generator cache to free memory
        generator.clear_cache()
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        # Handle other exceptions similarly
        if task_id and task_id in active_tasks:
            active_tasks[task_id]["cancelled"] = True
        if generation_task and not generation_task.done():
            generation_task.cancel()
    
    finally:
        # Cleanup when websocket closes
        if task_id and task_id in active_tasks:
            del active_tasks[task_id]
            print(f"Cleaned up task {task_id}")

async def generate_with_pattern(websocket: WebSocket, task_id: str, address_type: str, pattern: str, position: str):
    """Generate addresses until pattern is found - optimized version"""
    max_attempts = None  # No limit on attempts
    batch_size = 1000  # Process in batches for better performance
    
    try:
        # If no pattern, just generate one address quickly
        if not pattern:
            address, private_key = generator.generate_address(address_type)
            await websocket.send_text(json.dumps({
                "type": "success",
                "address": address,
                "private_key": private_key,
                "attempts": 1
            }))
            return
        
        # Use multiprocess for complex patterns
        if len(pattern) >= 4:  # For longer patterns, use multiprocessing
            await websocket.send_text(json.dumps({
                "type": "info",
                "message": "使用多进程加速生成..."
            }))
            
            # Run multiprocess search in executor to avoid blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    generator.find_pattern_multiprocess,
                    address_type, pattern, position, max_attempts
                )
                
                # Check periodically for cancellation and send progress
                attempts_checked = 0
                while not future.done():
                    # Check if task is cancelled or websocket is disconnected
                    if (task_id not in active_tasks or 
                        active_tasks[task_id]["cancelled"] or
                        not hasattr(active_tasks[task_id].get("websocket"), "client_state")):
                        
                        print(f"Cancelling multiprocess task {task_id}")
                        future.cancel()
                        # Force terminate if cancel doesn't work immediately
                        try:
                            future.result(timeout=1.0)
                        except (concurrent.futures.TimeoutError, concurrent.futures.CancelledError):
                            print(f"Task {task_id} cancelled or timed out")
                        return
                    
                    attempts_checked += 1000  # Estimate
                    if attempts_checked % 5000 == 0:
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "progress",
                                "attempts": attempts_checked,
                                "current_address": "多进程搜索中..."
                            }))
                        except Exception as e:
                            print(f"Failed to send progress update: {e}")
                            # WebSocket might be closed, cancel the task
                            future.cancel()
                            return
                    
                    await asyncio.sleep(0.5)
                
                try:
                    result = future.result(timeout=1.0)
                    if result:
                        address, private_key, attempts = result
                        await websocket.send_text(json.dumps({
                            "type": "success",
                            "address": address,
                            "private_key": private_key,
                            "attempts": attempts
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "info",
                            "message": "搜索已停止或被取消。"
                        }))
                except (concurrent.futures.CancelledError, concurrent.futures.TimeoutError):
                    print(f"Multiprocess task {task_id} was cancelled or timed out")
                except Exception as e:
                    print(f"Error in multiprocess task {task_id}: {e}")
        else:
            # Use batch processing for shorter patterns
            attempts = 0
            while True:  # Continue indefinitely until pattern is found or cancelled
                # Check if task is cancelled or websocket is disconnected
                if (task_id not in active_tasks or 
                    active_tasks[task_id]["cancelled"] or
                    not hasattr(active_tasks[task_id].get("websocket"), "client_state")):
                    print(f"Stopping batch processing for task {task_id}")
                    break
                
                # Check if task is paused
                if active_tasks[task_id]["paused"]:
                    await asyncio.sleep(0.1)
                    continue
                
                # Generate batch of addresses
                try:
                    batch = generator.generate_batch(address_type, batch_size)
                except Exception as e:
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"生成错误: {str(e)}"
                        }))
                    except Exception:
                        print(f"Failed to send error message for task {task_id}")
                    break
                
                # Check each address in batch
                for address, private_key in batch:
                    attempts += 1
                    
                    # Check if cancelled during batch processing
                    if (task_id not in active_tasks or 
                        active_tasks[task_id]["cancelled"]):
                        print(f"Task {task_id} cancelled during batch processing")
                        return
                    
                    # Send progress update
                    if attempts % 500 == 0 or attempts == 1:
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "progress",
                                "attempts": attempts,
                                "current_address": address
                            }))
                        except Exception as e:
                            print(f"Failed to send progress update for task {task_id}: {e}")
                            # WebSocket might be closed, stop processing
                            return
                    
                    # Check pattern match
                    if generator.check_pattern_match(address, pattern, position):
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "success",
                                "address": address,
                                "private_key": private_key,
                                "attempts": attempts
                            }))
                        except Exception as e:
                            print(f"Failed to send success message for task {task_id}: {e}")
                        return
                
                # Small delay to prevent blocking
                await asyncio.sleep(0.01)
            
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"意外错误: {str(e)}"
        }))
    finally:
        # Clean up task
        if task_id in active_tasks:
            del active_tasks[task_id]

# Background task for periodic cleanup
async def periodic_cleanup():
    """Periodically clean up disconnected tasks"""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        cleanup_disconnected_tasks()

# Start background cleanup task when app starts
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_cleanup())
    print("Started periodic cleanup task")

@app.on_event("shutdown")
async def shutdown_event():
    # Cancel all active tasks
    for task_id in list(active_tasks.keys()):
        active_tasks[task_id]["cancelled"] = True
    active_tasks.clear()
    generator.clear_cache()
    print("Cleaned up all tasks on shutdown")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
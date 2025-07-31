#!/usr/bin/env python3
"""
性能测试脚本 - 比较优化前后的生成速度
"""

import time
import statistics
from btc_generator import BitcoinAddressGenerator

def test_single_generation(generator, address_type, iterations=1000):
    """测试单个地址生成性能"""
    times = []
    
    for _ in range(iterations):
        start_time = time.time()
        generator.generate_address(address_type)
        end_time = time.time()
        times.append(end_time - start_time)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times),
        'total': sum(times)
    }

def test_batch_generation(generator, address_type, batch_size=100, iterations=10):
    """测试批量地址生成性能"""
    times = []
    
    for _ in range(iterations):
        start_time = time.time()
        generator.generate_batch(address_type, batch_size)
        end_time = time.time()
        times.append(end_time - start_time)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times),
        'total': sum(times),
        'addresses_per_second': (batch_size * iterations) / sum(times)
    }

def test_pattern_finding(generator, address_type, pattern, position, max_attempts=10000):
    """测试模式匹配性能"""
    print(f"\n测试模式匹配: {pattern} (位置: {position})")
    
    # 测试批量方法
    start_time = time.time()
    result_batch = generator.find_pattern_batch(address_type, pattern, position, 1000, max_attempts)
    batch_time = time.time() - start_time
    
    # 测试多进程方法
    start_time = time.time()
    result_multiprocess = generator.find_pattern_multiprocess(address_type, pattern, position, max_attempts)
    multiprocess_time = time.time() - start_time
    
    return {
        'batch': {
            'time': batch_time,
            'found': result_batch is not None,
            'attempts': result_batch[2] if result_batch else max_attempts
        },
        'multiprocess': {
            'time': multiprocess_time,
            'found': result_multiprocess is not None,
            'attempts': result_multiprocess[2] if result_multiprocess else max_attempts
        }
    }

def main():
    print("=== Bitcoin地址生成器性能测试 ===")
    print("正在初始化生成器...")
    
    generator = BitcoinAddressGenerator()
    address_types = ['p2pkh', 'p2wpkh', 'p2sh-p2wpkh', 'p2tr']
    
    # 测试单个地址生成
    print("\n1. 单个地址生成性能测试 (1000次)")
    print("-" * 50)
    for addr_type in address_types:
        print(f"\n测试 {addr_type}:")
        stats = test_single_generation(generator, addr_type, 1000)
        print(f"  平均时间: {stats['mean']*1000:.2f}ms")
        print(f"  中位数时间: {stats['median']*1000:.2f}ms")
        print(f"  最快: {stats['min']*1000:.2f}ms")
        print(f"  最慢: {stats['max']*1000:.2f}ms")
        print(f"  总时间: {stats['total']:.2f}s")
        print(f"  每秒生成: {1000/stats['total']:.1f} 个地址")
    
    # 测试批量生成
    print("\n\n2. 批量地址生成性能测试 (100个地址 x 10批次)")
    print("-" * 50)
    for addr_type in address_types:
        print(f"\n测试 {addr_type}:")
        stats = test_batch_generation(generator, addr_type, 100, 10)
        print(f"  平均批次时间: {stats['mean']:.3f}s")
        print(f"  每秒生成: {stats['addresses_per_second']:.1f} 个地址")
        print(f"  总时间: {stats['total']:.2f}s")
    
    # 测试模式匹配
    print("\n\n3. 模式匹配性能测试")
    print("-" * 50)
    
    test_patterns = [
        ('abc', 'start'),
        ('123', 'start'),
        ('00', 'end')
    ]
    
    for pattern, position in test_patterns:
        for addr_type in ['p2pkh', 'p2wpkh']:
            print(f"\n测试 {addr_type} - 模式: '{pattern}' (位置: {position})")
            try:
                results = test_pattern_finding(generator, addr_type, pattern, position, 5000)
                
                print(f"  批量方法:")
                print(f"    时间: {results['batch']['time']:.2f}s")
                print(f"    找到: {results['batch']['found']}")
                print(f"    尝试次数: {results['batch']['attempts']}")
                if results['batch']['found']:
                    print(f"    每秒尝试: {results['batch']['attempts']/results['batch']['time']:.0f}")
                
                print(f"  多进程方法:")
                print(f"    时间: {results['multiprocess']['time']:.2f}s")
                print(f"    找到: {results['multiprocess']['found']}")
                print(f"    尝试次数: {results['multiprocess']['attempts']}")
                if results['multiprocess']['found']:
                    print(f"    每秒尝试: {results['multiprocess']['attempts']/results['multiprocess']['time']:.0f}")
                
                if results['batch']['found'] and results['multiprocess']['found']:
                    speedup = results['batch']['time'] / results['multiprocess']['time']
                    print(f"  多进程加速比: {speedup:.1f}x")
                    
            except Exception as e:
                print(f"  测试失败: {e}")
    
    print("\n=== 性能测试完成 ===")
    print("\n优化建议:")
    print("- 对于单个地址生成，使用标准方法")
    print("- 对于大量地址生成，使用批量方法")
    print("- 对于复杂模式匹配（4+字符），使用多进程方法")
    print("- 对于简单模式匹配（<4字符），使用批量方法")

if __name__ == "__main__":
    main()
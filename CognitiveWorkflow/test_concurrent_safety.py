#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发安全性测试

测试多个工作流引擎同时运行时，ID生成和文件保存的安全性。
"""

import sys
import os
import threading
import time
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cognitive_workflow_rule_base.utils.concurrent_safe_id_generator import (
    ConcurrentSafeIdGenerator, SafeFileOperations, id_generator
)
from cognitive_workflow_rule_base.domain.entities import GlobalState
from cognitive_workflow_rule_base.infrastructure.repository_impl import StateRepositoryImpl
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_concurrent_id_generation():
    """测试并发ID生成的唯一性"""
    print("\n" + "="*60)
    print("🔬 测试并发ID生成的唯一性")
    print("="*60)
    
    generated_ids = set()
    lock = threading.Lock()
    error_count = 0
    
    def generate_workflow_id(thread_id):
        """在单个线程中生成工作流ID"""
        nonlocal error_count
        try:
            goal = f"并发测试目标_{thread_id}"
            workflow_id = id_generator.generate_workflow_id(goal)
            
            with lock:
                if workflow_id in generated_ids:
                    print(f"❌ 检测到重复ID: {workflow_id} (线程 {thread_id})")
                    error_count += 1
                    return False
                else:
                    generated_ids.add(workflow_id)
                    print(f"✅ 线程 {thread_id}: {workflow_id}")
                    return True
        except Exception as e:
            print(f"❌ 线程 {thread_id} 生成ID失败: {e}")
            error_count += 1
            return False
    
    # 使用多线程并发生成ID
    num_threads = 20
    num_ids_per_thread = 5
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        
        for thread_id in range(num_threads):
            for i in range(num_ids_per_thread):
                future = executor.submit(generate_workflow_id, f"{thread_id}_{i}")
                futures.append(future)
        
        # 等待所有任务完成
        success_count = 0
        for future in as_completed(futures):
            if future.result():
                success_count += 1
    
    total_expected = num_threads * num_ids_per_thread
    print(f"\n📊 ID生成结果:")
    print(f"   预期生成: {total_expected} 个")
    print(f"   成功生成: {success_count} 个")
    print(f"   唯一ID数: {len(generated_ids)} 个")
    print(f"   错误次数: {error_count} 次")
    
    # 验证所有ID都是唯一的
    assert len(generated_ids) == success_count, f"ID唯一性检查失败: {len(generated_ids)} != {success_count}"
    assert error_count == 0, f"存在 {error_count} 个错误"
    
    print(f"✅ 并发ID生成测试通过!")
    
    # 清理生成的ID
    for workflow_id in generated_ids:
        try:
            id_generator.release_workflow_id(workflow_id)
        except Exception:
            pass

def test_atomic_file_operations():
    """测试原子性文件操作"""
    print("\n" + "="*60) 
    print("🔬 测试原子性文件操作")
    print("="*60)
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        write_errors = []
        read_errors = []
        
        def concurrent_write(thread_id):
            """并发写入同一个文件"""
            try:
                file_path = temp_path / "concurrent_test.json"
                test_data = {
                    'thread_id': thread_id,
                    'timestamp': time.time(),
                    'data': [i for i in range(100)]  # 一些测试数据
                }
                
                # 使用原子性写入
                success = SafeFileOperations.atomic_write_json(file_path, test_data)
                if not success:
                    write_errors.append(f"线程 {thread_id} 写入失败")
                    return False
                
                print(f"✅ 线程 {thread_id} 写入成功")
                return True
                
            except Exception as e:
                write_errors.append(f"线程 {thread_id} 异常: {e}")
                return False
        
        def concurrent_read(thread_id):
            """并发读取文件"""
            try:
                file_path = temp_path / "concurrent_test.json"
                
                # 等待文件存在
                max_wait = 50  # 最多等待5秒
                for _ in range(max_wait):
                    if file_path.exists():
                        break
                    time.sleep(0.1)
                else:
                    read_errors.append(f"线程 {thread_id} 文件等待超时")
                    return False
                
                # 使用安全读取
                data = SafeFileOperations.safe_read_json(file_path)
                if data is None:
                    read_errors.append(f"线程 {thread_id} 读取失败")
                    return False
                
                # 验证数据完整性
                if 'thread_id' not in data or 'data' not in data:
                    read_errors.append(f"线程 {thread_id} 数据不完整")
                    return False
                
                print(f"✅ 线程 {thread_id} 读取成功: thread_id={data['thread_id']}")
                return True
                
            except Exception as e:
                read_errors.append(f"线程 {thread_id} 读取异常: {e}")
                return False
        
        # 启动并发写入和读取
        num_writers = 10
        num_readers = 15
        
        with ThreadPoolExecutor(max_workers=num_writers + num_readers) as executor:
            # 提交写入任务
            write_futures = []
            for i in range(num_writers):
                future = executor.submit(concurrent_write, f"writer_{i}")
                write_futures.append(future)
            
            # 稍微延迟后提交读取任务
            time.sleep(0.1)
            read_futures = []
            for i in range(num_readers):
                future = executor.submit(concurrent_read, f"reader_{i}")
                read_futures.append(future)
            
            # 等待所有任务完成
            write_success = sum(1 for future in as_completed(write_futures) if future.result())
            read_success = sum(1 for future in as_completed(read_futures) if future.result())
        
        print(f"\n📊 文件操作结果:")
        print(f"   写入成功: {write_success}/{num_writers}")
        print(f"   读取成功: {read_success}/{num_readers}")
        print(f"   写入错误: {len(write_errors)}")
        print(f"   读取错误: {len(read_errors)}")
        
        if write_errors:
            print(f"   写入错误详情: {write_errors[:3]}")
        if read_errors:
            print(f"   读取错误详情: {read_errors[:3]}")
        
        # 验证至少有一些成功的操作
        assert write_success > 0, "没有成功的写入操作"
        assert read_success > 0, "没有成功的读取操作"
        assert len(write_errors) < num_writers, "所有写入都失败了"
        
        print(f"✅ 原子性文件操作测试通过!")

def test_concurrent_state_repository():
    """测试并发状态仓储操作"""
    print("\n" + "="*60)
    print("🔬 测试并发状态仓储操作")
    print("="*60)
    
    # 创建临时存储路径
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = os.path.join(temp_dir, "states")
        repo = StateRepositoryImpl(storage_path)
        
        save_errors = []
        load_errors = []
        saved_states = []
        lock = threading.Lock()
        
        def concurrent_save_state(thread_id):
            """并发保存状态"""
            try:
                # 生成唯一的工作流ID和状态
                workflow_id = id_generator.generate_workflow_id(f"concurrent_test_{thread_id}")
                state_id = id_generator.generate_state_id(workflow_id, 0)
                
                global_state = GlobalState(
                    id=state_id,
                    state=f"并发测试状态_{thread_id}",
                    workflow_id=workflow_id,
                    iteration_count=0,
                    context_variables={'thread_id': thread_id, 'test_data': list(range(10))}
                )
                
                # 保存状态
                repo.save_state(global_state)
                
                with lock:
                    saved_states.append((workflow_id, state_id))
                
                print(f"✅ 线程 {thread_id} 状态保存成功: {state_id}")
                return True
                
            except Exception as e:
                save_errors.append(f"线程 {thread_id} 保存失败: {e}")
                print(f"❌ 线程 {thread_id} 保存失败: {e}")
                return False
        
        def concurrent_load_state(state_info):
            """并发加载状态"""
            workflow_id, state_id = state_info
            try:
                # 加载状态
                loaded_state = repo.load_state(state_id)
                
                # 验证数据完整性
                if loaded_state.id != state_id:
                    load_errors.append(f"状态ID不匹配: {loaded_state.id} != {state_id}")
                    return False
                
                if loaded_state.workflow_id != workflow_id:
                    load_errors.append(f"工作流ID不匹配: {loaded_state.workflow_id} != {workflow_id}")
                    return False
                
                print(f"✅ 状态加载成功: {state_id}")
                return True
                
            except Exception as e:
                load_errors.append(f"加载状态 {state_id} 失败: {e}")
                print(f"❌ 加载状态 {state_id} 失败: {e}")
                return False
        
        # 第一阶段：并发保存状态
        num_save_threads = 15
        
        with ThreadPoolExecutor(max_workers=num_save_threads) as executor:
            save_futures = []
            for i in range(num_save_threads):
                future = executor.submit(concurrent_save_state, i)
                save_futures.append(future)
            
            save_success = sum(1 for future in as_completed(save_futures) if future.result())
        
        # 第二阶段：并发加载状态
        with ThreadPoolExecutor(max_workers=len(saved_states)) as executor:
            load_futures = []
            for state_info in saved_states:
                future = executor.submit(concurrent_load_state, state_info)
                load_futures.append(future)
            
            load_success = sum(1 for future in as_completed(load_futures) if future.result())
        
        print(f"\n📊 状态仓储操作结果:")
        print(f"   保存成功: {save_success}/{num_save_threads}")
        print(f"   加载成功: {load_success}/{len(saved_states)}")
        print(f"   保存错误: {len(save_errors)}")
        print(f"   加载错误: {len(load_errors)}")
        
        if save_errors:
            print(f"   保存错误详情: {save_errors[:3]}")
        if load_errors:
            print(f"   加载错误详情: {load_errors[:3]}")
        
        # 验证结果
        assert save_success > 0, "没有成功保存的状态"
        assert load_success == len(saved_states), f"加载成功率不符合预期: {load_success} != {len(saved_states)}"
        
        print(f"✅ 并发状态仓储操作测试通过!")
        
        # 清理工作流ID
        for workflow_id, _ in saved_states:
            try:
                id_generator.release_workflow_id(workflow_id)
            except Exception:
                pass

def test_real_world_scenario():
    """模拟真实世界场景：多个工作流引擎同时启动相同目标"""
    print("\n" + "="*60)
    print("🔬 模拟真实场景：多工作流引擎同时启动")
    print("="*60)
    
    # 模拟多个工作流引擎同时处理相同的目标
    same_goal = "处理用户请求数据分析"
    num_engines = 8
    results = []
    errors = []
    
    def simulate_workflow_engine(engine_id):
        """模拟单个工作流引擎的启动"""
        try:
            # 1. 生成工作流ID
            workflow_id = id_generator.generate_workflow_id(same_goal)
            
            # 2. 生成规则集ID
            rule_set_id = id_generator.generate_rule_set_id(same_goal)
            
            # 3. 生成多个状态ID
            state_ids = []
            for i in range(3):
                state_id = id_generator.generate_state_id(workflow_id, i)
                state_ids.append(state_id)
            
            # 4. 生成执行ID
            execution_ids = []
            for i in range(2):
                exec_id = id_generator.generate_execution_id(f"rule_{i}")
                execution_ids.append(exec_id)
            
            result = {
                'engine_id': engine_id,
                'workflow_id': workflow_id,
                'rule_set_id': rule_set_id,
                'state_ids': state_ids,
                'execution_ids': execution_ids
            }
            
            print(f"✅ 引擎 {engine_id}: {workflow_id}")
            results.append(result)
            
            # 模拟工作流完成
            time.sleep(0.1)
            id_generator.release_workflow_id(workflow_id)
            
            return True
            
        except Exception as e:
            error_msg = f"引擎 {engine_id} 失败: {e}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    # 并发启动多个工作流引擎
    with ThreadPoolExecutor(max_workers=num_engines) as executor:
        futures = []
        for engine_id in range(num_engines):
            future = executor.submit(simulate_workflow_engine, engine_id)
            futures.append(future)
        
        success_count = sum(1 for future in as_completed(futures) if future.result())
    
    # 验证所有ID的唯一性
    all_workflow_ids = {r['workflow_id'] for r in results}
    all_rule_set_ids = {r['rule_set_id'] for r in results}
    all_state_ids = {sid for r in results for sid in r['state_ids']}
    all_execution_ids = {eid for r in results for eid in r['execution_ids']}
    
    print(f"\n📊 真实场景模拟结果:")
    print(f"   成功引擎: {success_count}/{num_engines}")
    print(f"   失败次数: {len(errors)}")
    print(f"   唯一工作流ID: {len(all_workflow_ids)}")
    print(f"   唯一规则集ID: {len(all_rule_set_ids)}")
    print(f"   唯一状态ID: {len(all_state_ids)}")
    print(f"   唯一执行ID: {len(all_execution_ids)}")
    
    if errors:
        print(f"   错误详情: {errors}")
    
    # 验证唯一性
    expected_workflow_ids = success_count
    expected_rule_set_ids = success_count
    expected_state_ids = success_count * 3
    expected_execution_ids = success_count * 2
    
    assert len(all_workflow_ids) == expected_workflow_ids, f"工作流ID不唯一: {len(all_workflow_ids)} != {expected_workflow_ids}"
    assert len(all_rule_set_ids) == expected_rule_set_ids, f"规则集ID不唯一: {len(all_rule_set_ids)} != {expected_rule_set_ids}"
    assert len(all_state_ids) == expected_state_ids, f"状态ID不唯一: {len(all_state_ids)} != {expected_state_ids}"
    assert len(all_execution_ids) == expected_execution_ids, f"执行ID不唯一: {len(all_execution_ids)} != {expected_execution_ids}"
    
    print(f"✅ 真实场景模拟测试通过!")

def main():
    """运行所有并发安全测试"""
    print("🚀 开始并发安全性测试")
    print("="*80)
    
    try:
        test_concurrent_id_generation()
        test_atomic_file_operations()
        test_concurrent_state_repository()
        test_real_world_scenario()
        
        print("\n" + "="*80)
        print("🎉 所有并发安全测试通过！")
        print("="*80)
        
        print("\n📋 并发安全特性验证:")
        print("✅ 唯一ID生成机制工作正常")
        print("✅ 原子性文件操作防止数据损坏")
        print("✅ 状态仓储并发访问安全")
        print("✅ 多工作流引擎可以安全并发运行")
        print("\n🔧 多个工作流引擎同时运行不会再出现JSON文件互相覆盖的问题！")
        
    except Exception as e:
        print(f"\n❌ 并发安全测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
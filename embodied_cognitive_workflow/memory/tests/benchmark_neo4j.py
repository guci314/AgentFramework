"""
Neo4j语义记忆性能基准测试

运行各种性能测试并生成报告
"""

import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np

from ..semantic_memory_neo4j import Neo4jSemanticMemory
from ..neo4j_config import Neo4jConfig
from ..interfaces import Concept
from ..utils import generate_memory_id


class Neo4jBenchmark:
    """Neo4j性能基准测试类"""
    
    def __init__(self, config: Neo4jConfig = None):
        """初始化基准测试"""
        self.config = config or Neo4jConfig(
            database="benchmark",
            create_indexes=True
        )
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
    
    def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("Neo4j语义记忆性能基准测试")
        print("=" * 50)
        
        # 测试列表
        benchmarks = [
            ("插入性能", self.benchmark_insert),
            ("搜索性能", self.benchmark_search),
            ("图遍历性能", self.benchmark_graph_traversal),
            ("并发性能", self.benchmark_concurrency),
            ("大规模数据", self.benchmark_large_scale),
            ("复杂查询", self.benchmark_complex_queries)
        ]
        
        for name, benchmark_func in benchmarks:
            print(f"\n运行测试: {name}")
            print("-" * 30)
            try:
                result = benchmark_func()
                self.results['tests'][name] = result
            except Exception as e:
                print(f"测试失败: {e}")
                self.results['tests'][name] = {'error': str(e)}
        
        # 生成报告
        self.generate_report()
    
    def benchmark_insert(self) -> Dict[str, Any]:
        """测试插入性能"""
        memory = Neo4jSemanticMemory(self.config)
        memory.clear()
        
        # 不同批量大小的测试
        batch_sizes = [10, 50, 100, 500, 1000]
        results = []
        
        for batch_size in batch_sizes:
            concepts = []
            for i in range(batch_size):
                concept = Concept(
                    id="",
                    name=f"Benchmark Concept {i}",
                    category=f"category_{i % 10}",
                    attributes={
                        'index': i,
                        'data': f"Test data for concept {i}",
                        'tags': [f'tag_{j}' for j in range(5)]
                    },
                    confidence=0.5 + (i % 50) / 100
                )
                concepts.append(concept)
            
            # 测试插入时间
            start_time = time.time()
            for concept in concepts:
                memory.add_concept(concept)
            elapsed_time = time.time() - start_time
            
            avg_time = elapsed_time / batch_size * 1000  # 毫秒
            results.append({
                'batch_size': batch_size,
                'total_time': elapsed_time,
                'avg_time_ms': avg_time
            })
            
            print(f"批量 {batch_size}: {elapsed_time:.3f}秒, 平均 {avg_time:.2f}ms/概念")
            
            # 清理
            memory.clear()
        
        memory.close()
        return {'insert_performance': results}
    
    def benchmark_search(self) -> Dict[str, Any]:
        """测试搜索性能"""
        memory = Neo4jSemanticMemory(self.config)
        memory.clear()
        
        # 准备测试数据
        print("准备搜索测试数据...")
        for i in range(1000):
            concept = Concept(
                id="",
                name=f"Search Test {i}",
                category=f"category_{i % 20}",
                attributes={
                    'description': f"This is a test concept number {i}",
                    'keywords': ['search', 'test', 'benchmark', f'keyword_{i % 50}']
                }
            )
            memory.add_concept(concept)
        
        # 测试不同类型的搜索
        search_tests = [
            ("精确匹配", "Search Test 500"),
            ("模糊匹配", "search"),
            ("关键词", "keyword_25"),
            ("类别搜索", "category_10"),
            ("不存在", "nonexistent_term")
        ]
        
        results = []
        for test_name, query in search_tests:
            times = []
            
            # 多次运行取平均
            for _ in range(5):
                start_time = time.time()
                items = memory.recall(query, limit=50)
                elapsed_time = time.time() - start_time
                times.append(elapsed_time)
            
            avg_time = statistics.mean(times) * 1000  # 毫秒
            results.append({
                'test_name': test_name,
                'query': query,
                'avg_time_ms': avg_time,
                'result_count': len(items)
            })
            
            print(f"{test_name} ('{query}'): {avg_time:.2f}ms, {len(items)} 结果")
        
        memory.close()
        return {'search_performance': results}
    
    def benchmark_graph_traversal(self) -> Dict[str, Any]:
        """测试图遍历性能"""
        memory = Neo4jSemanticMemory(self.config)
        memory.clear()
        
        # 创建测试图结构
        print("创建测试图结构...")
        
        # 创建根节点
        root = Concept(id="root", name="Root Node", category="root")
        root_id = memory.add_concept(root)
        
        # 创建多层结构
        layers = 4
        nodes_per_parent = 5
        current_layer = [root_id]
        total_nodes = 1
        
        for layer in range(layers):
            next_layer = []
            for parent_id in current_layer:
                for i in range(nodes_per_parent):
                    child = Concept(
                        id="",
                        name=f"Layer {layer+1} Node {i}",
                        category=f"layer_{layer+1}"
                    )
                    child_id = memory.add_concept(child)
                    memory.create_relationship(parent_id, child_id, "CONTAINS")
                    next_layer.append(child_id)
                    total_nodes += 1
            current_layer = next_layer
        
        print(f"创建了 {total_nodes} 个节点")
        
        # 测试不同深度的遍历
        results = []
        for depth in range(1, layers + 1):
            times = []
            
            for _ in range(3):
                start_time = time.time()
                graph = memory.get_knowledge_graph(root_id, depth=depth)
                elapsed_time = time.time() - start_time
                times.append(elapsed_time)
            
            avg_time = statistics.mean(times)
            node_count = len(graph['nodes'])
            edge_count = len(graph['edges'])
            
            results.append({
                'depth': depth,
                'avg_time': avg_time,
                'node_count': node_count,
                'edge_count': edge_count
            })
            
            print(f"深度 {depth}: {avg_time:.3f}秒, {node_count} 节点, {edge_count} 边")
        
        memory.close()
        return {'graph_traversal': results}
    
    def benchmark_concurrency(self) -> Dict[str, Any]:
        """测试并发性能"""
        import threading
        import queue
        
        memory = Neo4jSemanticMemory(self.config)
        memory.clear()
        
        # 准备测试
        thread_counts = [1, 2, 4, 8]
        operations_per_thread = 100
        results = []
        
        def worker(thread_id: int, result_queue: queue.Queue):
            """工作线程"""
            successes = 0
            failures = 0
            start_time = time.time()
            
            for i in range(operations_per_thread):
                try:
                    if i % 3 == 0:
                        # 插入
                        concept = Concept(
                            id="",
                            name=f"Thread {thread_id} Concept {i}",
                            category="concurrent"
                        )
                        memory.add_concept(concept)
                    elif i % 3 == 1:
                        # 搜索
                        memory.recall(f"Thread {thread_id}", limit=10)
                    else:
                        # 统计
                        memory.get_statistics()
                    successes += 1
                except Exception:
                    failures += 1
            
            elapsed_time = time.time() - start_time
            result_queue.put({
                'thread_id': thread_id,
                'successes': successes,
                'failures': failures,
                'time': elapsed_time
            })
        
        for thread_count in thread_counts:
            print(f"\n测试 {thread_count} 个线程...")
            result_queue = queue.Queue()
            threads = []
            
            start_time = time.time()
            
            # 启动线程
            for i in range(thread_count):
                t = threading.Thread(target=worker, args=(i, result_queue))
                threads.append(t)
                t.start()
            
            # 等待完成
            for t in threads:
                t.join()
            
            total_time = time.time() - start_time
            
            # 收集结果
            thread_results = []
            total_successes = 0
            total_failures = 0
            
            while not result_queue.empty():
                result = result_queue.get()
                thread_results.append(result)
                total_successes += result['successes']
                total_failures += result['failures']
            
            throughput = total_successes / total_time
            
            results.append({
                'thread_count': thread_count,
                'total_time': total_time,
                'total_operations': total_successes + total_failures,
                'success_rate': total_successes / (total_successes + total_failures),
                'throughput_ops_per_sec': throughput
            })
            
            print(f"  完成: {total_successes} 成功, {total_failures} 失败")
            print(f"  吞吐量: {throughput:.2f} ops/sec")
            
            # 清理
            memory.clear()
        
        memory.close()
        return {'concurrency': results}
    
    def benchmark_large_scale(self) -> Dict[str, Any]:
        """测试大规模数据性能"""
        memory = Neo4jSemanticMemory(self.config)
        memory.clear()
        
        results = {}
        
        # 测试不同规模
        scales = [1000, 5000, 10000]
        
        for scale in scales:
            print(f"\n测试规模: {scale} 概念")
            
            # 插入测试
            insert_start = time.time()
            for i in range(scale):
                concept = Concept(
                    id="",
                    name=f"Large Scale Concept {i}",
                    category=f"category_{i % 50}",
                    attributes={
                        'index': i,
                        'scale_test': True,
                        'data': f"Data for concept {i}" * 10  # 增加数据量
                    },
                    confidence=0.5 + (i % 100) / 200,
                    domain=f"domain_{i % 20}"
                )
                memory.add_concept(concept)
                
                # 每1000个概念创建一些关系
                if i > 0 and i % 1000 == 0:
                    # 创建一些随机关系
                    for _ in range(10):
                        source_idx = i - np.random.randint(1, min(1000, i))
                        target_idx = i - np.random.randint(1, min(1000, i))
                        if source_idx != target_idx:
                            memory.create_relationship(
                                f"large_scale_concept_{source_idx}",
                                f"large_scale_concept_{target_idx}",
                                "RELATED_TO"
                            )
            
            insert_time = time.time() - insert_start
            
            # 获取统计信息
            stats = memory.get_statistics()
            
            # 随机搜索测试
            search_times = []
            for _ in range(10):
                query_idx = np.random.randint(0, scale)
                start_time = time.time()
                memory.recall(f"Concept {query_idx}", limit=50)
                search_times.append(time.time() - start_time)
            
            avg_search_time = statistics.mean(search_times)
            
            results[f'scale_{scale}'] = {
                'insert_time': insert_time,
                'avg_insert_time_ms': (insert_time / scale) * 1000,
                'total_concepts': stats['total_concepts'],
                'total_relationships': stats['total_relationships'],
                'avg_search_time_ms': avg_search_time * 1000
            }
            
            print(f"  插入时间: {insert_time:.2f}秒")
            print(f"  平均插入: {(insert_time / scale) * 1000:.2f}ms/概念")
            print(f"  平均搜索: {avg_search_time * 1000:.2f}ms")
            
            # 清理
            memory.clear()
        
        memory.close()
        return {'large_scale': results}
    
    def benchmark_complex_queries(self) -> Dict[str, Any]:
        """测试复杂查询性能"""
        memory = Neo4jSemanticMemory(self.config)
        memory.clear()
        
        # 创建复杂的知识图谱
        print("创建复杂知识图谱...")
        
        # 创建主题域
        domains = []
        for d in range(5):
            domain = Concept(
                id=f"domain_{d}",
                name=f"Domain {d}",
                category="domain",
                confidence=1.0
            )
            memory.add_concept(domain)
            domains.append(domain.id)
        
        # 每个域创建概念
        concept_count = 0
        for domain_id in domains:
            for i in range(100):
                concept = Concept(
                    id="",
                    name=f"Concept in {domain_id} #{i}",
                    category="concept",
                    attributes={
                        'domain': domain_id,
                        'importance': np.random.random(),
                        'tags': [f'tag_{j}' for j in range(np.random.randint(1, 5))]
                    },
                    confidence=0.5 + np.random.random() * 0.5
                )
                cid = memory.add_concept(concept)
                
                # 连接到域
                memory.create_relationship(domain_id, cid, "CONTAINS")
                
                # 创建概念间的关系
                if concept_count > 0 and np.random.random() > 0.7:
                    # 随机连接到之前的概念
                    target_idx = np.random.randint(0, concept_count)
                    memory.create_relationship(cid, f"concept_{target_idx}", "RELATED_TO")
                
                concept_count += 1
        
        print(f"创建了 {concept_count} 个概念")
        
        # 测试复杂查询
        results = []
        
        # 1. 多跳查询
        print("\n测试多跳查询...")
        for hops in [1, 2, 3]:
            start_time = time.time()
            graph = memory.get_knowledge_graph(domains[0], depth=hops)
            elapsed_time = time.time() - start_time
            
            results.append({
                'query_type': f'{hops}-hop traversal',
                'time': elapsed_time,
                'result_size': len(graph['nodes'])
            })
            print(f"  {hops} 跳: {elapsed_time:.3f}秒, {len(graph['nodes'])} 节点")
        
        # 2. 模式查找
        print("\n测试模式查找...")
        start_time = time.time()
        patterns = memory.find_patterns("concept", min_confidence=0.7)
        elapsed_time = time.time() - start_time
        
        results.append({
            'query_type': 'pattern finding',
            'time': elapsed_time,
            'result_size': len(patterns)
        })
        print(f"  模式查找: {elapsed_time:.3f}秒, {len(patterns)} 模式")
        
        # 3. 相似度计算
        print("\n测试相似度计算...")
        # 随机选择两个概念
        all_concepts = memory.list_all(limit=1000)
        if len(all_concepts) >= 2:
            times = []
            for _ in range(5):
                idx1, idx2 = np.random.choice(len(all_concepts), 2, replace=False)
                start_time = time.time()
                similarity = memory.calculate_concept_similarity(
                    all_concepts[idx1].id,
                    all_concepts[idx2].id
                )
                times.append(time.time() - start_time)
            
            avg_time = statistics.mean(times)
            results.append({
                'query_type': 'similarity calculation',
                'time': avg_time,
                'result_size': 1
            })
            print(f"  相似度计算: {avg_time * 1000:.2f}ms")
        
        memory.close()
        return {'complex_queries': results}
    
    def generate_report(self):
        """生成性能报告"""
        # 保存JSON报告
        report_file = f"neo4j_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n\n性能报告已保存到: {report_file}")
        
        # 生成可视化报告（如果有matplotlib）
        try:
            self.generate_visualizations()
        except ImportError:
            print("需要安装matplotlib来生成可视化报告")
    
    def generate_visualizations(self):
        """生成可视化图表"""
        # 插入性能图
        if 'insert_performance' in self.results['tests'].get('插入性能', {}):
            data = self.results['tests']['插入性能']['insert_performance']
            
            plt.figure(figsize=(10, 6))
            batch_sizes = [d['batch_size'] for d in data]
            avg_times = [d['avg_time_ms'] for d in data]
            
            plt.plot(batch_sizes, avg_times, 'b-o')
            plt.xlabel('批量大小')
            plt.ylabel('平均插入时间 (ms)')
            plt.title('Neo4j插入性能')
            plt.grid(True)
            plt.savefig('neo4j_insert_performance.png')
            plt.close()
        
        # 并发性能图
        if 'concurrency' in self.results['tests'].get('并发性能', {}):
            data = self.results['tests']['并发性能']['concurrency']
            
            plt.figure(figsize=(10, 6))
            thread_counts = [d['thread_count'] for d in data]
            throughputs = [d['throughput_ops_per_sec'] for d in data]
            
            plt.bar(thread_counts, throughputs)
            plt.xlabel('线程数')
            plt.ylabel('吞吐量 (ops/sec)')
            plt.title('Neo4j并发性能')
            plt.savefig('neo4j_concurrency_performance.png')
            plt.close()
        
        print("可视化图表已生成")


def main():
    """运行基准测试"""
    # 检查Neo4j是否可用
    try:
        from neo4j import GraphDatabase
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="graphiti123!",
            database="benchmark"
        )
        driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password)
        )
        driver.verify_connectivity()
        driver.close()
    except Exception as e:
        print(f"Neo4j不可用: {e}")
        print("请确保Neo4j正在运行并且凭据正确")
        return
    
    # 运行基准测试
    benchmark = Neo4jBenchmark(config)
    benchmark.run_all_benchmarks()


if __name__ == '__main__':
    main()
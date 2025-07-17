#!/usr/bin/env python3
"""
Memory Profiling and Benchmarking for WorkflowState
===================================================

This script analyzes memory usage patterns of the WorkflowState class
under various scenarios to identify optimization opportunities.

Scenarios tested:
1. Small states with short history
2. Large complex states with deep nesting
3. Long-running workflows with extensive history
4. Rapid state updates (stress testing)
5. Different serialization methods comparison

Memory metrics collected:
- Peak memory usage
- Average memory usage
- Memory growth over time
- Serialization/deserialization overhead
- History storage efficiency
"""

import sys
import gc
import time
import json
import pickle
import psutil
import tracemalloc
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Import our classes
from enhancedAgent_v2 import WorkflowState, StateHistoryEntry

@dataclass
class MemoryBenchmarkResult:
    """Results from a memory benchmark test"""
    scenario_name: str
    peak_memory_mb: float
    avg_memory_mb: float
    memory_growth_mb: float
    serialization_time_ms: float
    deserialization_time_ms: float
    serialized_size_bytes: int
    history_count: int
    total_duration_ms: float

class MemoryProfiler:
    """Memory profiling utilities for WorkflowState"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = 0
        self.memory_samples = []
        
    def start_profiling(self):
        """Start memory profiling session"""
        gc.collect()  # Clean up before starting
        tracemalloc.start()
        self.baseline_memory = self.get_memory_usage()
        self.memory_samples = [self.baseline_memory]
        
    def stop_profiling(self) -> Dict[str, float]:
        """Stop profiling and return statistics"""
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        final_memory = self.get_memory_usage()
        self.memory_samples.append(final_memory)
        
        return {
            'peak_memory_mb': peak / 1024 / 1024,
            'current_memory_mb': current / 1024 / 1024,
            'memory_growth_mb': (final_memory - self.baseline_memory) / 1024 / 1024,
            'avg_memory_mb': sum(self.memory_samples) / len(self.memory_samples) / 1024 / 1024
        }
        
    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        return self.process.memory_info().rss
        
    def sample_memory(self):
        """Take a memory sample"""
        self.memory_samples.append(self.get_memory_usage())

class WorkflowStateBenchmark:
    """Benchmark suite for WorkflowState memory usage"""
    
    def __init__(self):
        self.profiler = MemoryProfiler()
        self.results = []
        
    def create_small_state_data(self) -> str:
        """Create small state data for testing"""
        return json.dumps({
            "current_step": "step_1",
            "status": "running",
            "progress": 0.25,
            "last_update": datetime.now().isoformat()
        })
        
    def create_large_state_data(self) -> str:
        """Create large, complex state data for testing"""
        data = {
            "workflow_metadata": {
                "id": "workflow_12345",
                "name": "Complex Data Processing Pipeline",
                "version": "2.1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            "current_step": {
                "id": "data_transformation_step",
                "name": "Advanced Data Transformation",
                "status": "in_progress",
                "progress": 0.67,
                "substeps": [
                    {"id": f"substep_{i}", "status": "completed", "data": f"result_{i}" * 100}
                    for i in range(50)
                ]
            },
            "processed_data": {
                "records": [
                    {
                        "id": i,
                        "name": f"Record {i}",
                        "data": {
                            "values": list(range(100)),
                            "metadata": {"tags": [f"tag_{j}" for j in range(20)]},
                            "processed_at": datetime.now().isoformat()
                        }
                    }
                    for i in range(100)
                ]
            },
            "system_state": {
                "memory_usage": {"current": 1024, "peak": 2048},
                "cpu_usage": {"current": 45.2, "average": 38.7},
                "disk_usage": {"used": 15360, "available": 51200},
                "network_stats": {"bytes_sent": 1048576, "bytes_received": 2097152}
            },
            "error_log": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "WARNING",
                    "message": f"Warning message {i}" * 50,
                    "stack_trace": "Stack trace details here" * 20
                }
                for i in range(25)
            ]
        }
        return json.dumps(data, indent=2)
        
    def benchmark_small_states_short_history(self) -> MemoryBenchmarkResult:
        """Benchmark: Small states with short history"""
        print("🔍 Benchmarking: Small states with short history...")
        
        self.profiler.start_profiling()
        start_time = time.time()
        
        # Create WorkflowState and add small states
        state = WorkflowState()
        
        for i in range(20):
            state_data = self.create_small_state_data()
            state.set_global_state(state_data, source=f"test_source_{i}")
            
            if i % 5 == 0:
                self.profiler.sample_memory()
                
        # Test serialization
        ser_start = time.time()
        serialized = pickle.dumps(state)
        ser_time = (time.time() - ser_start) * 1000
        
        # Test deserialization
        deser_start = time.time()
        deserialized_state = pickle.loads(serialized)
        deser_time = (time.time() - deser_start) * 1000
        
        end_time = time.time()
        memory_stats = self.profiler.stop_profiling()
        
        return MemoryBenchmarkResult(
            scenario_name="Small States Short History",
            peak_memory_mb=memory_stats['peak_memory_mb'],
            avg_memory_mb=memory_stats['avg_memory_mb'],
            memory_growth_mb=memory_stats['memory_growth_mb'],
            serialization_time_ms=ser_time,
            deserialization_time_ms=deser_time,
            serialized_size_bytes=len(serialized),
            history_count=state.get_state_history_count(),
            total_duration_ms=(end_time - start_time) * 1000
        )
        
    def benchmark_large_states_deep_nesting(self) -> MemoryBenchmarkResult:
        """Benchmark: Large complex states with deep nesting"""
        print("🔍 Benchmarking: Large complex states with deep nesting...")
        
        self.profiler.start_profiling()
        start_time = time.time()
        
        # Create WorkflowState and add large complex states
        state = WorkflowState()
        
        for i in range(10):
            state_data = self.create_large_state_data()
            state.set_global_state(state_data, source=f"complex_source_{i}")
            
            if i % 2 == 0:
                self.profiler.sample_memory()
                
        # Test serialization
        ser_start = time.time()
        serialized = pickle.dumps(state)
        ser_time = (time.time() - ser_start) * 1000
        
        # Test deserialization
        deser_start = time.time()
        deserialized_state = pickle.loads(serialized)
        deser_time = (time.time() - deser_start) * 1000
        
        end_time = time.time()
        memory_stats = self.profiler.stop_profiling()
        
        return MemoryBenchmarkResult(
            scenario_name="Large Complex States",
            peak_memory_mb=memory_stats['peak_memory_mb'],
            avg_memory_mb=memory_stats['avg_memory_mb'],
            memory_growth_mb=memory_stats['memory_growth_mb'],
            serialization_time_ms=ser_time,
            deserialization_time_ms=deser_time,
            serialized_size_bytes=len(serialized),
            history_count=state.get_state_history_count(),
            total_duration_ms=(end_time - start_time) * 1000
        )
        
    def benchmark_long_running_extensive_history(self) -> MemoryBenchmarkResult:
        """Benchmark: Long-running workflows with extensive history"""
        print("🔍 Benchmarking: Long-running workflows with extensive history...")
        
        self.profiler.start_profiling()
        start_time = time.time()
        
        # Create WorkflowState and simulate long-running workflow
        state = WorkflowState()
        
        # Simulate 200 state updates (exceeding default history limit of 50)
        for i in range(200):
            state_data = f"Long running state update {i}: " + self.create_small_state_data()
            state.set_global_state(state_data, source=f"long_running_source_{i}")
            
            if i % 25 == 0:
                self.profiler.sample_memory()
                
        # Test serialization
        ser_start = time.time()
        serialized = pickle.dumps(state)
        ser_time = (time.time() - ser_start) * 1000
        
        # Test deserialization
        deser_start = time.time()
        deserialized_state = pickle.loads(serialized)
        deser_time = (time.time() - deser_start) * 1000
        
        end_time = time.time()
        memory_stats = self.profiler.stop_profiling()
        
        return MemoryBenchmarkResult(
            scenario_name="Long Running Extensive History",
            peak_memory_mb=memory_stats['peak_memory_mb'],
            avg_memory_mb=memory_stats['avg_memory_mb'],
            memory_growth_mb=memory_stats['memory_growth_mb'],
            serialization_time_ms=ser_time,
            deserialization_time_ms=deser_time,
            serialized_size_bytes=len(serialized),
            history_count=state.get_state_history_count(),
            total_duration_ms=(end_time - start_time) * 1000
        )
        
    def benchmark_rapid_updates_stress_test(self) -> MemoryBenchmarkResult:
        """Benchmark: Rapid state updates (stress testing)"""
        print("🔍 Benchmarking: Rapid state updates (stress testing)...")
        
        self.profiler.start_profiling()
        start_time = time.time()
        
        # Create WorkflowState and perform rapid updates
        state = WorkflowState()
        
        # Rapid updates with minimal delay
        for i in range(500):
            state_data = f"Rapid update {i}: {time.time()}"
            state.set_global_state(state_data, source=f"rapid_source_{i}")
            
            if i % 50 == 0:
                self.profiler.sample_memory()
                
        # Test serialization
        ser_start = time.time()
        serialized = pickle.dumps(state)
        ser_time = (time.time() - ser_start) * 1000
        
        # Test deserialization
        deser_start = time.time()
        deserialized_state = pickle.loads(serialized)
        deser_time = (time.time() - deser_start) * 1000
        
        end_time = time.time()
        memory_stats = self.profiler.stop_profiling()
        
        return MemoryBenchmarkResult(
            scenario_name="Rapid Updates Stress Test",
            peak_memory_mb=memory_stats['peak_memory_mb'],
            avg_memory_mb=memory_stats['avg_memory_mb'],
            memory_growth_mb=memory_stats['memory_growth_mb'],
            serialization_time_ms=ser_time,
            deserialization_time_ms=deser_time,
            serialized_size_bytes=len(serialized),
            history_count=state.get_state_history_count(),
            total_duration_ms=(end_time - start_time) * 1000
        )
        
    def run_all_benchmarks(self) -> List[MemoryBenchmarkResult]:
        """Run all benchmark scenarios"""
        print("🚀 Starting WorkflowState Memory Benchmarks...")
        print("=" * 60)
        
        benchmarks = [
            self.benchmark_small_states_short_history,
            self.benchmark_large_states_deep_nesting,
            self.benchmark_long_running_extensive_history,
            self.benchmark_rapid_updates_stress_test
        ]
        
        results = []
        for benchmark in benchmarks:
            try:
                result = benchmark()
                results.append(result)
                print(f"✅ {result.scenario_name} completed")
                
                # Brief pause between benchmarks
                time.sleep(0.5)
                gc.collect()  # Clean up between tests
                
            except Exception as e:
                print(f"❌ {benchmark.__name__} failed: {e}")
                
        return results
        
    def print_results(self, results: List[MemoryBenchmarkResult]):
        """Print benchmark results in a formatted table"""
        print("\n" + "=" * 80)
        print("📊 MEMORY BENCHMARK RESULTS")
        print("=" * 80)
        
        # Header
        print(f"{'Scenario':<30} {'Peak MB':<10} {'Avg MB':<10} {'Growth MB':<12} {'Ser ms':<8} {'Deser ms':<10} {'Size KB':<10} {'History':<8}")
        print("-" * 80)
        
        # Results
        for result in results:
            print(f"{result.scenario_name:<30} "
                  f"{result.peak_memory_mb:<10.2f} "
                  f"{result.avg_memory_mb:<10.2f} "
                  f"{result.memory_growth_mb:<12.2f} "
                  f"{result.serialization_time_ms:<8.2f} "
                  f"{result.deserialization_time_ms:<10.2f} "
                  f"{result.serialized_size_bytes/1024:<10.2f} "
                  f"{result.history_count:<8}")
                  
        # Summary statistics
        print("-" * 80)
        avg_peak = sum(r.peak_memory_mb for r in results) / len(results)
        avg_growth = sum(r.memory_growth_mb for r in results) / len(results)
        total_size = sum(r.serialized_size_bytes for r in results)
        
        print(f"{'AVERAGES':<30} "
              f"{avg_peak:<10.2f} "
              f"{'N/A':<10} "
              f"{avg_growth:<12.2f} "
              f"{'N/A':<8} "
              f"{'N/A':<10} "
              f"{total_size/1024:<10.2f} "
              f"{'N/A':<8}")
              
        print("\n📋 Key Findings:")
        
        # Find the scenario with highest memory usage
        highest_memory = max(results, key=lambda r: r.peak_memory_mb)
        print(f"• Highest memory usage: {highest_memory.scenario_name} ({highest_memory.peak_memory_mb:.2f} MB)")
        
        # Find the scenario with largest serialized size
        largest_size = max(results, key=lambda r: r.serialized_size_bytes)
        print(f"• Largest serialized size: {largest_size.scenario_name} ({largest_size.serialized_size_bytes/1024:.2f} KB)")
        
        # Find the slowest serialization
        slowest_ser = max(results, key=lambda r: r.serialization_time_ms)
        print(f"• Slowest serialization: {slowest_ser.scenario_name} ({slowest_ser.serialization_time_ms:.2f} ms)")
        
        # Memory efficiency analysis
        print(f"\n🔍 Memory Efficiency Analysis:")
        for result in results:
            efficiency = result.history_count / (result.serialized_size_bytes / 1024) if result.serialized_size_bytes > 0 else 0
            print(f"• {result.scenario_name}: {efficiency:.2f} history entries per KB")

def main():
    """Main function to run memory benchmarks"""
    print("🧪 WorkflowState Memory Profiling and Benchmarking")
    print("=" * 60)
    
    # Check if required packages are available
    try:
        import psutil
        import tracemalloc
    except ImportError as e:
        print(f"❌ Required package missing: {e}")
        print("Please install: pip install psutil")
        return
        
    # Run benchmarks
    benchmark = WorkflowStateBenchmark()
    results = benchmark.run_all_benchmarks()
    
    if results:
        benchmark.print_results(results)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"memory_benchmark_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump([
                {
                    'scenario_name': r.scenario_name,
                    'peak_memory_mb': r.peak_memory_mb,
                    'avg_memory_mb': r.avg_memory_mb,
                    'memory_growth_mb': r.memory_growth_mb,
                    'serialization_time_ms': r.serialization_time_ms,
                    'deserialization_time_ms': r.deserialization_time_ms,
                    'serialized_size_bytes': r.serialized_size_bytes,
                    'history_count': r.history_count,
                    'total_duration_ms': r.total_duration_ms
                }
                for r in results
            ], f, indent=2)
            
        print(f"\n💾 Results saved to: {filename}")
        
    else:
        print("❌ No benchmark results to display")

if __name__ == "__main__":
    main() 
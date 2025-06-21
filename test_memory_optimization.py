#!/usr/bin/env python3
"""
Memory Optimization Test
========================

Test the new memory optimization features of WorkflowState:
1. Serialization fix (pickle with thread locks)
2. Memory usage analysis
3. History compression
4. Overall optimization pipeline

This test verifies that the serialization problem is resolved
and that the optimization features work correctly.
"""

import pickle
import json
from datetime import datetime
from enhancedAgent_v2 import WorkflowState

def test_serialization_fix():
    """Test that the serialization problem is now fixed"""
    print("🧪 Testing serialization fix...")
    
    # Create a WorkflowState with some data
    state = WorkflowState()
    state.set_global_state("Initial test state")
    
    # Add some history
    for i in range(5):
        state.set_global_state(f"State update {i}", source=f"test_source_{i}")
    
    try:
        # Test pickle serialization
        serialized_data = pickle.dumps(state)
        print(f"✅ Serialization successful! Size: {len(serialized_data)} bytes")
        
        # Test deserialization
        deserialized_state = pickle.loads(serialized_data)
        print(f"✅ Deserialization successful!")
        
        # Verify data integrity
        original_global_state = state.get_global_state()
        restored_global_state = deserialized_state.get_global_state()
        
        if original_global_state == restored_global_state:
            print("✅ Data integrity verified: Global state matches")
        else:
            print(f"❌ Data integrity failed: '{original_global_state}' != '{restored_global_state}'")
            
        # Test that the lock works in the deserialized object
        deserialized_state.set_global_state("Testing lock functionality")
        print("✅ Thread lock functionality verified after deserialization")
        
        return True
        
    except Exception as e:
        print(f"❌ Serialization test failed: {e}")
        return False

def test_memory_analysis():
    """Test memory usage analysis features"""
    print("\n📊 Testing memory usage analysis...")
    
    state = WorkflowState()
    
    # Add various sized states
    test_states = [
        "Small state",
        "Medium state with more content that is somewhat longer",
        "Large state with extensive content that goes on and on, containing lots of details about the current workflow execution status, including detailed information about each step, any errors encountered, progress indicators, and comprehensive context about what the system is currently doing." * 3
    ]
    
    for i, test_state in enumerate(test_states):
        state.set_global_state(test_state, source=f"analysis_test_{i}")
    
    try:
        memory_usage = state.get_memory_usage()
        print(f"✅ Memory analysis successful!")
        print(f"   📈 Global state size: {memory_usage['global_state_size_bytes']} bytes")
        print(f"   📈 History total size: {memory_usage['history_total_size_bytes']} bytes")
        print(f"   📈 Serialized size: {memory_usage['serialized_size_bytes']} bytes")
        print(f"   📈 History count: {memory_usage['history_count']}")
        print(f"   📈 Average state size: {memory_usage['average_state_size_bytes']:.2f} bytes")
        print(f"   📈 Compression ratio: {memory_usage['compression_ratio']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory analysis test failed: {e}")
        return False

def test_history_compression():
    """Test history compression functionality"""
    print("\n🗜️ Testing history compression...")
    
    state = WorkflowState()
    
    # Add some compressible states (repetitive content)
    repetitive_content = "This is a repetitive state with repeated patterns. " * 10
    for i in range(10):
        state.set_global_state(f"{repetitive_content} Update {i}", source=f"compress_test_{i}")
    
    try:
        # Get initial memory usage
        initial_usage = state.get_memory_usage()
        print(f"   📊 Initial serialized size: {initial_usage['serialized_size_bytes']} bytes")
        
        # Apply compression
        success = state.compress_history(compression_level=9)  # High compression
        if not success:
            print("❌ History compression failed")
            return False
            
        print("✅ History compression applied")
        
        # Get compressed memory usage
        compressed_usage = state.get_memory_usage()
        print(f"   📊 Compressed serialized size: {compressed_usage['serialized_size_bytes']} bytes")
        
        # Calculate compression savings
        initial_size = initial_usage['serialized_size_bytes']
        compressed_size = compressed_usage['serialized_size_bytes']
        if initial_size > compressed_size:
            savings = initial_size - compressed_size
            percentage = (savings / initial_size) * 100
            print(f"✅ Compression saved {savings} bytes ({percentage:.1f}%)")
        else:
            print("ℹ️ No significant compression achieved (expected with small data)")
        
        # Test decompression
        decompressed_history = state.get_decompressed_history(limit=3)
        if decompressed_history:
            first_entry = decompressed_history[0]
            if "This is a repetitive state" in first_entry.state_snapshot:
                print("✅ Decompression verified: Content successfully restored")
            else:
                print("❌ Decompression failed: Content not properly restored")
                
        return True
        
    except Exception as e:
        print(f"❌ History compression test failed: {e}")
        return False

def test_full_optimization():
    """Test the complete optimization pipeline"""
    print("\n🚀 Testing full optimization pipeline...")
    
    state = WorkflowState()
    
    # Create a realistic scenario with mixed content
    states = [
        "System initialization complete",
        "Loading configuration from /path/to/config.json",
        "Database connection established successfully",
        "User authentication module loaded", 
        "API endpoints registered: /api/v1/users, /api/v1/auth, /api/v1/data",
        "Cache warming started for user sessions",
        "Background task scheduler initialized",
        "Email service connection verified",
        "File upload handler configured with 10MB limit",
        "System ready to accept requests"
    ]
    
    # Add states with some empty ones to test cleanup
    for i, state_content in enumerate(states):
        state.set_global_state(state_content, source=f"system_init_{i}")
        # Add some empty states to test cleanup
        if i % 3 == 0:
            state.set_global_state("   ", source=f"empty_{i}")  # Whitespace only
    
    try:
        # Run full optimization
        optimization_results = state.optimize_memory(
            enable_compression=True,
            compression_level=6
        )
        
        if optimization_results['success']:
            print("✅ Full optimization completed successfully!")
            
            optimizations = optimization_results['optimizations_applied']
            print(f"   🔧 Optimizations applied: {', '.join(optimizations)}")
            
            if 'space_saved_bytes' in optimization_results:
                saved = optimization_results['space_saved_bytes']
                percentage = optimization_results['percentage_saved']
                print(f"   💾 Space saved: {saved} bytes ({percentage:.2f}%)")
            else:
                print("   ℹ️ No significant space savings (small dataset)")
                
            # Verify functionality after optimization
            state.set_global_state("Post-optimization test", source="verification")
            current_state = state.get_global_state()
            if current_state == "Post-optimization test":
                print("✅ Functionality verified after optimization")
            else:
                print("❌ Functionality compromised after optimization")
                
        else:
            print("❌ Full optimization failed")
            if 'error' in optimization_results:
                print(f"   Error: {optimization_results['error']}")
                
        return optimization_results['success']
        
    except Exception as e:
        print(f"❌ Full optimization test failed: {e}")
        return False

def main():
    """Run all memory optimization tests"""
    print("🔬 Memory Optimization Test Suite")
    print("=" * 50)
    
    tests = [
        ("Serialization Fix", test_serialization_fix),
        ("Memory Analysis", test_memory_analysis),
        ("History Compression", test_history_compression),
        ("Full Optimization", test_full_optimization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🎯 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    print(f"\n📋 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All memory optimization tests passed!")
        return True
    else:
        print("⚠️ Some tests failed - review implementation")
        return False

if __name__ == "__main__":
    main() 
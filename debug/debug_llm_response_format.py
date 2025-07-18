#!/usr/bin/env python3
"""
Debug script to test LLM response_format compatibility
"""

import sys
import os
from pathlib import Path

# Add paths to find the modules
sys.path.append(str(Path(__file__).parent))

from llm_lazy import get_modelngchain_core.messages import HumanMessage

def test_llm_response_format():
    """Test if the LLM supports response_format parameter"""
    
    print("Testing LLM response_format compatibility...")
    print(f"LLM type: {type(get_model("deepseek_chat"))}")
    print(f"LLM model: {get_model("deepseek_chat").model_name}")
    
    messages = [HumanMessage("Say hello")]
    
    # Test 1: Call without response_format
    try:
        print("\n1. Testing without response_format...")
        result1 = get_model("deepseek_chat").invoke(messages)
        print(f"✅ Success: {result1.content[:100]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Call with response_format=None
    try:
        print("\n2. Testing with response_format=None...")
        result2 = get_model("deepseek_chat").invoke(messages, response_format=None)
        print(f"✅ Success: {result2.content[:100]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Call with **kwargs approach
    try:
        print("\n3. Testing with **kwargs (empty)...")
        kwargs = {}
        result3 = get_model("deepseek_chat").invoke(messages, **kwargs)
        print(f"✅ Success: {result3.content[:100]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 4: Check what parameters the invoke method accepts
    try:
        print("\n4. Checking invoke method signature...")
        import inspect
        sig = inspect.signature(get_model("deepseek_chat").invoke)
        print(f"Invoke signature: {sig}")
        print(f"Parameters: {list(sig.parameters.keys())}")
    except Exception as e:
        print(f"❌ Failed to get signature: {e}")

if __name__ == "__main__":
    test_llm_response_format()
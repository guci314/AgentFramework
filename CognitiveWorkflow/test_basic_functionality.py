#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test basic cognitive workflow functionality after UUID/timestamp removal
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'cognitive_workflow_rule_base'))

from services.state_service import StateService
from services.language_model_service import LanguageModelService
from infrastructure.repository_impl import StateRepositoryImpl
from domain.entities import GlobalState

def test_basic_functionality():
    """Test that basic workflow functionality still works"""
    
    print("Testing basic cognitive workflow functionality...")
    
    try:
        # Initialize services
        state_repo = StateRepositoryImpl(storage_path="./.test_cognitive_workflow_data/states")
        llm_service = LanguageModelService()
        state_service = StateService(llm_service, state_repo)
        
        print("✓ Services initialized successfully")
        
        # Create initial state
        initial_state = state_service.create_initial_state(
            goal="Test goal: Create a simple hello world program",
            workflow_id="test_workflow_001"
        )
        
        print(f"✓ Initial state created with ID: {initial_state.id}")
        print(f"✓ State description: {initial_state.description[:100]}...")
        
        # Load the state back
        loaded_state = state_service.load_state(initial_state.id)
        
        if loaded_state:
            print(f"✓ State successfully loaded back from storage")
            print(f"✓ Loaded state ID: {loaded_state.id}")
        else:
            print("✗ Failed to load state back")
            return False
        
        print("\n🎉 Basic functionality test passed! The system works correctly without UUIDs/timestamps.")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
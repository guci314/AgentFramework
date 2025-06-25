#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify UUID and timestamp removal for LLM caching optimization
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'cognitive_workflow_rule_base'))

from domain.entities import ProductionRule, RuleExecution, GlobalState, WorkflowResult
from domain.value_objects import RulePhase, ExecutionStatus

def test_uuid_removal():
    """Test that entities can be created without automatic UUID/timestamp generation"""
    
    print("Testing UUID and timestamp removal...")
    
    # Test ProductionRule creation
    rule = ProductionRule(
        id="test_rule_1",
        name="Test Rule",
        condition="IF test condition",
        action="THEN test action",
        agent_capability_id="test_agent",
        priority=50,
        phase=RulePhase.PROBLEM_SOLVING,
        expected_outcome="Test outcome"
    )
    print(f"✓ ProductionRule created with deterministic ID: {rule.id}")
    
    # Test RuleExecution creation
    execution = RuleExecution(
        id="test_execution_1",
        rule_id="test_rule_1",
        status=ExecutionStatus.PENDING
    )
    print(f"✓ RuleExecution created with deterministic ID: {execution.id}")
    
    # Test GlobalState creation
    state = GlobalState(
        id="test_state_1",
        description="Test state",
        context_variables={'test': 'value'},
        execution_history=[],
        workflow_id="test_workflow_1",
        iteration_count=0,
        goal_achieved=False
    )
    print(f"✓ GlobalState created with deterministic ID: {state.id}")
    
    # Test WorkflowResult creation
    result = WorkflowResult(
        success=True,
        message="Test result",
        data={'result': 'success'},
        error_details=None,
        metadata={'test': 'metadata'}
    )
    print(f"✓ WorkflowResult created successfully")
    
    # Test serialization
    rule_dict = rule.to_dict()
    state_dict = state.to_dict()
    result_dict = result.to_dict()
    
    print(f"✓ All entities can be serialized to dict")
    
    # Check that no UUID or timestamp fields are present
    forbidden_fields = ['created_at', 'updated_at', 'timestamp', 'started_at']
    
    for field in forbidden_fields:
        if field in rule_dict:
            print(f"✗ Found forbidden field '{field}' in ProductionRule")
            return False
        if field in state_dict:
            print(f"✗ Found forbidden field '{field}' in GlobalState")
            return False
        if field in result_dict and field != 'timestamp':  # WorkflowResult keeps timestamp for analysis
            print(f"✗ Found forbidden field '{field}' in WorkflowResult")
            return False
    
    print("✓ No forbidden UUID/timestamp fields found in serialized entities")
    
    print("\n🎉 All tests passed! UUID and timestamp removal successful for LLM caching optimization.")
    return True

if __name__ == "__main__":
    success = test_uuid_removal()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test Stage 1 - Requirement Freeze
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from llm_router import LLMRouter
from roles import hod

def test_requirement_freeze():
    """Test that Stage 1 creates frozen requirements"""
    
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not set")
        return False
    
    config = Config()
    llm = LLMRouter(config)
    
    print("Testing Stage 1: Requirement Freeze")
    print("=" * 70)
    
    # Simulate Stage 0 output
    stage0_result = {
        "approved": true,
        "feasible": true,
        "assessment": "Standard FPGA UART design, well-established implementation",
        "questions": [],
        "assumptions": [
            "System clock: 50 MHz",
            "FIFO depth: 16 bytes",
            "Reset: Synchronous active-high",
            "Stop bits: 1",
            "Parity: None",
            "Data bits: 8",
            "Baud rate: 115200"
        ]
    }
    
    user_idea = "UART transmitter with 8-bit data, 115200 baud"
    
    print(f"\nUser Idea: {user_idea}")
    print(f"\nStage 0 Assumptions:")
    for assumption in stage0_result['assumptions']:
        print(f"  - {assumption}")
    
    print("\n" + "=" * 70)
    print("Calling Stage 1: Requirement Freeze...")
    print("=" * 70)
    
    try:
        result = hod.freeze_requirements(llm, user_idea, stage0_result)
        
        print("\nRaw Result:")
        print(json.dumps(result, indent=2))
        
        print("\n" + "=" * 70)
        approved = result.get('approved', False)
        
        if approved:
            print("✓ Stage 1 PASSED - Requirements frozen")
            requirements = result.get('requirements', {})
            
            print(f"\nTitle: {requirements.get('title', 'N/A')}")
            print(f"Description: {requirements.get('description', 'N/A')}")
            
            clock_specs = requirements.get('clock_specs', {})
            primary = clock_specs.get('primary_clock', {})
            print(f"Clock: {primary.get('frequency_mhz', 'N/A')} MHz")
            
            params = requirements.get('parameters', {})
            print(f"\nKey Parameters:")
            for key, value in params.items():
                print(f"  {key}: {value}")
            
            return True
        else:
            print("✗ Stage 1 FAILED - Requirements not approved")
            print(f"Reason: {result.get('rejection_reason', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_requirement_freeze()
    sys.exit(0 if success else 1)

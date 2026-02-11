#!/usr/bin/env python3
"""
Quick test to verify Stage 0 validation works correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from llm_router import LLMRouter
from roles import hod

def test_validation():
    """Test that validation approves reasonable ideas"""
    
    # Set a test API key if not already set
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not set")
        return False
    
    config = Config()
    llm_router = LLMRouter(config)
    
    test_ideas = [
        "UART transmitter with 8-bit data, 115200 baud",
        "SPI master controller, mode 0, 8-bit transfers",
        "Button debouncer with 10ms debounce time",
        "16-bit counter with enable and reset"
    ]
    
    print("Testing Stage 0 Validation")
    print("=" * 60)
    
    for idea in test_ideas:
        print(f"\nTesting: {idea}")
        try:
            result = hod.validate_idea(llm_router, idea)
            
            approved = result.get("approved", False)
            status = "✓ APPROVED" if approved else "✗ REJECTED"
            
            print(f"  Result: {status}")
            
            if approved:
                print(f"  Assessment: {result.get('assessment', 'N/A')}")
                if result.get('assumptions'):
                    print(f"  Assumptions made: {len(result['assumptions'])}")
            else:
                print(f"  Reason: {result.get('rejection_reason', 'N/A')}")
                
        except Exception as e:
            print(f"  ERROR: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("Validation test complete")
    return True

if __name__ == "__main__":
    success = test_validation()
    sys.exit(0 if success else 1)

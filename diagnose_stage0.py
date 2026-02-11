#!/usr/bin/env python3
"""
Diagnostic script to see raw LLM responses from Stage 0
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from llm_router import LLMRouter

def diagnose_validation():
    """Check raw LLM response for validation"""
    
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not set")
        print("Set it with: export GROQ_API_KEY='your-key-here'")
        return
    
    config = Config()
    llm = LLMRouter(config)
    
    print(f"Using model: {config.hod_model}")
    print(f"Temperature: {config.temperature}")
    print("=" * 70)
    
    system_prompt = """You are validating FPGA design ideas. Your job: APPROVE viable ideas.

RULES:
1. Standard FPGA designs (UART, SPI, counters, etc.) → APPROVE with assumptions
2. Only reject if truly impossible for FPGAs
3. Make reasonable assumptions for missing details

EXAMPLES OF WHAT TO APPROVE:
- UART transmitter → APPROVE (assume 50MHz clock, 16-byte FIFO)
- SPI master → APPROVE (assume mode 0, 50MHz system clock)
- Counter → APPROVE (assume 50MHz clock, sync reset)

EXAMPLES OF WHAT TO REJECT (rare):
- "10 GHz clock" → REJECT (impossible for FPGA)
- "Run Linux" → REJECT (needs CPU, not just FPGA)

Output JSON:
{
  "approved": true,
  "feasible": true,
  "assessment": "Standard FPGA design, viable",
  "questions": [],
  "assumptions": [
    "System clock: 50 MHz",
    "Add more specific assumptions here"
  ]
}

For UART transmitter with 115200 baud, you would APPROVE and assume:
- System clock: 50 MHz (sufficient for baud rate generation)
- FIFO depth: 16 bytes (standard buffering)
- Reset type: Synchronous active-high
- Interface: ready/valid handshaking"""

    user_prompt = """Design Idea: UART transmitter with 8-bit data, 115200 baud

Is this viable for FPGA? If yes, APPROVE it with specific assumptions.

EXAMPLE - For "UART transmitter with 8-bit data, 115200 baud":
{
  "approved": true,
  "feasible": true,
  "assessment": "Standard FPGA UART design, well-established implementation",
  "questions": [],
  "assumptions": [
    "System clock: 50 MHz",
    "FIFO depth: 16 bytes",
    "Reset: Synchronous active-high",
    "Stop bits: 1",
    "Parity: None"
  ]
}

Now evaluate: UART transmitter with 8-bit data, 115200 baud

Return JSON output."""

    print("\nSending request to Groq API...")
    print("=" * 70)
    
    try:
        response = llm.call_with_system_prompt(
            role="hod",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format="json",
            temperature=0.1
        )
        
        print("\nRAW RESPONSE CONTENT:")
        print("=" * 70)
        print(response['content'])
        print("=" * 70)
        
        print("\nRESPONSE METADATA:")
        print(f"Model used: {response.get('model', 'unknown')}")
        print(f"Tokens: {response.get('usage', {})}")
        print("=" * 70)
        
        print("\nPARSING JSON...")
        try:
            parsed = llm.parse_json_response(response)
            
            print("\nPARSED JSON:")
            print("=" * 70)
            print(json.dumps(parsed, indent=2))
            print("=" * 70)
            
            print("\nVALIDATION RESULT:")
            print("=" * 70)
            approved = parsed.get('approved')
            feasible = parsed.get('feasible')
            
            print(f"✓ Approved: {approved}")
            print(f"✓ Feasible: {feasible}")
            print(f"✓ Assessment: {parsed.get('assessment', 'N/A')}")
            
            if approved:
                print(f"\n✓ SUCCESS - Design was approved!")
                assumptions = parsed.get('assumptions', [])
                print(f"\nAssumptions made ({len(assumptions)}):")
                for i, assumption in enumerate(assumptions, 1):
                    print(f"  {i}. {assumption}")
            else:
                print(f"\n✗ FAILED - Design was rejected")
                print(f"Reason: {parsed.get('rejection_reason', 'NOT PROVIDED')}")
                print("\nThis is unexpected for a UART design!")
                print("Check the model or prompt configuration.")
                
        except json.JSONDecodeError as e:
            print(f"\n✗ ERROR: Failed to parse JSON")
            print(f"Error: {e}")
            print("\nThe LLM did not return valid JSON.")
            print("Try checking if response_format='json' is working.")
            
    except Exception as e:
        print(f"\n✗ ERROR: API call failed")
        print(f"Error: {e}")
        print("\nCheck:")
        print("  1. GROQ_API_KEY is set correctly")
        print("  2. Network connection")
        print("  3. Groq API status")

if __name__ == "__main__":
    diagnose_validation()

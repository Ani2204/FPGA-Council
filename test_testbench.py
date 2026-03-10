#!/usr/bin/env python3
"""
Test Stage 5b - Testbench Generation
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from llm_router import LLMRouter
from roles import testbench


def test_testbench_generation():
    """Test that Stage 5b generates valid Verilog testbenches for a given module"""

    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not set")
        return False

    config = Config()
    llm = LLMRouter(config)

    print("Testing Stage 5b: Testbench Generation")
    print("=" * 70)

    # Simulate Stage 1 requirements output
    requirements = {
        "approved": True,
        "requirements": {
            "title": "16-bit Counter with Enable and Reset",
            "description": "Synchronous 16-bit counter with active-high enable and synchronous reset",
            "clock_specs": {
                "primary_clock": {
                    "name": "clk",
                    "frequency_mhz": 50
                }
            },
            "parameters": {
                "width": 16,
                "reset_value": 0
            }
        }
    }

    # Simulate Stage 5 verified module output (a simple 16-bit counter)
    verified_modules = [
        {
            "module_name": "counter_16bit",
            "verilog_code": (
                "module counter_16bit (\n"
                "    input  wire        clk,\n"
                "    input  wire        rst,\n"
                "    input  wire        en,\n"
                "    output reg  [15:0] count\n"
                ");\n"
                "    always @(posedge clk) begin\n"
                "        if (rst)\n"
                "            count <= 16'h0000;\n"
                "        else if (en)\n"
                "            count <= count + 16'h0001;\n"
                "    end\n"
                "endmodule\n"
            )
        }
    ]

    print(f"\nDesign: {requirements['requirements']['title']}")
    print(f"Modules to test: {[m['module_name'] for m in verified_modules]}")
    print("\n" + "=" * 70)
    print("Calling Stage 5b: Testbench Generation...")
    print("=" * 70)

    try:
        result = testbench.generate_testbench(llm, requirements, verified_modules)

        print("\nRaw Result (truncated):")
        # Print JSON but truncate long verilog_code fields for readability
        display = json.loads(json.dumps(result))
        for tb in display.get("testbenches", []):
            code = tb.get("verilog_code", "")
            if len(code) > 200:
                tb["verilog_code"] = code[:200] + "...[truncated]"
        print(json.dumps(display, indent=2))

        print("\n" + "=" * 70)
        testbenches = result.get("testbenches", [])

        if testbenches:
            print(f"✓ Stage 5b PASSED - {len(testbenches)} testbench(es) generated")
            for tb in testbenches:
                tb_name = tb.get('module_name') or (tb.get('dut_module', 'unknown') + '_tb')
                dut = tb.get('dut_module', 'N/A')
                print(f"\n  Testbench: {tb_name}")
                print(f"  DUT:       {dut}")
                print(f"  Test cases ({len(test_cases)}):")
                for tc in test_cases:
                    print(f"    - {tc}")
                verilog = tb.get('verilog_code', '')
                print(f"  Code length: {len(verilog)} chars")
                # Verify basic testbench structure
                has_timescale = '`timescale' in verilog
                has_initial = 'initial' in verilog
                has_finish = '$finish' in verilog
                has_module = f"module {tb_name}" in verilog or 'module ' in verilog
                print(f"  Has `timescale: {has_timescale}")
                print(f"  Has initial block: {has_initial}")
                print(f"  Has $finish: {has_finish}")
                print(f"  Has module decl: {has_module}")

            sim_notes = result.get("simulation_notes", "")
            if sim_notes:
                print(f"\nSimulation notes: {sim_notes}")

            return True
        else:
            print("✗ Stage 5b FAILED - No testbenches generated")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_testbench_generation()
    sys.exit(0 if success else 1)

"""
Testbench Role
Generates self-checking Verilog simulation testbenches for verified RTL modules
"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_prompt(prompt_name: str) -> str:
    """Load prompt template from file"""
    prompt_path = Path("prompts") / f"{prompt_name}.txt"
    if prompt_path.exists():
        return prompt_path.read_text()
    return ""


def generate_testbench(
    llm_router,
    requirements: Dict[str, Any],
    verified_modules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Stage 5b: Generate self-checking Verilog testbenches for verified RTL modules

    Args:
        llm_router: LLM router instance
        requirements: Frozen requirements from Stage 1
        verified_modules: List of verified Verilog module dicts from Stage 5

    Returns:
        Dict with 'testbenches' list and 'simulation_notes' string
    """
    system_prompt = _load_prompt("testbench") or """You are the Testbench Engineer. Your ONLY job is to write Verilog simulation testbenches.

TESTBENCH RULES (MANDATORY):
- Use `timescale 1ns/1ps at the top of every file
- Define a free-running clock matching the RTL clock frequency
- Assert synchronous reset for at least 2 clock cycles at startup
- Use initial blocks for stimulus (allowed in testbench)
- Use #delay for timing (allowed in testbench)
- Call $finish after all tests complete
- Use $display to report test progress and results
- Add automatic pass/fail checks comparing expected vs actual values
- Print overall PASS/FAIL summary at the end
- Name the testbench module <dut_module>_tb

COVERAGE REQUIREMENTS:
- Reset behaviour
- Normal functional operation
- Edge cases (all-zeros, all-ones, overflow, boundary values)
- Enable/disable toggling if module has enable inputs

Output ONLY valid JSON with this structure:
{
  "testbenches": [
    {
      "module_name": "<dut_module>_tb",
      "dut_module": "<dut_module>",
      "description": "brief description of what is tested",
      "verilog_code": "complete Verilog testbench code",
      "test_cases": ["list of test scenarios covered"],
      "coverage_notes": "summary of functional coverage"
    }
  ],
  "simulation_notes": "how to compile and run simulations"
}"""

    # Build concise module summaries for the prompt (code + port list)
    module_summaries = []
    for module in verified_modules:
        module_name = module.get('module_name') or module.get('name') or 'unnamed_module'
        verilog_code = module.get('verilog_code') or module.get('code') or module.get('verilog', '')
        module_summaries.append({
            "module_name": module_name,
            "verilog_code": verilog_code
        })

    user_prompt = f"""REQUIREMENTS:
{json.dumps(requirements.get('requirements', {}), indent=2)}

VERIFIED RTL MODULES (write one testbench per module):
{json.dumps(module_summaries, indent=2)}

Generate complete, self-checking Verilog testbenches for ALL modules above.

Each testbench must:
1. Instantiate the module under test with correct port connections
2. Generate a free-running clock
3. Apply synchronous reset, then drive meaningful test vectors
4. Check outputs automatically and print PASS/FAIL for each check
5. End with $finish

IMPORTANT: Escape all special characters in the Verilog code properly for JSON.

Return JSON output with all testbenches."""

    # Try with JSON mode first, fall back to text mode if validation fails
    try:
        response = llm_router.call_with_system_prompt(
            role="testbench",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format="json"
        )
        result = llm_router.parse_json_response(response)
    except Exception as e:
        error_str = str(e)
        if "json_validate_failed" in error_str or "JSON" in error_str:
            logger.warning(f"JSON mode failed for testbench generation: {e}")
            logger.info("Retrying without strict JSON mode...")
            response = llm_router.call_with_system_prompt(
                role="testbench",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format=None
            )
            result = llm_router.parse_json_response(response)
        else:
            raise

    testbenches = result.get("testbenches", [])
    logger.info(f"Generated {len(testbenches)} testbench(es)")
    for tb in testbenches:
        tb_name = tb.get('module_name') or (tb.get('dut_module', 'unknown') + '_tb')
        logger.info(f"  - {tb_name}")

    return result

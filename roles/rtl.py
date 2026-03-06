"""
RTL Role
Generates synthesizable Verilog code ONLY
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


def generate_rtl(
    llm_router,
    requirements: Dict[str, Any],
    architecture_design: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Stage 4: Generate synthesizable Verilog RTL
    
    Args:
        llm_router: LLM router instance
        requirements: Frozen requirements
        architecture_design: Approved architecture
        
    Returns:
        Generated Verilog modules
    """
    system_prompt = _load_prompt("rtl") or """You are the RTL Design Engineer. Your ONLY job is to write synthesizable Verilog code.

Your responsibilities:
1. Implement the exact architecture provided
2. Write clean, synthesizable Verilog (not SystemVerilog unless specified)
3. Follow coding best practices for FPGA synthesis
4. Include proper reset logic and clock domain handling
5. Add comments for clarity

CRITICAL RULES - SYNTHESIZABLE CODE ONLY:
- Use blocking assignments (=) for combinational logic
- Use non-blocking assignments (<=) for sequential logic
- Avoid latches - all combinational outputs must be assigned in all cases
- No delays (#) - this is not a testbench
- No initial blocks except for simulation-only code in comments
- Proper sensitivity lists for always blocks
- No division or modulo by non-power-of-2 (use shifts/masks instead)
- No floating point
- Explicit bit widths on all constants
- Proper handling of multi-bit signals

CODE QUALITY:
- Modular design matching architecture
- Clear signal names
- Comments for complex logic
- One module per response unit
- Include module header with I/O description

Output ONLY valid JSON with this structure:
{
  "modules": [
    {
      "module_name": "name",
      "description": "brief description",
      "verilog_code": "complete Verilog code",
      "dependencies": ["list of other modules this depends on"],
      "synthesis_notes": "any notes for synthesis"
    }
  ],
  "integration_notes": "how modules connect together",
  "testbench_recommendations": "what to test"
}

VERILOG FORMAT:
- Full module with proper port declarations
- Include parameter definitions if needed
- Complete implementation, not snippets
- Use Verilog-2001 or later syntax"""

    # Extract blocks to implement
    blocks = architecture_design.get("block_diagram", {}).get("blocks", [])
    fsms = architecture_design.get("fsms", [])
    
    context = f"""REQUIREMENTS:
{json.dumps(requirements.get('requirements', {}), indent=2)}

ARCHITECTURE BLOCKS:
{json.dumps(blocks, indent=2)}

FSMS:
{json.dumps(fsms, indent=2)}

INTERFACES:
{json.dumps(architecture_design.get('interface_specifications', []), indent=2)}

CLOCK DOMAINS:
{json.dumps(architecture_design.get('clock_domains', []), indent=2)}"""

    user_prompt = f"""{context}

Generate complete, synthesizable Verilog implementation for all modules.

Ensure code is production-quality and follows all synthesis rules.

IMPORTANT: Escape all special characters in the Verilog code properly for JSON.

Return JSON output with all modules."""

    # Try with JSON mode first, fall back to text mode if JSON validation fails
    try:
        response = llm_router.call_with_system_prompt(
            role="rtl",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format="json"
        )
        result = llm_router.parse_json_response(response)
    except Exception as e:
        error_str = str(e)
        if "json_validate_failed" in error_str or "JSON" in error_str:
            logger.warning(f"JSON mode failed due to validation error: {e}")
            logger.info("Retrying without strict JSON mode...")
            
            # Retry without JSON mode constraint
            response = llm_router.call_with_system_prompt(
                role="rtl",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format=None  # No strict JSON mode
            )
            result = llm_router.parse_json_response(response)
        else:
            # Some other error, re-raise it
            raise
    
    # Log generated modules
    modules = result.get("modules", [])
    logger.info(f"Generated {len(modules)} Verilog modules")
    for module in modules:
        # Handle different possible field names
        module_name = module.get('module_name') or module.get('name') or 'unknown'
        logger.info(f"  - {module_name}")
    
    return result


def fix_rtl(
    llm_router,
    original_module: Dict[str, Any],
    errors: List[str],
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fix RTL based on toolchain errors
    
    Args:
        llm_router: LLM router instance
        original_module: Original module with errors
        errors: List of error messages from toolchain
        requirements: Original requirements for context
        
    Returns:
        Fixed module
    """
    system_prompt = _load_prompt("rtl") or """You are the RTL Design Engineer specializing in fixing synthesis and lint errors.

Your responsibility is to fix Verilog code based on toolchain error messages.

CRITICAL RULES:
- Maintain original functionality
- Fix ONLY the reported errors
- Ensure code remains synthesizable
- Do not add unnecessary complexity
- Keep the same module interface unless errors require changes

Output ONLY valid JSON with this structure:
{
  "fixed_module": {
    "module_name": "name",
    "verilog_code": "corrected Verilog code",
    "changes_made": ["list of specific fixes applied"],
    "explanation": "why changes fix the errors"
  }
}"""

    user_prompt = f"""ORIGINAL MODULE:
{original_module.get('verilog_code', '')}

ERRORS TO FIX:
{chr(10).join(errors)}

REQUIREMENTS CONTEXT:
{json.dumps(requirements.get('requirements', {}), indent=2)}

Fix the Verilog code to resolve all errors while maintaining functionality.

Return JSON output with the fixed module."""

    response = llm_router.call_with_system_prompt(
        role="rtl",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format="json"
    )
    
    result = llm_router.parse_json_response(response)
    
    if "fixed_module" in result:
        logger.info(f"Fixed module: {result['fixed_module'].get('module_name')}")
        logger.info(f"Changes: {result['fixed_module'].get('changes_made', [])}")
    
    return result

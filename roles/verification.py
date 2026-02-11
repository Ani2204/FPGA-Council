"""
Verification Role
Audits RTL for correctness and provides fixes
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


def audit_rtl(
    llm_router,
    requirements: Dict[str, Any],
    modules: List[Dict[str, Any]],
    validation_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Stage 5: Audit RTL and provide fixes
    
    Args:
        llm_router: LLM router instance
        requirements: Frozen requirements
        modules: RTL modules to audit
        validation_results: Toolchain validation results
        
    Returns:
        Audit results with fixed modules if issues found
    """
    system_prompt = _load_prompt("verify") or """You are the Verification Engineer. Your role is to audit RTL for correctness and synthesizability.

Your responsibilities:
1. Review RTL against requirements and architecture
2. Check for synthesis issues (latches, incomplete case statements, etc.)
3. Verify timing considerations
4. Check for common RTL bugs
5. Fix any issues found by toolchain validation
6. Ensure code follows best practices

VERIFICATION CHECKLIST:
- All combinational paths have complete assignments
- No unintended latches
- Proper reset handling (sync vs async)
- Clock domain crossing handled properly
- No simulation-only constructs in synthesis code
- Bit widths match specifications
- FSM encoding is explicit
- No timing violations likely
- Proper use of blocking vs non-blocking assignments

CRITICAL RULES:
- Use toolchain errors as primary feedback
- Fix errors without changing functionality
- Maintain module interfaces
- Document all changes made
- Be conservative - don't over-optimize

Output ONLY valid JSON with this structure:
{
  "has_issues": boolean,
  "overall_assessment": "summary of audit",
  "module_audits": [
    {
      "module_name": "name",
      "passed": boolean,
      "issues_found": [
        {
          "type": "error|warning",
          "description": "issue description",
          "location": "line or block description",
          "severity": "critical|major|minor"
        }
      ],
      "toolchain_errors": ["errors from validation"],
      "recommendations": ["list of fixes needed"]
    }
  ],
  "fixed_modules": [
    {
      "module_name": "name",
      "verilog_code": "corrected code",
      "changes_made": ["specific changes"],
      "verification_notes": "notes about fixes"
    }
  ],
  "verification_recommendations": "suggestions for testbench"
}"""

    # Combine module info with validation results
    module_info = []
    for i, module in enumerate(modules):
        info = {
            "module": module,
            "validation": validation_results[i] if i < len(validation_results) else {}
        }
        module_info.append(info)
    
    user_prompt = f"""REQUIREMENTS:
{json.dumps(requirements.get('requirements', {}), indent=2)}

MODULES TO AUDIT:
{json.dumps([m['module'] for m in module_info], indent=2)}

TOOLCHAIN VALIDATION RESULTS:
{json.dumps([m['validation'] for m in module_info], indent=2)}

Audit all modules and provide fixes for any issues found.

Return JSON output following the schema."""

    response = llm_router.call_with_system_prompt(
        role="verification",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format="json",
        max_tokens=8192
    )
    
    result = llm_router.parse_json_response(response)
    
    # Log audit summary
    has_issues = result.get("has_issues", False)
    logger.info(f"Audit complete. Issues found: {has_issues}")
    
    if has_issues and "fixed_modules" in result:
        logger.info(f"Provided {len(result['fixed_modules'])} fixed modules")
    
    return result


def review_fixes(
    llm_router,
    original_modules: List[Dict[str, Any]],
    fixed_modules: List[Dict[str, Any]],
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Review fixes to ensure they maintain correctness
    
    Args:
        llm_router: LLM router instance
        original_modules: Original modules
        fixed_modules: Fixed modules
        requirements: Requirements for context
        
    Returns:
        Review results
    """
    system_prompt = """You are the Verification Engineer reviewing fixes to RTL code.

Your responsibility is to ensure fixes maintain correctness and don't introduce new issues.

REVIEW CHECKLIST:
- Fixes address the original errors
- Functionality is preserved
- No new issues introduced
- Changes are minimal and targeted
- Code quality maintained or improved

Output ONLY valid JSON with this structure:
{
  "approved": boolean,
  "review_summary": "overall assessment",
  "module_reviews": [
    {
      "module_name": "name",
      "approved": boolean,
      "concerns": ["list any concerns"],
      "recommendations": ["suggestions"]
    }
  ],
  "overall_concerns": ["any system-level concerns"]
}"""

    user_prompt = f"""ORIGINAL MODULES:
{json.dumps(original_modules, indent=2)}

FIXED MODULES:
{json.dumps(fixed_modules, indent=2)}

REQUIREMENTS:
{json.dumps(requirements.get('requirements', {}), indent=2)}

Review the fixes to ensure they are correct and don't introduce new issues.

Return JSON output."""

    response = llm_router.call_with_system_prompt(
        role="verification",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format="json"
    )
    
    result = llm_router.parse_json_response(response)
    return result

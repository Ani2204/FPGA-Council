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
    system_prompt = """You are the Verification Engineer. Your PRIMARY job is to fix RTL errors found by the toolchain.

CRITICAL: If the toolchain reports ANY errors, you MUST:
1. Set "has_issues": true
2. Analyze the specific errors
3. Provide fixed Verilog code in "fixed_modules"

TOOLCHAIN ERRORS ARE THE SOURCE OF TRUTH!
If Yosys or Verilator reports errors, the RTL has issues - no exceptions.

Common toolchain errors and fixes:
- "inferred latch" → Add default assignments in all code paths
- "multiple drivers" → Remove duplicate assignments to same signal  
- "syntax error" → Fix Verilog syntax
- "undeclared identifier" → Declare all signals
- "width mismatch" → Match bit widths exactly

Output ONLY valid JSON:
{
  "has_issues": boolean,  ← TRUE if toolchain found ANY errors
  "overall_assessment": "summary",
  "module_audits": [
    {
      "module_name": "name",
      "passed": boolean,
      "issues_found": [{"type": "error", "description": "..."}],
      "toolchain_errors": ["list from validation"],
      "recommendations": ["fixes needed"]
    }
  ],
  "fixed_modules": [  ← REQUIRED if has_issues is true
    {
      "module_name": "name",
      "verilog_code": "corrected code here",
      "changes_made": ["specific changes"],
      "verification_notes": "what was fixed"
    }
  ]
}

REMEMBER: If toolchain validation shows passed=false, you MUST provide fixes!
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

CRITICAL INSTRUCTIONS:
1. Check each validation result - if "passed": false, there ARE errors
2. Read the "errors" and "warnings" arrays in validation results
3. If ANY module has passed: false, set has_issues: true
4. Provide fixed_modules with corrected Verilog code

Audit all modules and provide fixes for any issues found.

Return JSON output following the schema."""

    response = llm_router.call_with_system_prompt(
        role="verification",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format="json"
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

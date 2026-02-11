"""
System Role
Analyzes FPGA feasibility, timing, and resource constraints
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_prompt(prompt_name: str) -> str:
    """Load prompt template from file"""
    prompt_path = Path("prompts") / f"{prompt_name}.txt"
    if prompt_path.exists():
        return prompt_path.read_text()
    return ""


def check_feasibility(
    llm_router,
    requirements: Dict[str, Any],
    architecture_design: Dict[str, Any],
    verification_result: Dict[str, Any],
    target_fpga: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stage 6: Check FPGA implementation feasibility
    
    Args:
        llm_router: LLM router instance
        requirements: Frozen requirements
        architecture_design: Architecture design
        verification_result: Verified RTL results
        target_fpga: Target FPGA family (if specified)
        
    Returns:
        Feasibility analysis with risk assessment
    """
    system_prompt = _load_prompt("system") or """You are the System Engineer for FPGA implementation. Your role is to assess implementation feasibility.

Your responsibilities:
1. Estimate resource utilization (LUTs, FFs, BRAMs, DSPs)
2. Assess timing feasibility for target clock frequencies
3. Identify potential bottlenecks or critical paths
4. Evaluate power considerations
5. Check for FPGA-specific limitations
6. Provide risk assessment (LOW/MEDIUM/HIGH)

ANALYSIS AREAS:
- Resource estimation based on design complexity
- Timing closure probability
- Clock domain crossing risks
- I/O pin requirements
- Special resource needs (PLLs, high-speed transceivers, etc.)
- Implementation complexity

RISK LEVELS:
- LOW: Standard design, should implement easily
- MEDIUM: Some challenges, may need optimization
- HIGH: Significant risks, may not meet requirements

CRITICAL RULES:
- Be realistic about resource estimates
- Consider implementation experience
- Flag timing risks early
- Recommend specific FPGA families if not specified
- Consider power and thermal constraints

Output ONLY valid JSON with this structure:
{
  "feasible": boolean,
  "risk_level": "LOW|MEDIUM|HIGH",
  "overall_assessment": "summary",
  "resource_estimates": {
    "luts": {"estimated": number, "percentage": number, "confidence": "low|medium|high"},
    "flip_flops": {"estimated": number, "percentage": number, "confidence": "low|medium|high"},
    "brams": {"estimated": number, "percentage": number, "confidence": "low|medium|high"},
    "dsps": {"estimated": number, "percentage": number, "confidence": "low|medium|high"},
    "notes": "estimation methodology"
  },
  "timing_analysis": {
    "clock_domains": [
      {
        "name": "domain_name",
        "target_frequency_mhz": number,
        "estimated_achievable_mhz": number,
        "timing_risk": "LOW|MEDIUM|HIGH",
        "critical_paths": ["identified potential critical paths"],
        "recommendations": ["suggestions for timing closure"]
      }
    ],
    "overall_timing_risk": "LOW|MEDIUM|HIGH"
  },
  "implementation_challenges": [
    {
      "area": "category",
      "challenge": "description",
      "severity": "LOW|MEDIUM|HIGH",
      "mitigation": "suggested approach"
    }
  ],
  "fpga_recommendations": {
    "recommended_families": ["if not specified"],
    "minimum_device_size": "description",
    "special_requirements": ["PLLs, transceivers, etc."]
  },
  "power_thermal": {
    "estimated_power_w": number,
    "thermal_concerns": boolean,
    "notes": "power/thermal analysis"
  },
  "risks": [
    {
      "risk": "description",
      "probability": "LOW|MEDIUM|HIGH",
      "impact": "LOW|MEDIUM|HIGH",
      "mitigation": "recommended action"
    }
  ],
  "recommendations": ["overall implementation recommendations"],
  "go_no_go": "recommendation with rationale"
}"""

    # Build context
    req_spec = requirements.get('requirements', {})
    clock_specs = req_spec.get('clock_specs', {})
    interfaces = req_spec.get('interfaces', [])
    resource_targets = req_spec.get('resource_targets', {})
    
    blocks = architecture_design.get('block_diagram', {}).get('blocks', [])
    fsms = architecture_design.get('fsms', [])
    
    modules = verification_result.get('final_modules', [])
    
    target_info = f"Target FPGA: {target_fpga}" if target_fpga else "Target FPGA: Not specified - recommend suitable family"
    
    user_prompt = f"""{target_info}

REQUIREMENTS:
Clock Specs: {json.dumps(clock_specs, indent=2)}
Interfaces: {json.dumps(interfaces, indent=2)}
Resource Targets: {json.dumps(resource_targets, indent=2)}

ARCHITECTURE:
Number of blocks: {len(blocks)}
Number of FSMs: {len(fsms)}
Clock domains: {json.dumps(architecture_design.get('clock_domains', []), indent=2)}

RTL MODULES:
{json.dumps([{
    'name': m.get('module_name'),
    'description': m.get('description', '')
} for m in modules], indent=2)}

Analyze FPGA implementation feasibility and provide detailed risk assessment.

Return JSON output following the schema."""

    response = llm_router.call_with_system_prompt(
        role="system",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format="json"
    )
    
    result = llm_router.parse_json_response(response)
    
    # Log feasibility summary
    feasible = result.get("feasible", False)
    risk_level = result.get("risk_level", "UNKNOWN")
    logger.info(f"Feasibility check complete. Feasible: {feasible}, Risk: {risk_level}")
    
    return result

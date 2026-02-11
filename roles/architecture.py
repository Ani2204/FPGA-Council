"""
Architecture Role
Designs block diagrams, FSMs, and interfaces - NO CODE
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_prompt(prompt_name: str) -> str:
    """Load prompt template from file"""
    prompt_path = Path("prompts") / f"{prompt_name}.txt"
    if prompt_path.exists():
        return prompt_path.read_text()
    return ""


def design_architecture(llm_router, requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage 2: Design system architecture
    
    Args:
        llm_router: LLM router instance
        requirements: Frozen requirements specification
        
    Returns:
        Architecture design with blocks, FSMs, interfaces
    """
    system_prompt = _load_prompt("arch") or """You are the Architecture Designer for FPGA projects. Your role is to create detailed architectural designs WITHOUT writing any code.

Your responsibilities:
1. Design block diagram showing all modules and their connections
2. Design FSMs for control logic with states and transitions
3. Define all internal interfaces and data paths
4. Specify pipeline stages and data flow
5. Design register interfaces and control signals

CRITICAL RULES:
- NO CODE ALLOWED - you design, you don't implement
- Focus on structure, not implementation
- Define clear module boundaries
- Specify all signals between modules (name, width, direction, purpose)
- Design for testability and modularity
- Consider clock domain crossings
- Plan for error handling

Output ONLY valid JSON with this structure:
{
  "design_overview": "high-level description",
  "block_diagram": {
    "top_module": "name",
    "blocks": [
      {
        "name": "block_name",
        "type": "fsm|datapath|interface|control",
        "purpose": "description",
        "inputs": [{"name": "...", "width": number, "description": "..."}],
        "outputs": [{"name": "...", "width": number, "description": "..."}],
        "internal_state": "description if stateful"
      }
    ],
    "connections": [
      {
        "from": "source_block.signal",
        "to": "dest_block.signal",
        "width": number,
        "description": "purpose"
      }
    ]
  },
  "fsms": [
    {
      "name": "fsm_name",
      "purpose": "description",
      "states": [
        {"name": "STATE_NAME", "encoding": "optional", "description": "..."}
      ],
      "transitions": [
        {
          "from": "STATE_A",
          "to": "STATE_B",
          "condition": "description",
          "actions": ["list of actions in this state"]
        }
      ],
      "outputs": ["signals controlled by this FSM"]
    }
  ],
  "data_paths": [
    {
      "name": "path_name",
      "description": "data flow description",
      "stages": ["stage1", "stage2", ...],
      "latency_cycles": number
    }
  ],
  "clock_domains": [
    {
      "name": "domain_name",
      "clock_signal": "clk_name",
      "modules": ["list of modules in this domain"],
      "cdc_required": ["interfaces that cross domains"]
    }
  ],
  "interface_specifications": [
    {
      "name": "interface_name",
      "protocol": "description",
      "signals": [
        {"name": "...", "direction": "input|output", "width": number, "timing": "..."}
      ],
      "handshaking": "description",
      "timing_diagram": "text description of timing"
    }
  ],
  "error_handling": {
    "error_conditions": ["list of possible errors"],
    "detection_method": "how errors are detected",
    "response_strategy": "how system responds to errors"
  }
}"""

    user_prompt = f"""FROZEN REQUIREMENTS:
{json.dumps(requirements.get('requirements', {}), indent=2)}

Design the complete architecture for this system. Create block diagram, FSMs, and interface specs.

DO NOT write any Verilog or implementation code.

Return JSON output following the schema."""

    response = llm_router.call_with_system_prompt(
        role="architecture",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_format="json"
    )
    
    result = llm_router.parse_json_response(response)
    
    # Log architecture summary
    if "block_diagram" in result:
        blocks = result["block_diagram"].get("blocks", [])
        logger.info(f"Architecture designed with {len(blocks)} blocks")
        
    if "fsms" in result:
        fsms = result["fsms"]
        logger.info(f"Designed {len(fsms)} FSMs")
    
    return result

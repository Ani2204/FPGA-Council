"""
Stage Controller
Orchestrates the multi-role design flow with gated stages
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import Config
from llm_router import LLMRouter
from toolchain import ToolchainValidator
from roles import hod, architecture, rtl, verification, system_role

logger = logging.getLogger(__name__)


class StageController:
    """Controls progression through design stages with gating"""
    
    def __init__(
        self,
        config: Config,
        llm_router: LLMRouter,
        toolchain: ToolchainValidator
    ):
        self.config = config
        self.llm = llm_router
        self.toolchain = toolchain
        self.prompts_dir = Path("prompts")
    
    def stage0_idea_validation(self, user_idea: str) -> Dict[str, Any]:
        """
        Stage 0: Validate idea and gather constraints
        
        Args:
            user_idea: User's design description
            
        Returns:
            Validation result with questions and constraints
        """
        logger.info("Executing Stage 0: Idea Validation")
        logger.info(f"Validating: {user_idea}")
        
        result = hod.validate_idea(self.llm, user_idea)
        
        approved = result.get('approved', False)
        logger.info(f"Stage 0 complete. Approved: {approved}")
        
        if approved:
            assumptions = result.get('assumptions', [])
            logger.info(f"Made {len(assumptions)} assumption(s) for missing constraints")
        else:
            logger.warning(f"Rejection reason: {result.get('rejection_reason', 'Unknown')}")
        
        return result
    
    def stage1_requirement_freeze(
        self,
        user_idea: str,
        stage0_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stage 1: HOD freezes numeric requirements
        
        Args:
            user_idea: Original user idea
            stage0_result: Results from stage 0
            
        Returns:
            Frozen requirements specification
        """
        logger.info("Executing Stage 1: Requirement Freeze")
        
        result = hod.freeze_requirements(
            self.llm,
            user_idea,
            stage0_result
        )
        
        approved = result.get('approved', False)
        logger.info(f"Stage 1 complete. Approved: {approved}")
        
        if approved:
            requirements = result.get('requirements', {})
            logger.info(f"Title: {requirements.get('title', 'N/A')}")
            logger.info(f"Clock: {requirements.get('clock_specs', {}).get('primary_clock', {}).get('frequency_mhz', 'N/A')} MHz")
        else:
            logger.error(f"Stage 1 rejection reason: {result.get('rejection_reason', 'Unknown')}")
            logger.error("This is unexpected - Stage 1 should document requirements, not reject")
        
        
        return result
    
    def stage2_architecture_design(
        self,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stage 2: Architecture role designs system
        
        Args:
            requirements: Frozen requirements from stage 1
            
        Returns:
            Architecture design (no code)
        """
        logger.info("Executing Stage 2: Architecture Design")
        
        result = architecture.design_architecture(
            self.llm,
            requirements
        )
        
        logger.info("Stage 2 complete. Architecture designed.")
        if "block_diagram" in result:
            logger.info(f"Blocks: {', '.join(result['block_diagram'].get('blocks', []))}")
        
        return result
    
    def stage3_architecture_approval(
        self,
        requirements: Dict[str, Any],
        architecture_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stage 3: HOD approves architecture
        
        Args:
            requirements: Frozen requirements
            architecture_design: Architecture from stage 2
            
        Returns:
            Approval decision
        """
        logger.info("Executing Stage 3: Architecture Approval")
        
        result = hod.approve_architecture(
            self.llm,
            requirements,
            architecture_design
        )
        
        logger.info(f"Stage 3 complete. Approved: {result.get('approved', False)}")
        if not result.get("approved"):
            logger.warning(f"Architecture rejected: {result.get('rejection_reason', 'Unknown')}")
        
        return result
    
    def stage4_rtl_generation(
        self,
        requirements: Dict[str, Any],
        architecture_design: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stage 4: RTL role generates Verilog
        
        Args:
            requirements: Frozen requirements
            architecture_design: Approved architecture
            
        Returns:
            Generated Verilog modules
        """
        logger.info("Executing Stage 4: RTL Generation")
        
        result = rtl.generate_rtl(
            self.llm,
            requirements,
            architecture_design
        )
        
        logger.info(f"Stage 4 complete. Generated {len(result.get('modules', []))} modules.")
        for module in result.get("modules", []):
            logger.info(f"  - {module['module_name']}")
        
        return result
    
    def stage5_verification_audit(
        self,
        requirements: Dict[str, Any],
        rtl_output: Dict[str, Any],
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Stage 5: Verification audit with auto-fix loop
        
        Args:
            requirements: Frozen requirements
            rtl_output: RTL from stage 4
            max_iterations: Maximum fix iterations
            
        Returns:
            Verification results with final RTL
        """
        logger.info("Executing Stage 5: Verification Audit")
        
        current_modules = rtl_output.get("modules", [])
        iteration = 0
        all_passed = False
        audit_history = []
        
        while iteration < max_iterations and not all_passed:
            iteration += 1
            logger.info(f"Verification iteration {iteration}/{max_iterations}")
            
            # Run toolchain validation
            validation_results = self.toolchain.validate_multiple_modules(current_modules)
            
            # Check if all modules passed
            all_passed = all(vr.get("passed", False) for vr in validation_results)
            
            if all_passed:
                logger.info("All modules passed validation!")
                break
            
            # Run verification role audit
            audit_result = verification.audit_rtl(
                self.llm,
                requirements,
                current_modules,
                validation_results
            )
            
            audit_history.append({
                "iteration": iteration,
                "validation_results": validation_results,
                "audit": audit_result
            })
            
            # Check if verification role found issues
            if not audit_result.get("has_issues", False):
                # Verification role says it's OK, but toolchain failed
                # This is a critical error
                logger.error("Verification role approved but toolchain validation failed!")
                all_passed = False
                break
            
            # Get fixed modules
            if "fixed_modules" in audit_result:
                current_modules = audit_result["fixed_modules"]
                logger.info(f"Applied fixes from verification role")
            else:
                logger.error("Verification role did not provide fixed modules")
                break
        
        # Final validation
        final_validation = self.toolchain.validate_multiple_modules(current_modules)
        all_passed = all(vr.get("passed", False) for vr in final_validation)
        
        result = {
            "passed": all_passed,
            "iterations": iteration,
            "max_iterations": max_iterations,
            "final_modules": current_modules,
            "final_validation": final_validation,
            "audit_history": audit_history
        }
        
        logger.info(f"Stage 5 complete. Passed: {all_passed} after {iteration} iterations")
        
        return result
    
    def stage6_system_feasibility(
        self,
        requirements: Dict[str, Any],
        architecture_design: Dict[str, Any],
        verification_result: Dict[str, Any],
        target_fpga: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stage 6: System role checks FPGA feasibility
        
        Args:
            requirements: Frozen requirements
            architecture_design: Architecture design
            verification_result: Verified RTL
            target_fpga: Target FPGA family
            
        Returns:
            Feasibility analysis
        """
        logger.info("Executing Stage 6: System Feasibility Check")
        
        result = system_role.check_feasibility(
            self.llm,
            requirements,
            architecture_design,
            verification_result,
            target_fpga
        )
        
        logger.info("Stage 6 complete. Feasibility checked.")
        if "risk_level" in result:
            logger.info(f"Risk level: {result['risk_level']}")
        
        return result
    
    def stage7_final_approval(
        self,
        requirements: Dict[str, Any],
        architecture_design: Dict[str, Any],
        verification_result: Dict[str, Any],
        feasibility_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stage 7: Final HOD approval
        
        Args:
            requirements: Frozen requirements
            architecture_design: Architecture design
            verification_result: Verified RTL
            feasibility_result: System feasibility
            
        Returns:
            Final approval decision
        """
        logger.info("Executing Stage 7: Final HOD Approval")
        
        result = hod.final_approval(
            self.llm,
            requirements,
            architecture_design,
            verification_result,
            feasibility_result
        )
        
        logger.info(f"Stage 7 complete. Approved: {result.get('approved', False)}")
        if result.get("approved"):
            logger.info("✓ DESIGN FLOW COMPLETE - RTL ready for implementation")
        else:
            logger.warning(f"Design rejected: {result.get('rejection_reason', 'Unknown')}")
        
        return result

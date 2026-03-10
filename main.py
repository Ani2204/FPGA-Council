#!/usr/bin/env python3
"""
FPGA AI Design Bot - Main Entry Point
Multi-role AI orchestration for synthesizable Verilog generation
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from config import Config
from stage_controller import StageController
from llm_router import LLMRouter
from toolchain import ToolchainValidator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fpga_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class FPGADesignBot:
    """Main orchestrator for multi-role FPGA design system"""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm_router = LLMRouter(config)
        self.toolchain = ToolchainValidator(config)
        self.controller = StageController(config, self.llm_router, self.toolchain)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("outputs") / self.session_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run_design_flow(self, user_idea: str, target_fpga: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute complete design flow from idea to validated RTL
        
        Args:
            user_idea: High-level design description
            target_fpga: Optional FPGA target (e.g., 'ice40', 'ecp5')
            
        Returns:
            Complete session results with all stage outputs
        """
        logger.info(f"Starting design session {self.session_id}")
        logger.info(f"User idea: {user_idea}")
        
        session_data = {
            "session_id": self.session_id,
            "user_idea": user_idea,
            "target_fpga": target_fpga,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # Stage 0: Idea Validation and Constraint Gathering
            logger.info("=" * 80)
            logger.info("STAGE 0: Idea Validation & Constraint Gathering")
            logger.info("=" * 80)
            stage0_result = self.controller.stage0_idea_validation(user_idea)
            session_data["stages"]["stage0"] = stage0_result
            self._save_stage_output("stage0_validation.json", stage0_result)
            
            if not stage0_result.get("approved", False):
                logger.error("Stage 0 failed: Idea not approved")
                return session_data
            
            # Stage 1: HOD Requirement Freeze
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 1: HOD Requirement Freeze")
            logger.info("=" * 80)
            stage1_result = self.controller.stage1_requirement_freeze(
                user_idea, 
                stage0_result
            )
            session_data["stages"]["stage1"] = stage1_result
            self._save_stage_output("stage1_requirements.json", stage1_result)
            
            if not stage1_result.get("approved", False):
                logger.error("Stage 1 failed: Requirements not frozen")
                return session_data
            
            # Stage 2: Architecture Design
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 2: Architecture Design")
            logger.info("=" * 80)
            stage2_result = self.controller.stage2_architecture_design(
                stage1_result
            )
            session_data["stages"]["stage2"] = stage2_result
            self._save_stage_output("stage2_architecture.json", stage2_result)
            
            # Stage 3: HOD Architecture Approval
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 3: HOD Architecture Approval")
            logger.info("=" * 80)
            stage3_result = self.controller.stage3_architecture_approval(
                stage1_result,
                stage2_result
            )
            session_data["stages"]["stage3"] = stage3_result
            self._save_stage_output("stage3_approval.json", stage3_result)
            
            if not stage3_result.get("approved", False):
                logger.error("Stage 3 failed: Architecture not approved")
                return session_data
            
            # Stage 4: RTL Generation
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 4: RTL Generation")
            logger.info("=" * 80)
            stage4_result = self.controller.stage4_rtl_generation(
                stage1_result,
                stage2_result
            )
            session_data["stages"]["stage4"] = stage4_result
            self._save_stage_output("stage4_rtl.json", stage4_result)
            
            # Save Verilog files
            if "modules" in stage4_result:
                for module in stage4_result["modules"]:
                    # Handle different possible field names
                    module_name = module.get('module_name') or module.get('name') or 'unnamed_module'
                    verilog_code = module.get('verilog_code') or module.get('code') or module.get('verilog', '')
                    
                    if verilog_code:
                        verilog_path = self.output_dir / f"{module_name}.v"
                        verilog_path.write_text(verilog_code)
                        logger.info(f"Saved Verilog: {verilog_path}")
                    else:
                        logger.warning(f"Module {module_name} has no verilog_code field")
            
            # Stage 5: Verification Audit with Auto-Fix Loop
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 5: Verification Audit")
            logger.info("=" * 80)
            stage5_result = self.controller.stage5_verification_audit(
                stage1_result,
                stage4_result,
                max_iterations=self.config.max_verification_iterations
            )
            session_data["stages"]["stage5"] = stage5_result
            self._save_stage_output("stage5_verification.json", stage5_result)
            
            # Save final verified Verilog
            if stage5_result.get("passed", False) and "final_modules" in stage5_result:
                for module in stage5_result["final_modules"]:
                    module_name = module.get('module_name') or module.get('name') or 'unnamed_module'
                    verilog_code = module.get('verilog_code') or module.get('code') or module.get('verilog', '')
                    
                    if verilog_code:
                        verilog_path = self.output_dir / f"{module_name}_verified.v"
                        verilog_path.write_text(verilog_code)
                        logger.info(f"Saved verified Verilog: {verilog_path}")
            
            
            if not stage5_result.get("passed", False):
                logger.error("Stage 5 failed: Verification did not pass")
                return session_data

            # Stage 5b: Testbench Generation
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 5b: Testbench Generation")
            logger.info("=" * 80)
            stage5b_result = self.controller.stage5b_testbench_generation(
                stage1_result,
                stage5_result
            )
            session_data["stages"]["stage5b"] = stage5b_result
            self._save_stage_output("stage5b_testbenches.json", stage5b_result)

            # Save testbench Verilog files
            for tb in stage5b_result.get("testbenches", []):
                tb_name = tb.get('module_name') or (tb.get('dut_module', 'unnamed_module') + '_tb')
                tb_code = tb.get('verilog_code', '')
                if tb_code:
                    tb_path = self.output_dir / f"{tb_name}.v"
                    tb_path.write_text(tb_code)
                    logger.info(f"Saved testbench: {tb_path}")
                else:
                    logger.warning(f"Testbench {tb_name} has no verilog_code")

            # Stage 6: System Feasibility Check
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 6: System Feasibility Check")
            logger.info("=" * 80)
            stage6_result = self.controller.stage6_system_feasibility(
                stage1_result,
                stage2_result,
                stage5_result,
                target_fpga
            )
            session_data["stages"]["stage6"] = stage6_result
            self._save_stage_output("stage6_system.json", stage6_result)
            
            # Stage 7: Final HOD Approval
            logger.info("\n" + "=" * 80)
            logger.info("STAGE 7: Final HOD Approval")
            logger.info("=" * 80)
            stage7_result = self.controller.stage7_final_approval(
                stage1_result,
                stage2_result,
                stage5_result,
                stage6_result
            )
            session_data["stages"]["stage7"] = stage7_result
            self._save_stage_output("stage7_final_approval.json", stage7_result)
            
            # Save complete session
            self._save_stage_output("complete_session.json", session_data)
            
            # Print summary
            self._print_summary(session_data)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Design flow failed with error: {e}", exc_info=True)
            session_data["error"] = str(e)
            self._save_stage_output("error_session.json", session_data)
            raise
    
    def _save_stage_output(self, filename: str, data: Dict[str, Any]):
        """Save stage output to JSON file"""
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved stage output: {output_path}")
    
    def _print_summary(self, session_data: Dict[str, Any]):
        """Print human-readable summary of design session"""
        print("\n" + "=" * 80)
        print("DESIGN SESSION SUMMARY")
        print("=" * 80)
        print(f"Session ID: {session_data['session_id']}")
        print(f"User Idea: {session_data['user_idea']}")
        print(f"Target FPGA: {session_data.get('target_fpga', 'Not specified')}")
        print("\nStage Results:")
        
        stages = session_data.get("stages", {})
        stage_names = {
            "stage0": "Idea Validation",
            "stage1": "Requirement Freeze",
            "stage2": "Architecture Design",
            "stage3": "Architecture Approval",
            "stage4": "RTL Generation",
            "stage5": "Verification Audit",
            "stage5b": "Testbench Generation",
            "stage6": "System Feasibility",
            "stage7": "Final Approval"
        }
        
        for stage_key, stage_name in stage_names.items():
            if stage_key in stages:
                stage_data = stages[stage_key]
                # Determine success based on the field each stage actually populates
                if stage_key == "stage2":
                    # Architecture design: success if the design has meaningful content
                    block_diagram = stage_data.get("block_diagram")
                    design_overview = stage_data.get("design_overview")
                    success = bool(
                        (isinstance(block_diagram, dict) and block_diagram) or
                        (isinstance(design_overview, str) and design_overview.strip())
                    )
                elif stage_key == "stage5b":
                    # Testbench generation: success if at least one testbench was generated
                    success = bool(stage_data.get("testbenches"))
                elif stage_key == "stage4":
                    # RTL generation: success if at least one module was generated
                    success = bool(stage_data.get("modules"))
                elif stage_key == "stage6":
                    # System feasibility: success if the design is marked feasible
                    success = stage_data.get("feasible", False)
                else:
                    success = bool(stage_data.get("approved") or stage_data.get("passed"))
                status = "✓ PASSED" if success else "✗ FAILED"
                print(f"  {stage_name}: {status}")
        
        # Check if design is complete
        final_approved = stages.get("stage7", {}).get("approved", False)
        
        print("\n" + "=" * 80)
        if final_approved:
            print("✓ DESIGN COMPLETE - RTL is ready for implementation")
            print(f"Output directory: {self.output_dir}")
        else:
            print("✗ DESIGN INCOMPLETE - Review stage outputs for issues")
        print("=" * 80)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="FPGA AI Design Bot - Multi-role AI orchestration for Verilog generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic design
  python main.py "UART transmitter with 8-bit data, 115200 baud"
  
  # With target FPGA
  python main.py "SPI master controller" --target ice40
  
  # From specification file
  python main.py --spec examples/sample_spec.json
        """
    )
    
    parser.add_argument(
        "idea",
        nargs="?",
        help="High-level design idea or description"
    )
    
    parser.add_argument(
        "--spec",
        type=str,
        help="Path to JSON specification file"
    )
    
    parser.add_argument(
        "--target",
        type=str,
        choices=["ice40", "ecp5", "gowin", "xilinx", "altera"],
        help="Target FPGA family"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config.py",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = Config()
    
    # Get design idea
    if args.spec:
        with open(args.spec, 'r') as f:
            spec_data = json.load(f)
            idea = spec_data.get("idea") or spec_data.get("description")
            target = spec_data.get("target_fpga", args.target)
    elif args.idea:
        idea = args.idea
        target = args.target
    else:
        parser.error("Either provide an idea or --spec file")
    
    # Create and run bot
    bot = FPGADesignBot(config)
    
    try:
        results = bot.run_design_flow(idea, target)
        sys.exit(0 if results.get("stages", {}).get("stage7", {}).get("approved") else 1)
    except KeyboardInterrupt:
        logger.info("Design flow interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Design flow failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

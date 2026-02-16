"""
Toolchain Validator
Integrates with FPGA toolchain utilities for validation
"""

import logging
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import Config

logger = logging.getLogger(__name__)


class ToolchainValidator:
    """Validates Verilog RTL using FPGA toolchain tools"""
    
    def __init__(self, config: Config):
        self.config = config
        self.available_tools = config.get_available_tools()
        logger.info(f"Available toolchain tools: {self.available_tools}")
    
    def validate_rtl(
        self,
        verilog_code: str,
        module_name: str,
        target_fpga: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive RTL validation
        
        Args:
            verilog_code: Verilog source code
            module_name: Top module name
            target_fpga: Optional FPGA target
            
        Returns:
            Validation results with errors and warnings
        """
        results = {
            "module_name": module_name,
            "passed": True,
            "checks": {}
        }
        
        # Create temporary file for Verilog code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.v',
            delete=False
        ) as f:
            f.write(verilog_code)
            verilog_file = f.name
        
        try:
            # Run lint check
            if self.config.enable_lint_check and self.available_tools.get("verilator"):
                lint_result = self.run_verilator_lint(verilog_file, module_name)
                results["checks"]["lint"] = lint_result
                if not lint_result["passed"]:
                    results["passed"] = False
            
            # Run synthesis check
            if self.config.enable_synthesis_check and self.available_tools.get("yosys"):
                synth_result = self.run_yosys_synthesis(verilog_file, module_name)
                results["checks"]["synthesis"] = synth_result
                if not synth_result["passed"]:
                    results["passed"] = False
            
            # Optional: Formal verification readiness (just check syntax)
            if self.config.enable_formal_verification and self.available_tools.get("sby"):
                formal_result = self.check_formal_readiness(verilog_code)
                results["checks"]["formal_readiness"] = formal_result
            
        finally:
            # Clean up temp file
            Path(verilog_file).unlink(missing_ok=True)
        
        return results
    
    def run_verilator_lint(
        self,
        verilog_file: str,
        top_module: str
    ) -> Dict[str, Any]:
        """
        Run Verilator lint check
        
        Args:
            verilog_file: Path to Verilog file
            top_module: Top module name
            
        Returns:
            Lint check results
        """
        if not self.available_tools.get("verilator"):
            return {
                "passed": True,
                "skipped": True,
                "reason": "Verilator not available"
            }
        
        # Build command - older Verilator versions don't support --top-module
        cmd = [
            self.config.verilator_path,
            "--lint-only",
            "-Wall",
            verilog_file
        ]
        
        logger.info(f"Running Verilator lint: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Verilator returns 0 on success
            passed = result.returncode == 0
            
            errors = []
            warnings = []
            
            # Parse output for errors and warnings
            output = result.stderr + result.stdout
            for line in output.split('\n'):
                if '%Error' in line:
                    errors.append(line.strip())
                elif '%Warning' in line:
                    warnings.append(line.strip())
            
            return {
                "passed": passed,
                "errors": errors,
                "warnings": warnings,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "errors": ["Verilator lint timed out"],
                "warnings": [],
                "timeout": True
            }
        except Exception as e:
            logger.error(f"Verilator lint failed: {e}")
            return {
                "passed": False,
                "errors": [str(e)],
                "warnings": []
            }
    
    def run_yosys_synthesis(
        self,
        verilog_file: str,
        top_module: str
    ) -> Dict[str, Any]:
        """
        Run Yosys synthesis check
        
        Args:
            verilog_file: Path to Verilog file
            top_module: Top module name
            
        Returns:
            Synthesis check results
        """
        if not self.available_tools.get("yosys"):
            return {
                "passed": True,
                "skipped": True,
                "reason": "Yosys not available"
            }
        
        # Create Yosys script
        script = f"""
read_verilog {verilog_file}
hierarchy -check -top {top_module}
proc
opt
check
"""
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.ys',
            delete=False
        ) as f:
            f.write(script)
            script_file = f.name
        
        try:
            cmd = [self.config.yosys_path, "-s", script_file]
            
            logger.info(f"Running Yosys synthesis check: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Yosys returns 0 on success
            passed = result.returncode == 0
            
            errors = []
            warnings = []
            
            # Parse output
            output = result.stderr + result.stdout
            for line in output.split('\n'):
                if 'ERROR' in line.upper():
                    errors.append(line.strip())
                elif 'WARNING' in line.upper():
                    warnings.append(line.strip())
            
            # Extract statistics if successful
            stats = self._parse_yosys_stats(output)
            
            return {
                "passed": passed,
                "errors": errors,
                "warnings": warnings,
                "statistics": stats,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "errors": ["Yosys synthesis timed out"],
                "warnings": [],
                "timeout": True
            }
        except Exception as e:
            logger.error(f"Yosys synthesis failed: {e}")
            return {
                "passed": False,
                "errors": [str(e)],
                "warnings": []
            }
        finally:
            Path(script_file).unlink(missing_ok=True)
    
    def _parse_yosys_stats(self, output: str) -> Dict[str, Any]:
        """Parse Yosys statistics from output"""
        stats = {}
        
        # Look for cell counts
        cell_pattern = r'Number of cells:\s+(\d+)'
        match = re.search(cell_pattern, output)
        if match:
            stats['num_cells'] = int(match.group(1))
        
        # Look for wire counts
        wire_pattern = r'Number of wires:\s+(\d+)'
        match = re.search(wire_pattern, output)
        if match:
            stats['num_wires'] = int(match.group(1))
        
        return stats
    
    def check_formal_readiness(self, verilog_code: str) -> Dict[str, Any]:
        """
        Check if code has formal verification properties
        
        Args:
            verilog_code: Verilog source code
            
        Returns:
            Formal readiness check results
        """
        has_assert = 'assert' in verilog_code
        has_assume = 'assume' in verilog_code
        has_cover = 'cover' in verilog_code
        
        formal_properties = has_assert or has_assume or has_cover
        
        return {
            "passed": True,  # This is just informational
            "has_properties": formal_properties,
            "has_assert": has_assert,
            "has_assume": has_assume,
            "has_cover": has_cover,
            "message": "Contains formal properties" if formal_properties else "No formal properties found"
        }
    
    def extract_errors_for_llm(self, validation_results: Dict[str, Any]) -> str:
        """
        Format validation errors for LLM feedback
        
        Args:
            validation_results: Results from validate_rtl
            
        Returns:
            Formatted error message for LLM
        """
        error_messages = []
        
        for check_name, check_result in validation_results.get("checks", {}).items():
            if not check_result.get("passed", True) and not check_result.get("skipped", False):
                error_messages.append(f"\n{check_name.upper()} ERRORS:")
                
                for error in check_result.get("errors", []):
                    error_messages.append(f"  - {error}")
                
                if check_result.get("warnings"):
                    error_messages.append(f"\n{check_name.upper()} WARNINGS:")
                    for warning in check_result.get("warnings", []):
                        error_messages.append(f"  - {warning}")
        
        return "\n".join(error_messages) if error_messages else "No errors found"
    
    def validate_multiple_modules(
        self,
        modules: List[Dict[str, str]],
        target_fpga: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Validate multiple Verilog modules
        
        Args:
            modules: List of dicts with 'module_name'/'name' and 'verilog_code'/'code'
            target_fpga: Optional FPGA target
            
        Returns:
            List of validation results for each module
        """
        results = []
        
        for module in modules:
            # Handle different possible field names
            module_name = module.get("module_name") or module.get("name") or "unknown"
            verilog_code = module.get("verilog_code") or module.get("code") or module.get("verilog")
            
            if not verilog_code:
                logger.error(f"Module {module_name} has no verilog code")
                results.append({
                    "module_name": module_name,
                    "passed": False,
                    "checks": {},
                    "error": "No verilog code provided"
                })
                continue
            
            logger.info(f"Validating module: {module_name}")
            
            result = self.validate_rtl(verilog_code, module_name, target_fpga)
            results.append(result)
        
        return results

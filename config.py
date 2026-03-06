"""
Configuration for FPGA AI Design Bot
Manages API keys, model selection, and system parameters
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration for FPGA design bot"""
    
    # API Configuration
    groq_api_key: str = ""
    groq_api_base: str = "https://api.groq.com/openai/v1"
    
    # Model Selection per Role
    # Available models: llama-3.3-70b-versatile, llama-3.1-70b-versatile, 
    #                   mixtral-8x7b-32768, gemma2-9b-it
    hod_model: str = "llama-3.3-70b-versatile"
    architecture_model: str = "llama-3.3-70b-versatile"
    rtl_model: str = "llama-3.3-70b-versatile"
    verification_model: str = "llama-3.3-70b-versatile"
    system_model: str = "llama-3.1-8b-instant"
    
    # Model Parameters
    temperature: float = 0.1  # Low temperature for deterministic outputs
    max_tokens: int = 8192
    
    # Rate Limit Handling
    max_api_retries: int = 10  # Max retries for rate limits
    rate_limit_retry_delay: float = 1.0  # Base delay for exponential backoff
    auto_wait_on_rate_limit: bool = True  # Auto-wait when rate limited
    
    # Workflow Parameters
    max_verification_iterations: int = 12
    enable_formal_verification: bool = True
    enable_synthesis_check: bool = True
    enable_lint_check: bool = True
    
    # Toolchain Paths (auto-detected or configured)
    yosys_path: Optional[str] = None
    verilator_path: Optional[str] = None
    sby_path: Optional[str] = None
    nextpnr_ice40_path: Optional[str] = None
    nextpnr_ecp5_path: Optional[str] = None
    
    # Output Configuration
    save_intermediate_outputs: bool = True
    verbose_logging: bool = True
    
    def __post_init__(self):
        """Load API key from environment if not set"""
        if not self.groq_api_key:
            self.groq_api_key = os.getenv("GROQ_API_KEY", "")
            
        if not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Please set it in environment or config:\n"
                "  export GROQ_API_KEY='your-api-key-here'\n"
                "  Or pass it to Config(groq_api_key='...')"
            )
        
        # Auto-detect toolchain paths if not set
        if self.yosys_path is None:
            self.yosys_path = self._find_executable("yosys")
        if self.verilator_path is None:
            self.verilator_path = self._find_executable("verilator")
        if self.sby_path is None:
            self.sby_path = self._find_executable("sby")
        if self.nextpnr_ice40_path is None:
            self.nextpnr_ice40_path = self._find_executable("nextpnr-ice40")
        if self.nextpnr_ecp5_path is None:
            self.nextpnr_ecp5_path = self._find_executable("nextpnr-ecp5")
    
    @staticmethod
    def _find_executable(name: str) -> Optional[str]:
        """Find executable in PATH"""
        import shutil
        return shutil.which(name)
    
    def get_model_for_role(self, role: str) -> str:
        """Get model name for specific role"""
        role_models = {
            "hod": self.hod_model,
            "architecture": self.architecture_model,
            "rtl": self.rtl_model,
            "verification": self.verification_model,
            "system": self.system_model
        }
        return role_models.get(role.lower(), self.hod_model)
    
    def has_toolchain(self, tool: str) -> bool:
        """Check if specific toolchain tool is available"""
        tool_paths = {
            "yosys": self.yosys_path,
            "verilator": self.verilator_path,
            "sby": self.sby_path,
            "nextpnr-ice40": self.nextpnr_ice40_path,
            "nextpnr-ecp5": self.nextpnr_ecp5_path
        }
        path = tool_paths.get(tool)
        return path is not None and os.path.exists(path)
    
    def get_available_tools(self) -> dict:
        """Return dict of available toolchain tools"""
        return {
            "yosys": self.has_toolchain("yosys"),
            "verilator": self.has_toolchain("verilator"),
            "sby": self.has_toolchain("sby"),
            "nextpnr-ice40": self.has_toolchain("nextpnr-ice40"),
            "nextpnr-ecp5": self.has_toolchain("nextpnr-ecp5")
        }

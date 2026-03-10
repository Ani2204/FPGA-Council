"""
Roles Package
Multi-role AI system for FPGA design
"""

from . import hod
from . import architecture
from . import rtl
from . import verification
from . import system_role
from . import testbench

__all__ = ['hod', 'architecture', 'rtl', 'verification', 'system_role', 'testbench']

# FPGA AI Design Bot

A production-grade multi-role AI orchestration system for designing synthesizable Verilog hardware. Uses specialized AI roles to automate the complete design flow from concept to verified RTL.

## Overview

This system orchestrates five specialized AI roles through a gated, stage-based workflow:

1. **HOD (Head of Design)** - Master controller and decision gatekeeper
2. **Architecture** - Block diagrams, FSMs, interfaces (no code)
3. **RTL** - Synthesizable Verilog generation
4. **Verification** - RTL audit and automated fixes
5. **System** - FPGA feasibility and resource analysis

## Features

- ✅ Multi-model routing via Groq API (Llama 3.3 70B, Mixtral, etc.)
- ✅ Deterministic 8-stage workflow with approval gates
- ✅ Automatic toolchain integration (Yosys, Verilator, SymbiYosys)
- ✅ Error feedback loop with automated RTL fixes
- ✅ Structured JSON outputs at every stage
- ✅ Production-quality code generation
- ✅ Complete design session logging

## Requirements

### System Requirements
- Ubuntu 24 (or compatible Linux)
- Python 3.10+
- FPGA toolchain (optional but recommended):
  - Yosys (synthesis check)
  - Verilator (lint check)
  - SymbiYosys (formal verification readiness)

### Python Dependencies
```bash
pip install requests
```

### API Requirements
- Groq API key (get from https://console.groq.com)

## Installation

1. Clone or extract the project:
```bash
cd fpga_ai_bot
```

2. Install FPGA toolchain (optional):
```bash
# Ubuntu/Debian
sudo apt-get install yosys verilator

# For SymbiYosys (formal verification)
sudo apt-get install symbiyosys
```

3. Set up API key:
```bash
export GROQ_API_KEY='your-api-key-here'
```

Or add to your `~/.bashrc` or `~/.profile`:
```bash
echo 'export GROQ_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Quick Start

### Basic Usage

```bash
# Simple design from command line
python main.py "UART transmitter with 8-bit data, 115200 baud"

# With target FPGA specified
python main.py "SPI master controller" --target ice40

# From specification file
python main.py --spec examples/sample_spec.json
```

### Example Session

```bash
python main.py "Design a debouncer for a push button with 10ms debounce time"
```

The system will:
1. Validate the idea and gather constraints
2. Freeze numeric requirements
3. Design architecture (blocks, FSMs)
4. Get HOD approval for architecture
5. Generate Verilog RTL
6. Run verification with toolchain (Yosys, Verilator)
7. Auto-fix any synthesis/lint errors (up to 3 iterations)
8. Check FPGA feasibility
9. Get final HOD approval

### Output Location

All outputs are saved to `outputs/YYYYMMDD_HHMMSS/`:
- `stage0_validation.json` - Idea validation results
- `stage1_requirements.json` - Frozen requirements
- `stage2_architecture.json` - Architecture design
- `stage3_approval.json` - Architecture approval
- `stage4_rtl.json` - Generated RTL
- `*.v` - Verilog source files
- `stage5_verification.json` - Verification results
- `*_verified.v` - Verified Verilog files
- `stage6_system.json` - Feasibility analysis
- `stage7_final_approval.json` - Final approval
- `complete_session.json` - Complete session data

## Project Structure

```
fpga_ai_bot/
├── main.py                 # CLI entry point
├── config.py              # Configuration and API settings
├── llm_router.py          # Groq API integration
├── toolchain.py           # FPGA toolchain integration
├── stage_controller.py    # Stage orchestration engine
├── roles/                 # AI role implementations
│   ├── __init__.py
│   ├── hod.py            # Head of Design role
│   ├── architecture.py   # Architecture role
│   ├── rtl.py            # RTL generation role
│   ├── verification.py   # Verification role
│   └── system_role.py    # System feasibility role
├── prompts/              # Prompt templates for each role
│   ├── hod.txt
│   ├── arch.txt
│   ├── rtl.txt
│   ├── verify.txt
│   └── system.txt
├── examples/             # Example specifications
│   └── sample_spec.json
├── outputs/              # Generated outputs (created at runtime)
└── logs/                 # Log files (created at runtime)
```

## Workflow Stages

### Stage 0: Idea Validation
- HOD validates feasibility
- Gathers all technical constraints
- Single-batch question collection

### Stage 1: Requirement Freeze
- HOD creates frozen specification
- Defines exact numeric parameters
- Sets clock specs, interfaces, timing

### Stage 2: Architecture Design
- Architecture role designs block diagram
- Creates FSM definitions
- Specifies all interfaces
- **No code generation**

### Stage 3: Architecture Approval
- HOD reviews architecture
- Checks requirement compliance
- Gate: Must pass to proceed

### Stage 4: RTL Generation
- RTL role generates Verilog
- Follows architecture exactly
- Synthesizable code only

### Stage 5: Verification Audit
- Runs Yosys synthesis check
- Runs Verilator lint check
- Verification role audits RTL
- **Auto-fix loop** (up to 3 iterations)
- Gate: Must pass to proceed

### Stage 6: System Feasibility
- System role estimates resources
- Analyzes timing feasibility
- Provides risk assessment
- Recommends FPGA families

### Stage 7: Final Approval
- HOD final GO/NO-GO decision
- Reviews complete design flow
- Production readiness check

## Configuration

Edit `config.py` to customize:

```python
# Model selection per role
hod_model = "llama-3.3-70b-versatile"
architecture_model = "llama-3.3-70b-versatile"
rtl_model = "llama-3.3-70b-versatile"
verification_model = "llama-3.3-70b-versatile"
system_model = "llama-3.1-70b-versatile"

# Workflow parameters
max_verification_iterations = 3
enable_formal_verification = True
enable_synthesis_check = True
enable_lint_check = True
```

## Advanced Usage

### Custom Specifications

Create a JSON specification file:

```json
{
  "idea": "Your design description",
  "target_fpga": "ice40",
  "constraints": {
    "clock_frequency_mhz": 50,
    "data_width": 16
  },
  "interfaces": [...],
  "requirements": {...}
}
```

Run with:
```bash
python main.py --spec my_design.json
```

### Debug Mode

Enable verbose logging:
```bash
python main.py "design description" --debug
```

### Multiple Designs

The system creates a new timestamped directory for each session, so you can run multiple designs without conflicts.

## Toolchain Integration

### Yosys (Synthesis Check)
- Validates synthesizability
- Checks for common errors
- Provides resource estimates

### Verilator (Lint Check)
- Catches common RTL bugs
- Warns about coding issues
- Ensures best practices

### SymbiYosys (Formal Verification)
- Checks for formal properties
- Validates assertions
- Optional - used if available

### Without Toolchain
The system works without toolchain tools installed, but verification stage will skip automated checks. You'll still get RTL code generated.

## Error Handling

### Automatic Fix Loop
If toolchain finds errors:
1. Verification role analyzes errors
2. Generates fixed Verilog
3. Re-runs toolchain validation
4. Repeats up to `max_verification_iterations` times

### Stage Gating
If any stage fails:
- Workflow stops
- Outputs saved to that point
- User can review and retry

## Best Practices

### For Best Results
1. Be specific in your design description
2. Include numeric constraints (clock freq, data width, etc.)
3. Specify target FPGA if known
4. Review stage outputs as they complete
5. Use the examples as templates

### Design Complexity
- Simple: Single module, basic FSM (< 2 minutes)
- Medium: Multiple modules, complex FSM (2-5 minutes)
- Complex: Multiple FSMs, clock domains (5-10 minutes)

### Resource Usage
- Each stage requires 1-3 API calls
- Complete flow: ~15-25 API calls
- Cost: ~$0.10-0.30 per design (with Groq)

## Troubleshooting

### API Key Issues
```
ValueError: GROQ_API_KEY not set
```
Solution: Set environment variable or edit config.py

### Toolchain Not Found
```
Warning: Yosys not available
```
Solution: Install toolchain or disable checks in config.py

### Verification Fails
Check `outputs/*/stage5_verification.json` for error details.
The system attempts auto-fix, but complex errors may need manual review.

### Module Not Found
```
ImportError: No module named 'requests'
```
Solution: `pip install requests`

## Examples

### Example 1: UART Transmitter
```bash
python main.py "UART transmitter, 115200 baud, 8N1 format, with 16-deep FIFO"
```

### Example 2: SPI Master
```bash
python main.py "SPI master controller, 4MHz clock, mode 0, 8-bit transfers" --target ice40
```

### Example 3: From Spec File
```bash
python main.py --spec examples/sample_spec.json
```

## Output Files

### Verilog Files
- `<module_name>.v` - Original generated RTL
- `<module_name>_verified.v` - Verified, lint-clean RTL

### JSON Files
All stage outputs in structured JSON format for downstream processing.

### Logs
- `logs/fpga_bot.log` - Complete execution log with all API calls and decisions

## Contributing

This is production-grade code. Contributions should maintain:
- Role separation (no authority overlap)
- Stage gating enforcement
- Synthesizable code standards
- Comprehensive error handling

## License

This project is provided as-is for FPGA design automation.

## Support

For issues:
1. Check logs in `logs/fpga_bot.log`
2. Review stage outputs in `outputs/*/`
3. Verify API key is set correctly
4. Ensure toolchain is installed (if using)

## Limitations

- Designs must be describable in single-session context
- Very large designs (>10K lines) may need manual breakdown
- Formal verification is readiness check only (not full formal proof)
- Resource estimates are approximations

## Performance

Typical execution times:
- Idea validation: 10-30s
- Architecture design: 30-60s
- RTL generation: 30-90s
- Verification: 20-60s per iteration
- Total: 3-10 minutes for complete flow

## Future Enhancements

Potential additions:
- Testbench generation
- Formal property generation
- Multi-file project support
- Interactive clarification mode
- Custom role additions
- Integration with version control

---

**Ready to design FPGA hardware with AI?**

```bash
python main.py "Your design idea here"
```

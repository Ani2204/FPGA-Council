#!/bin/bash
# Setup script for FPGA AI Design Bot

echo "=================================="
echo "FPGA AI Design Bot - Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python 3 not found. Please install Python 3.10 or later."
    exit 1
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python dependencies."
    exit 1
fi

# Check for GROQ_API_KEY
echo ""
echo "Checking for GROQ_API_KEY..."
if [ -z "$GROQ_API_KEY" ]; then
    echo "WARNING: GROQ_API_KEY environment variable not set."
    echo "Please set it with:"
    echo "  export GROQ_API_KEY='your-api-key-here'"
    echo ""
    echo "Or add to ~/.bashrc:"
    echo "  echo 'export GROQ_API_KEY=\"your-key\"' >> ~/.bashrc"
    echo "  source ~/.bashrc"
else
    echo "✓ GROQ_API_KEY is set"
fi

# Check for FPGA toolchain
echo ""
echo "Checking for FPGA toolchain..."
TOOLS_FOUND=0

if command -v yosys &> /dev/null; then
    echo "✓ Yosys found: $(yosys -V | head -1)"
    TOOLS_FOUND=$((TOOLS_FOUND + 1))
else
    echo "  Yosys not found (optional - used for synthesis checking)"
fi

if command -v verilator &> /dev/null; then
    echo "✓ Verilator found: $(verilator --version | head -1)"
    TOOLS_FOUND=$((TOOLS_FOUND + 1))
else
    echo "  Verilator not found (optional - used for lint checking)"
fi

if command -v sby &> /dev/null; then
    echo "✓ SymbiYosys found"
    TOOLS_FOUND=$((TOOLS_FOUND + 1))
else
    echo "  SymbiYosys not found (optional - used for formal verification)"
fi

if [ $TOOLS_FOUND -eq 0 ]; then
    echo ""
    echo "NOTE: No FPGA toolchain tools found."
    echo "The system will work without them, but verification will be limited."
    echo ""
    echo "To install on Ubuntu/Debian:"
    echo "  sudo apt-get install yosys verilator symbiyosys"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs
mkdir -p outputs
echo "✓ Directories created"

# Make main.py executable
chmod +x main.py

echo ""
echo "=================================="
echo "Setup complete!"
echo "=================================="
echo ""
echo "Quick start:"
echo "  python main.py \"UART transmitter with 8-bit data, 115200 baud\""
echo ""
echo "For more examples, see README.md"
echo ""

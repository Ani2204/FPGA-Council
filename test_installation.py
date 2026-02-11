#!/usr/bin/env python3
"""
Test script for FPGA AI Design Bot
Verifies installation and basic functionality
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        import config
        import llm_router
        import toolchain
        import stage_controller
        from roles import hod, architecture, rtl, verification, system_role
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    try:
        from config import Config
        
        # Try without API key first
        os.environ.pop('GROQ_API_KEY', None)
        try:
            cfg = Config()
            print("✗ Config should require API key")
            return False
        except ValueError as e:
            print(f"✓ Config correctly requires API key")
        
        # Set test API key
        os.environ['GROQ_API_KEY'] = 'test-key-123'
        cfg = Config()
        
        assert cfg.groq_api_key == 'test-key-123'
        assert cfg.hod_model is not None
        assert cfg.max_verification_iterations > 0
        
        print("✓ Configuration working correctly")
        
        # Check toolchain detection
        available = cfg.get_available_tools()
        print(f"  Available tools: {available}")
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\nTesting file structure...")
    
    required_files = [
        "main.py",
        "config.py",
        "llm_router.py",
        "toolchain.py",
        "stage_controller.py",
        "roles/__init__.py",
        "roles/hod.py",
        "roles/architecture.py",
        "roles/rtl.py",
        "roles/verification.py",
        "roles/system_role.py",
        "prompts/hod.txt",
        "prompts/arch.txt",
        "prompts/rtl.txt",
        "prompts/verify.txt",
        "prompts/system.txt",
        "examples/sample_spec.json",
        "README.md",
        "requirements.txt"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"✗ Missing files: {missing}")
        return False
    
    print(f"✓ All {len(required_files)} required files present")
    return True

def test_directories():
    """Test that required directories exist or can be created"""
    print("\nTesting directories...")
    
    required_dirs = ["logs", "outputs", "examples", "prompts", "roles"]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            print(f"  Creating {dir_name}/")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    print("✓ All directories ready")
    return True

def test_prompt_loading():
    """Test that prompts can be loaded"""
    print("\nTesting prompt loading...")
    
    from pathlib import Path
    
    prompts = ["hod", "arch", "rtl", "verify", "system"]
    
    for prompt_name in prompts:
        prompt_path = Path("prompts") / f"{prompt_name}.txt"
        if not prompt_path.exists():
            print(f"✗ Missing prompt: {prompt_path}")
            return False
        
        content = prompt_path.read_text()
        if len(content) < 50:
            print(f"✗ Prompt too short: {prompt_path}")
            return False
    
    print(f"✓ All {len(prompts)} prompts loaded successfully")
    return True

def test_example_specs():
    """Test that example specs are valid JSON"""
    print("\nTesting example specifications...")
    
    import json
    
    examples = list(Path("examples").glob("*.json"))
    
    for example in examples:
        try:
            with open(example) as f:
                data = json.load(f)
            
            if "idea" not in data:
                print(f"✗ Example missing 'idea': {example}")
                return False
            
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in {example}: {e}")
            return False
    
    print(f"✓ All {len(examples)} example specifications valid")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("FPGA AI Design Bot - Installation Test")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Directories", test_directories),
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("Prompt Loading", test_prompt_loading),
        ("Example Specs", test_example_specs)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nQuick start:")
        print('  python main.py "UART transmitter with 8-bit data"')
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

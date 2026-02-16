#!/usr/bin/env python3
"""
Stage 5 Diagnostic Tool
Analyzes verification failures and shows what errors remain
"""

import json
import sys
from pathlib import Path

def analyze_stage5(session_dir):
    """Analyze Stage 5 verification results"""
    
    stage5_file = Path(session_dir) / "stage5_verification.json"
    
    if not stage5_file.exists():
        print(f"Error: {stage5_file} not found")
        return
    
    with open(stage5_file) as f:
        data = json.load(f)
    
    print("=" * 80)
    print("STAGE 5 VERIFICATION ANALYSIS")
    print("=" * 80)
    
    passed = data.get("passed", False)
    iterations = data.get("iterations", 0)
    max_iter = data.get("max_iterations", 0)
    
    print(f"\nResult: {'✓ PASSED' if passed else '✗ FAILED'}")
    print(f"Iterations: {iterations}/{max_iter}")
    
    # Show final validation results
    final_val = data.get("final_validation", [])
    
    if final_val:
        print(f"\n{'=' * 80}")
        print("FINAL VALIDATION RESULTS")
        print("=" * 80)
        
        for i, module_val in enumerate(final_val):
            module_name = module_val.get("module_name", f"Module {i}")
            module_passed = module_val.get("passed", False)
            
            print(f"\nModule: {module_name}")
            print(f"Passed: {'✓ YES' if module_passed else '✗ NO'}")
            
            checks = module_val.get("checks", {})
            
            # Lint results
            if "lint" in checks:
                lint = checks["lint"]
                print(f"\n  Verilator Lint:")
                print(f"    Passed: {lint.get('passed', False)}")
                
                errors = lint.get("errors", [])
                if errors:
                    print(f"    Errors ({len(errors)}):")
                    for err in errors[:5]:  # Show first 5
                        print(f"      • {err}")
                    if len(errors) > 5:
                        print(f"      ... and {len(errors) - 5} more")
                
                warnings = lint.get("warnings", [])
                if warnings:
                    print(f"    Warnings ({len(warnings)}):")
                    for warn in warnings[:3]:
                        print(f"      • {warn}")
                    if len(warnings) > 3:
                        print(f"      ... and {len(warnings) - 3} more")
            
            # Synthesis results
            if "synthesis" in checks:
                synth = checks["synthesis"]
                print(f"\n  Yosys Synthesis:")
                print(f"    Passed: {synth.get('passed', False)}")
                
                errors = synth.get("errors", [])
                if errors:
                    print(f"    Errors ({len(errors)}):")
                    for err in errors[:5]:
                        print(f"      • {err}")
                    if len(errors) > 5:
                        print(f"      ... and {len(errors) - 5} more")
    
    # Show iteration history
    audit_history = data.get("audit_history", [])
    
    if audit_history:
        print(f"\n{'=' * 80}")
        print("ITERATION HISTORY")
        print("=" * 80)
        
        for hist in audit_history:
            iter_num = hist.get("iteration", "?")
            print(f"\nIteration {iter_num}:")
            
            # Show what errors were found
            val_results = hist.get("validation_results", [])
            if val_results:
                for vr in val_results:
                    if not vr.get("passed", False):
                        print("  Found issues:")
                        
                        checks = vr.get("checks", {})
                        if "lint" in checks and not checks["lint"].get("passed"):
                            errors = checks["lint"].get("errors", [])
                            print(f"    Lint errors: {len(errors)}")
                        
                        if "synthesis" in checks and not checks["synthesis"].get("passed"):
                            errors = checks["synthesis"].get("errors", [])
                            print(f"    Synthesis errors: {len(errors)}")
            
            # Show if fixes were provided
            audit = hist.get("audit", {})
            has_issues = audit.get("has_issues", False)
            fixed_modules = audit.get("fixed_modules", [])
            
            print(f"  Verification recognized issues: {has_issues}")
            print(f"  Provided fixes: {len(fixed_modules)} modules")
    
    # Recommendations
    print(f"\n{'=' * 80}")
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if not passed:
        print("\nStage 5 failed to converge after 3 iterations.")
        print("\nPossible actions:")
        print("  1. Increase max_verification_iterations in config.py")
        print("  2. Check the generated Verilog manually")
        print("  3. Look at the specific errors above")
        print("  4. Try a simpler design first")
        
        if final_val:
            print("\nTo see the actual Verilog code:")
            print(f"  cat {session_dir}/uart_transmitter.v")
    else:
        print("\n✓ Stage 5 passed! Verification successful.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Find most recent session
        outputs_dir = Path("outputs")
        if outputs_dir.exists():
            sessions = sorted(outputs_dir.iterdir(), key=lambda x: x.name, reverse=True)
            if sessions:
                session_dir = sessions[0]
                print(f"Analyzing most recent session: {session_dir.name}")
                analyze_stage5(session_dir)
            else:
                print("No sessions found in outputs/")
        else:
            print("Usage: python diagnose_stage5.py <session_dir>")
            print("  e.g., python diagnose_stage5.py outputs/20260216_114112")
    else:
        analyze_stage5(sys.argv[1])

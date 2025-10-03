#!/usr/bin/env python3
"""
Asset file validation tests

Usage: python tests/test_assets.py
"""

import json
import sys
import struct
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

try:
    from proxy_urls import WalletProxyProcessor
except ImportError as e:
    print(f"ERROR: Cannot import proxy_urls module: {e}")
    sys.exit(1)


def test(condition, message):
    """Simple test function - pass/fail with message."""
    if condition:
        print(f"PASS: {message}")
        return True
    else:
        print(f"FAIL: {message}")
        return False


def validate_png_file(file_path):
    """Validate PNG file format and dimensions using only standard library."""
    try:
        with open(file_path, 'rb') as f:
            # Check PNG signature
            header = f.read(8)
            if header != b'\x89PNG\r\n\x1a\n':
                return False, "Not a valid PNG file"
            
            # Read IHDR chunk to get dimensions
            f.read(4)  # chunk length
            chunk_type = f.read(4)
            if chunk_type != b'IHDR':
                return False, "Invalid PNG header"
            
            # Read width and height (4 bytes each, big-endian)
            width_bytes = f.read(4)
            height_bytes = f.read(4)
            width = struct.unpack('>I', width_bytes)[0]
            height = struct.unpack('>I', height_bytes)[0]
            
            return True, f"{width}×{height}"
    except Exception as e:
        return False, f"Error reading file: {e}"


def test_asset_files():
    """Test that all required asset files exist."""
    
    passed = 0
    failed = 0
    warnings = 0
    problems = []
    warning_problems = []
    
    # Check if size validation is disabled
    skip_size_check = os.getenv('SKIP_PNG_SIZE_CHECK', '').lower() in ('1', 'true', 'yes')
    # Check if extra images check is disabled (warnings instead of errors)
    skip_extra_images_check = os.getenv('SKIP_EXTRA_IMAGES_CHECK', '').lower() in ('1', 'true', 'yes')
    
    def check(condition, message, problem=None, is_warning=False):
        nonlocal passed, failed, warnings
        if test(condition, message):
            passed += 1
        else:
            if is_warning:
                warnings += 1
                if problem:
                    warning_problems.append(problem)
            else:
                failed += 1
                if problem:
                    problems.append(problem)
    
    print("=" * 50)
    print("ASSET FILES VALIDATION TESTS")
    if skip_size_check:
        print("(PNG size validation disabled)")
    if skip_extra_images_check:
        print("(Extra images check as warnings)")
    print("=" * 50)
    
    # Load wallets data
    try:
        wallets = json.loads(Path("wallets-v2.json").read_text())
    except Exception as e:
        print(f"ERROR: Cannot load wallets-v2.json: {e}")
        return False
    
    # Create processor to use its format_filename method
    processor = WalletProxyProcessor("dummy")
    
    # Get all expected filenames
    expected_files = set()
    
    # Check each wallet asset file
    for wallet in wallets:
        if not isinstance(wallet, dict) or 'app_name' not in wallet:
            continue
            
        app_name = wallet['app_name']
        filename = processor.format_filename(app_name) + '.png'
        expected_files.add(filename)
        file_path = Path("assets") / filename
        
        if not file_path.exists():
            check(False, f"{app_name} -> {filename} (MISSING)", f"CREATE: assets/{filename}")
            continue
        
        # Validate PNG file
        is_valid, info = validate_png_file(file_path)
        if not is_valid:
            check(False, f"{app_name} -> {filename} (INVALID: {info})", f"FIX:    assets/{filename} (invalid: {info})")
        elif not skip_size_check and info != "288×288":
            check(False, f"{app_name} -> {filename} ({info}, should be 288×288)", f"FIX:    assets/{filename} (wrong size: {info})")
        else:
            if skip_size_check and info != "288×288":
                check(True, f"{app_name} -> {filename} ({info}, size check skipped)")
            else:
                check(True, f"{app_name} -> {filename} ({info})")
    
    # Check for unused asset files
    assets_dir = Path("assets")
    if assets_dir.exists():
        for asset_file in assets_dir.glob("*.png"):
            if asset_file.name not in expected_files:
                if skip_extra_images_check:
                    check(False, f"Unused asset file: {asset_file.name}", f"REMOVE: assets/{asset_file.name} (not used by any wallet)", is_warning=True)
                else:
                    check(False, f"Unused asset file: {asset_file.name}", f"REMOVE: assets/{asset_file.name} (not used by any wallet)")
    
    # Show problems
    if problems:
        print(f"\nFiles that need attention:")
        print(f"Format: PNG images, 288×288px, non-transparent background, no rounded corners")
        print()
        for problem in problems:
            print(f"  {problem}")
    
    # Show warnings
    if warning_problems:
        print(f"\nWarning - Files that could be cleaned up:")
        print()
        for problem in warning_problems:
            print(f"  {problem}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"PASSED:   {passed}")
    print(f"FAILED:   {failed}")
    if warnings > 0:
        print(f"WARNINGS: {warnings}")
    print(f"TOTAL:    {passed + failed + warnings}")
    
    if failed == 0:
        if warnings > 0:
            print(f"\nALL TESTS PASSED (with {warnings} warnings)")
        else:
            print("\nALL TESTS PASSED")
        return True
    else:
        print(f"\n{failed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = test_asset_files()
    sys.exit(0 if success else 1)

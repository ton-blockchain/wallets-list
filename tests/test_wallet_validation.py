#!/usr/bin/env python3
"""
Simple wallet validation tests

Usage: python tests/test_wallet_validation.py
"""

import json
import sys
import os
from pathlib import Path
from urllib.parse import urlparse


def test(condition, message):
    """Simple test function - pass/fail with message."""
    if condition:
        print(f"PASS: {message}")
        return True
    else:
        print(f"FAIL: {message}")
        return False


def is_valid_url(url):
    """Check if URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def validate_wallet_file(file_path=None):
    """Validate wallet configuration file."""
    
    # Allow override via environment variable
    if file_path is None:
        file_path = os.getenv('WALLET_FILE', 'wallets-v2.json')
    
    # Load data
    try:
        wallets = json.loads(Path(file_path).read_text())
    except Exception as e:
        print(f"ERROR: Cannot load {file_path}: {e}")
        return False
    
    # Track results
    passed = 0
    failed = 0
    problems = []
    
    def check(condition, message, problem):
        nonlocal passed, failed
        if test(condition, message):
            passed += 1
        else:
            failed += 1
            problems.append(problem)
    
    print("=" * 50)
    print("WALLET VALIDATION TESTS")
    print("=" * 50)
    
    # Basic structure tests
    check(isinstance(wallets, list), "File contains array of wallets", f"FIX: File contains array of wallets")
    check(len(wallets) > 0, f"Found {len(wallets)} wallets", f"FIX: Found {len(wallets)} wallets")
    
    # Required fields for each wallet
    required_fields = {'app_name', 'name', 'image', 'about_url', 'bridge', 'platforms', 'features'}
    valid_platforms = {'ios', 'android', 'chrome', 'firefox', 'safari', 'macos', 'windows', 'linux'}
    
    app_names = []
    image_urls = []
    
    for i, wallet in enumerate(wallets):
        wallet_name = f"Wallet {i+1}"
        
        # Basic wallet structure
        check(isinstance(wallet, dict), f"{wallet_name} is valid object", f"FIX: {wallet_name} - must be valid object")
        
        if not isinstance(wallet, dict):
            continue
            
        app_name = wallet.get('app_name', 'unknown')
        wallet_id = f"{wallet_name} ({app_name})"
        
        # Required fields
        missing = required_fields - set(wallet.keys())
        check(not missing, f"{wallet_id} has required fields", f"FIX: {wallet_id} - add missing fields: {', '.join(missing)}")
        
        # String fields
        for field in ['app_name', 'name', 'image', 'about_url']:
            if field in wallet:
                value = wallet[field]
                check(isinstance(value, str) and value.strip(), f"{wallet_id}.{field} is valid string", f"FIX: {wallet_id}.{field} - must be non-empty string")
        
        # URL fields
        for field in ['image', 'about_url', 'universal_url']:
            if field in wallet:
                check(is_valid_url(wallet[field]), f"{wallet_id}.{field} is valid URL", f"FIX: {wallet_id}.{field} - invalid URL: {wallet[field]}")
        
        # Array fields
        for field in ['bridge', 'platforms', 'features']:
            if field in wallet:
                value = wallet[field]
                check(isinstance(value, list) and len(value) > 0, f"{wallet_id}.{field} is valid array", f"FIX: {wallet_id}.{field} - must be non-empty array")
        
        # Platform validation
        if 'platforms' in wallet and isinstance(wallet['platforms'], list):
            invalid_platforms = set(wallet['platforms']) - valid_platforms
            check(not invalid_platforms, f"{wallet_id} has valid platforms", f"FIX: {wallet_id}.platforms - invalid platforms: {', '.join(invalid_platforms)}")
        
        # Bridge validation
        bridge_types = []
        if 'bridge' in wallet and isinstance(wallet['bridge'], list):
            for j, bridge in enumerate(wallet['bridge']):
                bridge_id = f"{wallet_id}.bridge[{j}]"
                
                if isinstance(bridge, dict):
                    bridge_type = bridge.get('type')
                    check(bridge_type in ['sse', 'js'], f"{bridge_id} has valid type", f"FIX: {bridge_id} - invalid type: {bridge_type}")
                    
                    # Track bridge types for duplicate check
                    if bridge_type in ['sse', 'js']:
                        bridge_types.append(bridge_type)
                    
                    if bridge_type == 'sse':
                        has_url = 'url' in bridge
                        url_valid = has_url and isinstance(bridge['url'], str) and is_valid_url(bridge['url'])
                        check(has_url, f"{bridge_id} has url field", f"FIX: {bridge_id} - missing url field")
                        if has_url:
                            check(url_valid, f"{bridge_id} has valid URL", f"FIX: {bridge_id} - invalid URL: {bridge.get('url', 'missing')}")
                    elif bridge_type == 'js':
                        has_key = 'key' in bridge
                        key_valid = has_key and isinstance(bridge['key'], str) and bridge['key'].strip()
                        check(has_key, f"{bridge_id} has key field", f"FIX: {bridge_id} - missing key field")
                        if has_key:
                            check(key_valid, f"{bridge_id} has valid key", f"FIX: {bridge_id} - invalid key: {bridge.get('key', 'missing')}")
            
            # Check for duplicate bridge types
            for bridge_type in ['sse', 'js']:
                count = bridge_types.count(bridge_type)
                if count > 1:
                    check(False, f"{wallet_id} has unique {bridge_type} bridge", f"FIX: {wallet_id} - duplicate {bridge_type} bridge (found {count})")
        
        # Feature validation
        has_send_transaction = False
        feature_names = []
        if 'features' in wallet and isinstance(wallet['features'], list):
            for j, feature in enumerate(wallet['features']):
                feature_id = f"{wallet_id}.features[{j}]"
                
                if isinstance(feature, dict):
                    feature_name = feature.get('name')
                    check(feature_name in ['SendTransaction', 'SignData'], f"{feature_id} has valid name", f"FIX: {feature_id} - invalid name: {feature_name}")
                    
                    # Track feature names for duplicate check
                    if feature_name in ['SendTransaction', 'SignData']:
                        feature_names.append(feature_name)
                    
                    if feature_name == 'SendTransaction':
                        has_send_transaction = True
                        
                        # Check maxMessages (required)
                        has_max_msg = 'maxMessages' in feature
                        check(has_max_msg, f"{feature_id} has maxMessages field", f"FIX: {feature_id} - missing maxMessages field")
                        if has_max_msg:
                            max_msg = feature['maxMessages']
                            check(isinstance(max_msg, int) and max_msg > 0, f"{feature_id} has valid maxMessages", f"FIX: {feature_id} - maxMessages must be positive integer: {max_msg}")
                        
                        # Check extraCurrencySupported (required)
                        has_extra_currency = 'extraCurrencySupported' in feature
                        check(has_extra_currency, f"{feature_id} has extraCurrencySupported field", f"FIX: {feature_id} - missing extraCurrencySupported field")
                        if has_extra_currency:
                            extra_currency = feature['extraCurrencySupported']
                            check(isinstance(extra_currency, bool), f"{feature_id} has valid extraCurrencySupported", f"FIX: {feature_id} - extraCurrencySupported must be boolean: {extra_currency}")
                    
                    elif feature_name == 'SignData':
                        # Check types (required for SignData)
                        has_types = 'types' in feature
                        check(has_types, f"{feature_id} has types field", f"FIX: {feature_id} - missing types field")
                        if has_types:
                            types = feature['types']
                            is_valid_types = isinstance(types, list) and len(types) > 0
                            check(is_valid_types, f"{feature_id} has valid types array", f"FIX: {feature_id} - types must be non-empty array")
                            if is_valid_types:
                                valid_types = {'text', 'binary', 'cell'}
                                invalid_types = set(types) - valid_types
                                check(not invalid_types, f"{feature_id} has valid type values", f"FIX: {feature_id} - invalid types: {', '.join(invalid_types)}")
            
            # Check for duplicate feature types
            for feature_name in ['SendTransaction', 'SignData']:
                count = feature_names.count(feature_name)
                if count > 1:
                    check(False, f"{wallet_id} has unique {feature_name} feature", f"FIX: {wallet_id} - duplicate {feature_name} feature (found {count})")
        
        # Check that wallet has SendTransaction feature (required)
        check(has_send_transaction, f"{wallet_id} has SendTransaction feature", f"FIX: {wallet_id} - missing required SendTransaction feature")
        
        # Collect for uniqueness check
        if 'app_name' in wallet:
            app_names.append(wallet['app_name'])
        if 'image' in wallet:
            image_urls.append(wallet['image'])
    
    # Uniqueness tests
    
    duplicates = [name for name in set(app_names) if app_names.count(name) > 1]
    check(len(app_names) == len(set(app_names)), "All app_names are unique", f"FIX: Duplicate app_names found: {', '.join(duplicates)}")
    
    duplicates = [url for url in set(image_urls) if image_urls.count(url) > 1]
    check(len(image_urls) == len(set(image_urls)), "All image URLs are unique", f"FIX: Duplicate image URLs found: {', '.join(duplicates)}")
    
    # Show problems
    if problems:
        print(f"\nIssues that need to be fixed:")
        print()
        for problem in problems:
            print(f"  {problem}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"TOTAL:  {passed + failed}")
    
    if failed == 0:
        print("\nALL TESTS PASSED")
        return True
    else:
        print(f"\n{failed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = validate_wallet_file()
    sys.exit(0 if success else 1)
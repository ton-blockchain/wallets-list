#!/usr/bin/env python3
"""
Simple tests for proxy_urls.py script

Usage: python tests/test_proxy_urls.py
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

try:
    from proxy_urls import WalletProxyProcessor, load_json_file
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


def test_proxy_urls():
    """Test the proxy URL functionality."""
    
    passed = 0
    failed = 0
    
    def check(condition, message):
        nonlocal passed, failed
        if test(condition, message):
            passed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print("PROXY URLS TESTS")
    print("=" * 50)
    
    # Test filename formatting
    processor = WalletProxyProcessor("https://example.com/assets")
    
    # Filename formatting test cases
    test_cases = [
        ("telegram-wallet", "telegram_wallet"),
        ("fintopio-tg", "fintopio_tg"),
        ("Architec.ton", "architec_ton"),
        ("tonkeeper-pro", "tonkeeper_pro"),
        ("BitgetWeb3", "bitgetweb3"),
        ("okxMiniWallet", "okxminiwallet"),
        ("app__with___multiple", "app_with_multiple"),
        ("_leading_underscore_", "leading_underscore"),
        ("UPPERCASE", "uppercase"),
        ("123numeric", "123numeric"),
        ("special!@#$%chars", "special_chars"),
    ]
    
    for input_name, expected in test_cases:
        result = processor.format_filename(input_name)
        check(result == expected, f"Format '{input_name}' -> '{result}' (expected '{expected}')")
    
    # Test wallet processing
    test_wallets = [
        {
            "app_name": "telegram-wallet",
            "name": "Wallet",
            "image": "https://wallet.tg/images/logo-288.png",
            "about_url": "https://wallet.tg/"
        },
        {
            "app_name": "tonkeeper",
            "name": "Tonkeeper",
            "image": "https://tonkeeper.com/assets/tonconnect-icon.png",
            "about_url": "https://tonkeeper.com"
        }
    ]
    
    # Test with proxy processor
    processor = WalletProxyProcessor("https://proxy.example.com/assets")
    processed = processor.process_wallets(test_wallets)
    
    # Check URL replacement
    expected_url1 = "https://proxy.example.com/assets/telegram_wallet.png"
    check(processed[0]["image"] == expected_url1, f"telegram-wallet URL -> {processed[0]['image']}")
    
    expected_url2 = "https://proxy.example.com/assets/tonkeeper.png"
    check(processed[1]["image"] == expected_url2, f"tonkeeper URL -> {processed[1]['image']}")
    
    # Check that other fields are preserved
    check(processed[0]["about_url"] == "https://wallet.tg/", "Other fields preserved")
    check(processed[0]["name"] == "Wallet", "Name field preserved")
    
    # Test base URL handling
    test_wallet = {"app_name": "test", "image": "https://example.com/image.png"}
    
    # Test with trailing slash
    processor1 = WalletProxyProcessor("https://example.com/assets/")
    result1 = processor1.process_wallet(test_wallet)
    expected = "https://example.com/assets/test.png"
    check(result1["image"] == expected, f"Trailing slash handling -> {result1['image']}")
    
    # Test without trailing slash
    processor2 = WalletProxyProcessor("https://example.com/assets")
    result2 = processor2.process_wallet(test_wallet)
    check(result2["image"] == expected, f"No trailing slash handling -> {result2['image']}")
    
    # Test empty app_name handling
    empty_wallet = {"image": "https://example.com/image.png"}
    result3 = processor2.process_wallet(empty_wallet)
    check(result3["image"] == "https://example.com/image.png", "No app_name - image unchanged")
    
    # Test missing image field
    no_image_wallet = {"app_name": "test"}
    result4 = processor2.process_wallet(no_image_wallet)
    check("image" not in result4, "No image field - no image added")
    
    # Test actual JSON file processing
    try:
        # Load original wallets data
        original_wallets = load_json_file("wallets-v2.json")
        check(len(original_wallets) > 0, "Original JSON file loaded successfully")
        
        # Process with proxy URLs
        file_processor = WalletProxyProcessor("https://config.ton.org/assets")
        processed_wallets = file_processor.process_wallets(original_wallets)
        
        check(len(processed_wallets) == len(original_wallets), "Same number of wallets after processing")
        
        # Check each wallet
        image_changes = 0
        field_differences = 0
        
        for i, (original, processed) in enumerate(zip(original_wallets, processed_wallets)):
            # Check that all original fields are preserved
            for field, value in original.items():
                if field == 'image':
                    # Image should be changed if app_name exists
                    if 'app_name' in original:
                        expected_filename = file_processor.format_filename(original['app_name'])
                        expected_url = f"https://config.ton.org/assets/{expected_filename}.png"
                        if processed[field] == expected_url:
                            image_changes += 1
                else:
                    # All other fields should be identical
                    if processed.get(field) != value:
                        field_differences += 1
            
            # Check no new fields were added
            if set(original.keys()) != set(processed.keys()):
                field_differences += 1
        
        check(image_changes == len(original_wallets), f"Image URLs changed for {image_changes} wallets")
        check(field_differences == 0, "No other fields were modified")
        
        # Verify specific examples
        telegram_wallet = next((w for w in processed_wallets if w.get('app_name') == 'telegram-wallet'), None)
        if telegram_wallet:
            expected_image = "https://config.ton.org/assets/telegram_wallet.png"
            check(telegram_wallet['image'] == expected_image, "telegram-wallet has correct proxy URL")
        
        tonkeeper_wallet = next((w for w in processed_wallets if w.get('app_name') == 'tonkeeper'), None)
        if tonkeeper_wallet:
            expected_image = "https://config.ton.org/assets/tonkeeper.png"
            check(tonkeeper_wallet['image'] == expected_image, "tonkeeper has correct proxy URL")
            
            # Check other fields preserved
            original_tonkeeper = next((w for w in original_wallets if w.get('app_name') == 'tonkeeper'), None)
            if original_tonkeeper:
                check(tonkeeper_wallet['name'] == original_tonkeeper['name'], "tonkeeper name field preserved")
                check(tonkeeper_wallet['about_url'] == original_tonkeeper['about_url'], "tonkeeper about_url preserved")
        
    except Exception as e:
        check(False, f"JSON file processing failed: {e}")
    
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
    success = test_proxy_urls()
    sys.exit(0 if success else 1)
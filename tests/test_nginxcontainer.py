#!/usr/bin/env python3
"""
Test script for validating the built Docker image.

This script:
1. Fetches /wallets-v2.json from the running container
2. Extracts all image URLs from the wallet configurations
3. Tests each image URL to ensure it returns a valid PNG
4. Reports test results with detailed feedback

Usage:
    python test_image.py --base-url http://localhost:8080
    python test_image.py --base-url http://localhost:8080 --verbose
    python test_image.py --base-url http://localhost:8080 --timeout 30
"""

import argparse
import json
import os
import requests
import sys
import time
from typing import Dict, List, Any, Tuple


class ImageTester:
    """Tests Docker image endpoints and image URLs."""

    def __init__(self, base_url: str, expected_base_url: str = None, assets_prefix: str = "assets", timeout: int = 10, verbose: bool = False):
        """Initialize tester with base configuration."""
        self.base_url = base_url.rstrip('/')
        self.expected_base_url = expected_base_url.rstrip('/') if expected_base_url else None
        self.assets_prefix = assets_prefix
        self.timeout = timeout
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ton-wallets-test/1.0'
        })

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[INFO] {message}")

    def fetch_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """
        Fetch a JSON file from the base URL.

        Args:
            filename: Name of the JSON file to fetch

        Returns:
            Parsed JSON data

        Raises:
            requests.RequestException: If request fails
            json.JSONDecodeError: If response is not valid JSON
        """
        url = f"{self.base_url}/{filename}"
        self.log(f"Fetching data from: {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch {url}: {e}")

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON response from {url}: {e.msg}", e.doc, e.pos)

        if not isinstance(data, list):
            raise ValueError(f"Expected list, got {type(data).__name__}")

        self.log(f"Successfully fetched {len(data)} wallet entries from {filename}")
        return data

    def fetch_wallets_json(self) -> List[Dict[str, Any]]:
        """
        Fetch wallets-v2.json from the base URL.

        Returns:
            Parsed JSON data from wallets-v2.json
        """
        return self.fetch_json_file("wallets-v2.json")

    def extract_image_urls(self, wallets: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """
        Extract all image URLs from wallet configurations and validate expected base URL.

        Args:
            wallets: List of wallet configuration dictionaries

        Returns:
            Tuple of (original_urls, test_urls) - test_urls have base URL replaced for actual testing
        """
        original_urls = []
        for wallet in wallets:
            if 'image' in wallet and isinstance(wallet['image'], str):
                original_urls.append(wallet['image'])

        unique_original_urls = list(set(original_urls))
        self.log(f"Extracted {len(unique_original_urls)} unique image URLs from {len(original_urls)} total entries")

        # Validate expected base URL if provided
        if self.expected_base_url:
            mismatched_urls = []
            for url in unique_original_urls:
                if not url.startswith(self.expected_base_url):
                    mismatched_urls.append(url)

            if mismatched_urls:
                self.log(f"WARNING: {len(mismatched_urls)} URLs do not match expected base URL {self.expected_base_url}")
                for url in mismatched_urls:
                    self.log(f"  - {url}")

        # Create test URLs by replacing expected base URL with test base URL + assets prefix
        test_urls = []
        test_base_with_prefix = f"{self.base_url}/{self.assets_prefix}"

        for url in unique_original_urls:
            if self.expected_base_url and url.startswith(self.expected_base_url):
                # Replace expected base URL with test base URL + assets prefix
                test_url = url.replace(self.expected_base_url, test_base_with_prefix, 1)
                test_urls.append(test_url)
            else:
                # If no expected base URL or URL doesn't match, use as-is
                test_urls.append(url)

        return unique_original_urls, test_urls

    def is_valid_png(self, content: bytes) -> bool:
        """
        Check if content is a valid PNG image.

        Args:
            content: Raw response content

        Returns:
            True if content is a valid PNG, False otherwise
        """
        # PNG files start with these 8 bytes: 89 50 4E 47 0D 0A 1A 0A
        png_signature = b'\x89PNG\r\n\x1a\n'
        return content.startswith(png_signature)

    def test_image_url(self, url: str) -> Tuple[bool, str]:
        """
        Test a single image URL.

        Args:
            url: Image URL to test

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        try:
            self.log(f"Testing image URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Debug headers if verbose
            if self.verbose:
                debug_headers = ['content-type', 'cache-control', 'content-length']
                for header in debug_headers:
                    value = response.headers.get(header, 'N/A')
                    self.log(f"  {header}: {value}")

            content_type = response.headers.get('content-type', '').lower()
            if 'image/png' not in content_type:
                return False, f"Invalid content-type: {content_type}"

            if not self.is_valid_png(response.content):
                return False, "Response content is not a valid PNG image"

            if len(response.content) == 0:
                return False, "Empty response content"

            self.log(f"✓ Valid PNG: {len(response.content)} bytes")
            return True, ""

        except requests.Timeout:
            return False, f"Request timeout after {self.timeout}s"
        except requests.RequestException as e:
            return False, f"Request failed: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def run_tests(self) -> Tuple[int, int, List[str]]:
        """
        Run all tests.

        Returns:
            Tuple of (passed_count, total_count, failed_urls)
        """
        print(f"Starting tests for: {self.base_url}")
        if self.expected_base_url:
            print(f"Expected base URL: {self.expected_base_url}")
        print("=" * 60)

        total_tests = 0
        passed_tests = 0
        failed_items = []

        # Test 1: Fetch wallets-v2.json
        wallets_v2 = None
        try:
            wallets_v2 = self.fetch_wallets_json()
            print(f"✓ Successfully fetched wallets-v2.json ({len(wallets_v2)} wallets)")
            passed_tests += 1
        except Exception as e:
            print(f"✗ Failed to fetch wallets-v2.json: {e}")
            failed_items.append(f"{self.base_url}/wallets-v2.json")
        total_tests += 1

        # Test 2: Fetch wallets.json
        try:
            wallets_v1 = self.fetch_json_file("wallets.json")
            print(f"✓ Successfully fetched wallets.json ({len(wallets_v1)} wallets)")
            passed_tests += 1
        except Exception as e:
            print(f"✗ Failed to fetch wallets.json: {e}")
            failed_items.append(f"{self.base_url}/wallets.json")
        total_tests += 1

        if wallets_v2 is None:
            return passed_tests, total_tests, failed_items

        # Test 3: Extract and validate image URLs from wallets-v2.json
        original_urls, test_urls = self.extract_image_urls(wallets_v2)
        if not test_urls:
            print("✗ No image URLs found in wallets-v2.json data")
            failed_items.append("No image URLs in wallets-v2.json")
            return passed_tests, total_tests + 1, failed_items

        print(f"✓ Found {len(test_urls)} image URLs to test from wallets-v2.json")

        # Show URL replacement info if applicable
        if self.expected_base_url:
            replaced_count = sum(1 for orig, test in zip(original_urls, test_urls) if orig != test)
            if replaced_count > 0:
                print(f"✓ Replacing {replaced_count} URLs: {self.expected_base_url} → {self.base_url}/{self.assets_prefix}")
        print()

        # Test 4: Test each image URL from wallets-v2.json
        for i, (original_url, test_url) in enumerate(zip(original_urls, test_urls), 1):
            if original_url != test_url:
                print(f"[{i}/{len(test_urls)}] Testing: {original_url} → {test_url}")
            else:
                print(f"[{i}/{len(test_urls)}] Testing: {test_url}")

            success, error = self.test_image_url(test_url)
            if success:
                print(f"  ✓ Valid PNG")
                passed_tests += 1
            else:
                print(f"  ✗ Failed: {error}")
                failed_items.append(original_url)  # Report original URL in failures

            total_tests += 1

            # Small delay to avoid overwhelming the server
            if i < len(test_urls):
                time.sleep(0.1)


        return passed_tests, total_tests, failed_items


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Test Docker image endpoints and image URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_image.py --base-url http://localhost:8080
  python test_image.py --base-url http://localhost:8080 --verbose
  python test_image.py --base-url http://localhost:8080 --timeout 30
        """.strip()
    )

    parser.add_argument(
        '--base-url',
        default=os.getenv('BASE_URL', 'http://localhost:8080'),
        help='Base URL of the running Docker container (default: http://localhost:8080 or BASE_URL env var)'
    )

    parser.add_argument(
        '--expected-base-url',
        default=os.getenv('EXPECTED_BASE_URL'),
        help='Expected base URL in wallets JSON (for validation and URL replacement, default: EXPECTED_BASE_URL env var)'
    )

    parser.add_argument(
        '--assets-prefix',
        default=os.getenv('ASSETS_PREFIX', 'assets'),
        help='Assets prefix for test URLs (default: assets or ASSETS_PREFIX env var)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=int(os.getenv('TIMEOUT', '10')),
        help='Request timeout in seconds (default: 10 or TIMEOUT env var)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=os.getenv('VERBOSE', 'false').lower() == 'true',
        help='Enable verbose output (default: false or VERBOSE env var)'
    )

    return parser


def main() -> None:
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Validate arguments
    if not args.base_url.strip():
        print("ERROR: Base URL cannot be empty", file=sys.stderr)
        sys.exit(1)

    try:
        tester = ImageTester(args.base_url, args.expected_base_url, args.assets_prefix, args.timeout, args.verbose)
        passed, total, failed_urls = tester.run_tests()

        print()
        print("=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {len(failed_urls)}")

        if failed_urls:
            print()
            print("Failed items:")
            for item in failed_urls:
                print(f"  - {item}")

        print()
        if len(failed_urls) == 0:
            print("🎉 ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print(f"❌ {len(failed_urls)} TESTS FAILED")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
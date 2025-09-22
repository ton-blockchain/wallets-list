#!/usr/bin/env python3
"""
Wallet Image URL Proxy Script

This script processes wallet configuration files to replace external image URLs
with proxy URLs pointing to local assets. It also generates an origins mapping
file that maps filenames to their original URLs. It's designed to work with Docker
containers and generates sanitized filenames for wallet images.

Usage:
    # Basic usage with default settings
    python scripts/proxy_urls.py

    # Specify custom base URL
    python scripts/proxy_urls.py --base-url "https://your-proxy.com/assets/"

    # Use environment variable
    BASE_URL="https://your-proxy.com/assets/" python scripts/proxy_urls.py

    # Custom input/output files
    python scripts/proxy_urls.py --input custom-wallets.json --output custom-proxy.json --origins custom-origins.json

    # Verbose output
    python scripts/proxy_urls.py --verbose

Command Line Options:
    --base-url URL     Base URL for proxy server (default: https://config.ton.org/assets/)
    --input FILE       Input JSON file (default: wallets-v2.json)
    --output FILE      Output JSON file (default: wallets-v2.proxy.json)
    --origins FILE     Where to save mappings to original URLs JSON file (default: origins.json)
    --verbose, -v      Enable verbose output
    --help             Show help message

Environment Variables:
    BASE_URL: Base URL for the proxy server (overridden by --base-url)

File Naming Convention:
    - Converts app names to lowercase
    - Replaces non-alphanumeric characters with underscores
    - Prevents double underscores
    - Removes leading/trailing underscores
    Examples: "telegram-wallet" → "telegram_wallet.png"
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any


class WalletProxyProcessor:
    """Processes wallet configurations to replace image URLs with proxy URLs."""

    def __init__(self, base_url: str):
        """Initialize processor with base URL."""
        self.base_url = base_url.rstrip('/')
        self.origins_mapping = {}
    
    @staticmethod
    def format_filename(app_name: str) -> str:
        """
        Format app name for use as filename.
        
        Args:
            app_name: Original app name from wallet data
            
        Returns:
            Sanitized filename without extension
        """
        # Convert to lowercase and replace non-alphanumeric with underscores
        formatted = re.sub(r'[^a-z0-9]', '_', app_name.lower())
        
        # Collapse multiple underscores and trim edges
        formatted = re.sub(r'_+', '_', formatted).strip('_')
        
        return formatted
    
    def process_wallet(self, wallet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single wallet entry to replace image URL.

        Args:
            wallet: Wallet configuration dictionary

        Returns:
            Updated wallet configuration
        """
        processed_wallet = wallet.copy()

        if 'app_name' in wallet and 'image' in wallet:
            filename = self.format_filename(wallet['app_name'])
            filename_with_ext = f"{filename}.png"
            processed_wallet['image'] = f"{self.base_url}/{filename_with_ext}"

            # Store the mapping of filename to original URL
            self.origins_mapping[filename_with_ext] = wallet['image']

        return processed_wallet
    
    def process_wallets(self, wallets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process all wallet entries.
        
        Args:
            wallets: List of wallet configurations
            
        Returns:
            List of processed wallet configurations
        """
        return [self.process_wallet(wallet) for wallet in wallets]


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load and parse JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e.msg}", e.doc, e.pos)


def save_json_file(data: Any, file_path: str) -> None:
    """
    Save data to JSON file.

    Args:
        data: Data to save
        file_path: Output file path
    """
    path = Path(file_path)

    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Replace wallet image URLs with proxy URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/proxy_urls.py
  python scripts/proxy_urls.py --base-url https://proxy.example.com/assets/
  BASE_URL=https://proxy.example.com/assets/ python scripts/proxy_urls.py
        """.strip()
    )
    
    parser.add_argument(
        '--base-url',
        default=os.getenv('BASE_URL', 'https://config.ton.org/assets/'),
        help='Base URL for proxy server (default: https://config.ton.org/assets/)'
    )
    
    parser.add_argument(
        '--input',
        default='wallets-v2.json',
        help='Input JSON file (default: wallets-v2.json)'
    )
    
    parser.add_argument(
        '--output',
        default='wallets-v2.proxy.json',
        help='Output JSON file (default: wallets-v2.proxy.json)'
    )

    parser.add_argument(
        '--origins',
        default='origins.json',
        help='Origins mapping JSON file (default: origins.json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
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
        # Load input data
        if args.verbose:
            print(f"Loading wallet data from: {args.input}")
        
        wallets = load_json_file(args.input)
        
        if args.verbose:
            print(f"Loaded {len(wallets)} wallets")
            print(f"Using base URL: {args.base_url}")
        
        # Process wallets
        processor = WalletProxyProcessor(args.base_url)
        processed_wallets = processor.process_wallets(wallets)
        
        # Save output
        if args.verbose:
            print(f"Saving processed data to: {args.output}")

        save_json_file(processed_wallets, args.output)

        # Save origins mapping
        if args.verbose:
            print(f"Saving origins mapping to: {args.origins}")

        save_json_file(processor.origins_mapping, args.origins)

        # Report results
        original_count = len([w for w in wallets if 'image' in w])
        processed_count = len([w for w in processed_wallets if 'image' in w])

        if args.verbose:
            print("SUCCESS: Proxy URLs file created")
            print(f"Original URLs: {original_count}")
            print(f"Processed URLs: {processed_count}")
            print(f"Origins mapping entries: {len(processor.origins_mapping)}")
        else:
            print(f"SUCCESS: Created {args.output} with {len(processed_wallets)} wallets")
            print(f"SUCCESS: Created {args.origins} with {len(processor.origins_mapping)} origins")
    
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
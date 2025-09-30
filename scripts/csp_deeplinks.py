#!/usr/bin/env python3
"""
Script to extract deepLink properties from wallets-v2.json and format them as CSP policies.
"""

import json
import sys
from pathlib import Path


def extract_deeplinks(json_file_path):
    """Extract deepLink properties from the wallets JSON file."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            wallets = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_file_path}: {e}")
        return []
    
    deeplinks = []
    for wallet in wallets:
        if 'deepLink' in wallet:
            deeplinks.append(wallet['deepLink'])
    
    return deeplinks


def format_as_csp_policy(deeplinks):
    """Format deepLinks as CSP frame-src policy."""
    if not deeplinks:
        return "frame-src http: https:;"
    
    # Remove duplicates and sort
    unique_deeplinks = sorted(set(deeplinks))
    
    # Extract scheme only (keep only the part before :// and add :)
    formatted_deeplinks = []
    for dl in unique_deeplinks:
        if '://' in dl:
            scheme = dl.split('://')[0] + ':'
            formatted_deeplinks.append(scheme)
        else:
            formatted_deeplinks.append(dl)
    
    # Format as CSP policy
    csp_policy = "frame-src http: https: " + " ".join(formatted_deeplinks) + ";"
    return csp_policy


def main():
    # Get the path to wallets-v2.json (assuming script is in scripts/ directory)
    script_dir = Path(__file__).parent
    json_file = script_dir.parent / "wallets-v2.json"
    
    print("Extracting deepLink properties from wallets-v2.json...")
    deeplinks = extract_deeplinks(json_file)
    
    if not deeplinks:
        print("No deepLink properties found in the wallets file.")
        return
    
    print(f"\nFound {len(deeplinks)} deepLink properties:")
    for deeplink in sorted(set(deeplinks)):
        print(f"  - {deeplink}")
    
    print(f"\nCSP Policy (frame-src):")
    csp_policy = format_as_csp_policy(deeplinks)
    print(csp_policy)


if __name__ == "__main__":
    main()

# Wallet Image Proxy Scripts

This directory contains scripts for managing wallet image URLs and creating proxy configurations.

## Files

- `proxy_urls.py` - Main script to replace image URLs with proxy URLs
- `../tests/test_proxy_urls.py` - Test suite for the proxy script

## Usage

### Basic Usage

```bash
# Use default settings (BASE_URL=https://config.ton.org/assets/)
python scripts/proxy_urls.py

# Specify custom base URL
python scripts/proxy_urls.py --base-url "https://your-proxy.com/assets/"

# Use environment variable
BASE_URL="https://your-proxy.com/assets/" python scripts/proxy_urls.py

# Custom input/output files
python scripts/proxy_urls.py --input custom-wallets.json --output custom-proxy.json

# Verbose output
python scripts/proxy_urls.py --verbose
```

### Command Line Options

- `--base-url URL` - Base URL for proxy server (default: https://config.ton.org/assets/)
- `--input FILE` - Input JSON file (default: wallets-v2.json)
- `--output FILE` - Output JSON file (default: wallets-v2.proxy.json)
- `--verbose, -v` - Enable verbose output
- `--help` - Show help message

### Environment Variables

- `BASE_URL` - Base URL for proxy server (overridden by --base-url)

## Docker Integration

This script is designed to work with Docker containers:

1. Create a Dockerfile that serves static assets from `/assets/` directory
2. Use this script to generate the proxy JSON file
3. Set the appropriate BASE_URL for their container

Example Docker workflow:
```bash
# Generate proxy URLs for config.ton.org
python scripts/proxy_urls.py --base-url "https://config.ton.org/assets/"

# The generated wallets-v2.proxy.json can be used by applications
# that need to reference the local asset files
```

## Testing

Run the test suite:

```bash
# Run all tests
python tests/test_proxy_urls.py
```

## Architecture

The script uses a clean object-oriented design:

- **`WalletProxyProcessor`** - Main processing class that handles URL replacement
- **`format_filename()`** - Method for sanitizing app names into valid filenames
- **`load_json_file()` / `save_json_file()`** - Utility functions for file operations
- **Clean separation** - Processing logic separated from CLI interface

## File Naming Convention

The filename formatting follows these rules:

- Converts to lowercase
- Replaces non-alphanumeric characters with underscores
- Prevents double underscores
- Removes leading/trailing underscores

Examples:
- `telegram-wallet` → `telegram_wallet.png`
- `Architec.ton` → `architec_ton.png`
- `tonkeeper-pro` → `tonkeeper_pro.png`

## Output Format

The script generates a JSON file identical to the input, except the `image` field is replaced with the proxy URL:

```json
{
  "app_name": "telegram-wallet",
  "name": "Wallet",
  "image": "https://config.ton.org/assets/telegram_wallet.png",
  "about_url": "https://wallet.tg/",
  ...
}
```

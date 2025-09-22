#!/usr/bin/env python3
"""Generate nginx.conf from Jinja2 template using origins mapping data."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

try:
    from jinja2 import Environment, FileSystemLoader, Template
except ImportError:
    print("ERROR: jinja2 is required. Install with: pip install jinja2", file=sys.stderr)
    sys.exit(1)


def load_origins_file(file_path: str) -> Dict[str, str]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Origins file not found: {file_path}")

    try:
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Origins file must contain a JSON object")

        return data
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e.msg}", e.doc, e.pos)


def load_template(template_path: str) -> Template:
    path = Path(template_path)

    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    env = Environment(
        loader=FileSystemLoader(path.parent),
        trim_blocks=True,
        lstrip_blocks=True
    )

    return env.get_template(path.name)


def generate_nginx_config(origins: Dict[str, str], template: Template, assets_prefix: str = None, server_name: str = None, cache_duration_ok: str = None, cache_duration_notok: str = None) -> str:
    template_vars: Dict[str, Any] = {'origins': origins}
    if assets_prefix is not None:
        template_vars['assets_prefix'] = assets_prefix
    if server_name is not None:
        template_vars['server_name'] = server_name
    if cache_duration_ok is not None:
        template_vars['cache_duration_ok'] = cache_duration_ok
    if cache_duration_notok is not None:
        template_vars['cache_duration_notok'] = cache_duration_notok
    return template.render(**template_vars)


def save_config(config_content: str, output_path: str) -> None:
    path = Path(output_path)

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open('w', encoding='utf-8') as f:
        f.write(config_content)


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate nginx.conf from Jinja2 template using origins mapping",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_nginx_conf.py
  python scripts/generate_nginx_conf.py --template server/nginx.conf.j2 --output server/nginx.conf --origins custom-origins.json
  python scripts/generate_nginx_conf.py --assets-prefix images --server-name example.com
  python scripts/generate_nginx_conf.py --cache-duration-ok 1h --cache-duration-notok 5m
  python scripts/generate_nginx_conf.py --verbose
        """.strip()
    )

    parser.add_argument(
        '--origins',
        default='origins.json',
        help='Origins mapping JSON file (default: origins.json)'
    )

    parser.add_argument(
        '--template',
        default='server/nginx.conf.j2',
        help='Jinja2 template file (default: server/nginx.conf.j2)'
    )

    parser.add_argument(
        '--output',
        default='server/nginx.conf',
        help='Output nginx config file (default: server/nginx.conf)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--assets-prefix',
        help='Assets prefix for nginx locations (default: assets)'
    )

    parser.add_argument(
        '--server-name',
        help='Server name for nginx config (default: config.ton.org)'
    )

    parser.add_argument(
        '--cache-duration-ok',
        help='Cache duration for successful responses (default: 10m)'
    )

    parser.add_argument(
        '--cache-duration-notok',
        help='Cache duration for failed responses (default: 2m)'
    )

    return parser


def main() -> None:
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        if args.verbose:
            print(f"Loading origins data from: {args.origins}")

        origins = load_origins_file(args.origins)

        if args.verbose:
            print(f"Loaded {len(origins)} origin mappings")

        if args.verbose:
            print(f"Loading template from: {args.template}")

        template = load_template(args.template)

        if args.verbose:
            print("Generating nginx configuration...")

        config_content = generate_nginx_config(origins, template, args.assets_prefix, args.server_name, args.cache_duration_ok, args.cache_duration_notok)

        if args.verbose:
            print(f"Saving configuration to: {args.output}")

        save_config(config_content, args.output)

        if args.verbose:
            print("SUCCESS: Nginx configuration generated")
            print(f"Generated {len(origins)} map entries")
        else:
            print(f"SUCCESS: Generated {args.output} with {len(origins)} map entries")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
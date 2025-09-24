import argparse
import json
import sys
from pathlib import Path

import jsonschema
from jsonschema import Draft7Validator


class JsonSchemaNamespace(argparse.Namespace):
    wallets_file: Path
    json_schema_file: Path


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Checking a json file using json-schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_jsonschema.py --wallets-file=wallets-v2.json --json-schema-file=wallets-v2.schema.json
    """.strip(),
    )

    parser.add_argument(
        "--wallets-file",
        type=Path,
        required=True,
        help="Path to the 'wallets-v2.json' file",
    )

    parser.add_argument(
        "--json-schema-file",
        type=Path,
        required=True,
        help="Path to the 'wallets-v2.json' schema file",
    )

    return parser


def main() -> None:
    parser = create_argument_parser()
    args = parser.parse_args(namespace=JsonSchemaNamespace())

    wallets = json.loads(args.wallets_file.read_bytes())
    json_schema = json.loads(args.json_schema_file.read_bytes())

    error_message: str | None = None
    try:
        jsonschema.validate(instance=wallets, schema=json_schema, cls=Draft7Validator)
    except jsonschema.exceptions.ValidationError as e:
        error_message = str(e)

    if error_message is None:
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("TESTS FAILED:\n")
        print(error_message)
        sys.exit(1)


if __name__ == "__main__":
    main()

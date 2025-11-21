# main.py

import argparse

from file_utils import load_dhis_env_config
from create_missing_values_use_case import CreateMissingValuesUseCase
from dhis_utils import test_connection

# Default configuration (can be overridden by .env and CLI)
DEFAULT_BASE_URL = ""
DEFAULT_JSESSIONID = ""

DEFAULT_INPUT_FILE = ("teis_without_storedby.csv")    # read from input/
DEFAULT_OUTPUT_FILE = "insert_attr_fullname.sql"    # write to output/


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create missing attribute values SQL for DHIS2 tracked entities."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="DHIS2 base URL (default from code or .env).",
    )
    parser.add_argument(
        "--jsessionid",
        default=DEFAULT_JSESSIONID,
        help="JSESSIONID cookie value (default from code or .env).",
    )
    parser.add_argument(
        "--input-file",
        default=DEFAULT_INPUT_FILE,
        help="Input CSV file name (relative to 'input/' folder).",
    )
    parser.add_argument(
        "--output-file",
        default=DEFAULT_OUTPUT_FILE,
        help="Output SQL file name (relative to 'output/' folder).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Merge CLI defaults with .env (with confirmation)
    base_url, jsessionid = load_dhis_env_config(
        default_base_url=args.base_url,
        default_jsessionid=args.jsessionid,
    )

    test_connection(base_url=base_url, jsessionid=jsessionid)

    use_case = CreateMissingValuesUseCase(
        base_url=base_url,
        jsessionid=jsessionid,
        input_path=args.input_file,
        output_path=args.output_file,
    )

    use_case.execute()


if __name__ == "__main__":
    main()